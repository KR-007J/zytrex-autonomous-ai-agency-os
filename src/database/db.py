"""Database session and repository management for LeadGen system."""

from __future__ import annotations
import os
import json
import hashlib
from pathlib import Path
from typing import Generator, Optional, List, Dict, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, select, update, delete, desc, func, or_
from sqlalchemy.orm import sessionmaker, Session

from src.database.models import Base, Lead, ScrapeJob, OutreachDraft, ContactedMemory
from src.config import load_config

_engine = None
_SessionFactory = None


def get_engine(database_url: Optional[str] = None):
    global _engine
    if _engine is None:
        if not database_url:
            config = load_config()
            database_url = config.app.database_url

        # Ensure SQLite directory exists
        if database_url.startswith("sqlite:///"):
            db_path = database_url.replace("sqlite:///", "")
            if db_path != ":memory:":
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        _engine = create_engine(database_url, connect_args=connect_args, echo=False, pool_pre_ping=True)
    return _engine


def get_session_factory(database_url: Optional[str] = None) -> sessionmaker[Session]:
    global _SessionFactory
    if _SessionFactory is None:
        engine = get_engine(database_url)
        _SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionFactory


def init_db(database_url: Optional[str] = None) -> None:
    """Initialize database schema."""
    engine = get_engine(database_url)
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for transactional DB operations."""
    factory = get_session_factory()
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency for database session."""
    factory = get_session_factory()
    session: Session = factory()
    try:
        yield session
    finally:
        session.close()


# ==============================================================================
# Lead Repository Operations
# ==============================================================================

class LeadRepository:
    @staticmethod
    def get_leads(
        session: Session,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        industry: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[List[Lead], int]:
        """Fetch filtered and paginated leads with total count."""
        query = session.query(Lead)

        if status:
            query = query.filter(Lead.status == status)
        if industry:
            query = query.filter(Lead.industry_tag.ilike(f"%{industry}%"))
        if search:
            search_filter = or_(
                Lead.company_name.ilike(f"%{search}%"),
                Lead.contact_name.ilike(f"%{search}%"),
                Lead.email.ilike(f"%{search}%"),
                Lead.source_url.ilike(f"%{search}%"),
            )
            query = query.filter(search_filter)

        total = query.count()
        leads = query.order_by(desc(Lead.lead_score), desc(Lead.created_at)).offset(skip).limit(limit).all()
        return leads, total

    @staticmethod
    def get_by_id(session: Session, lead_id: int) -> Optional[Lead]:
        return session.query(Lead).filter(Lead.id == lead_id).first()

    @staticmethod
    def find_existing(
        session: Session,
        company_name: str,
        email: Optional[str] = None,
        source_domain: Optional[str] = None,
    ) -> Optional[Lead]:
        """Find if a lead already exists by email, domain, or exact company name."""
        if email:
            lead = session.query(Lead).filter(Lead.email == email.strip().lower()).first()
            if lead:
                return lead

        if source_domain and source_domain.strip():
            lead = session.query(Lead).filter(Lead.source_domain == source_domain.strip().lower()).first()
            if lead:
                return lead

        if company_name and company_name.strip():
            lead = session.query(Lead).filter(Lead.company_name.ilike(company_name.strip())).first()
            if lead:
                return lead

        return None

    @staticmethod
    def create_or_update(session: Session, lead_data: Dict[str, Any]) -> tuple[Lead, bool]:
        """Create lead if not exists, or update if exists. Returns (lead, is_new)."""
        existing = LeadRepository.find_existing(
            session=session,
            company_name=lead_data.get("company_name", ""),
            email=lead_data.get("email"),
            source_domain=lead_data.get("source_domain"),
        )

        if existing:
            # Update fields if new data is richer
            if not existing.email and lead_data.get("email"):
                existing.email = lead_data["email"]
            if not existing.phone and lead_data.get("phone"):
                existing.phone = lead_data["phone"]
            if not existing.contact_name and lead_data.get("contact_name"):
                existing.contact_name = lead_data["contact_name"]
            if not existing.linkedin_url and lead_data.get("linkedin_url"):
                existing.linkedin_url = lead_data["linkedin_url"]
            if lead_data.get("lead_score", 0) > existing.lead_score:
                existing.lead_score = lead_data["lead_score"]

            session.flush()
            return existing, False

        # Create new lead
        new_lead = Lead(
            company_name=lead_data.get("company_name", "Unknown Company"),
            contact_name=lead_data.get("contact_name"),
            email=lead_data.get("email"),
            phone=lead_data.get("phone"),
            source_url=lead_data.get("source_url"),
            source_domain=lead_data.get("source_domain"),
            industry_tag=lead_data.get("industry_tag"),
            location=lead_data.get("location"),
            linkedin_url=lead_data.get("linkedin_url"),
            lead_score=lead_data.get("lead_score", 0),
            status=lead_data.get("status", "new"),
            raw_snippet=lead_data.get("raw_snippet"),
            custom_metadata=lead_data.get("custom_metadata"),
        )
        session.add(new_lead)
        session.flush()
        return new_lead, True

    @staticmethod
    def get_stats(session: Session) -> Dict[str, Any]:
        """Calculate high-level dashboard metrics."""
        total_leads = session.query(func.count(Lead.id)).scalar() or 0
        leads_with_email = session.query(func.count(Lead.id)).filter(Lead.email.isnot(None), Lead.email != "").scalar() or 0
        leads_with_phone = session.query(func.count(Lead.id)).filter(Lead.phone.isnot(None), Lead.phone != "").scalar() or 0
        leads_contacted = session.query(func.count(Lead.id)).filter(Lead.status == "contacted").scalar() or 0
        pending_drafts = session.query(func.count(OutreachDraft.id)).filter(OutreachDraft.status == "pending_review").scalar() or 0

        # Status counts
        status_counts = dict(
            session.query(Lead.status, func.count(Lead.id)).group_by(Lead.status).all()
        )

        return {
            "total_leads": total_leads,
            "leads_with_email": leads_with_email,
            "leads_with_phone": leads_with_phone,
            "leads_contacted": leads_contacted,
            "pending_drafts": pending_drafts,
            "status_breakdown": status_counts,
        }


# ==============================================================================
# Global Enterprise Lead Repository
# ==============================================================================

class GlobalLeadRepository:
    @staticmethod
    def get_leads(
        session: Session,
        skip: int = 0,
        limit: int = 25,
        category: Optional[str] = None,
        region: Optional[str] = None,
        country_code: Optional[str] = None,
        platform_cms: Optional[str] = None,
        search: Optional[str] = None,
        min_score: int = 0,
        exclude_suppressed: bool = True,
    ) -> tuple[List[Any], int]:
        from src.database.models import GlobalEnterpriseLead, SuppressionRecord
        query = session.query(GlobalEnterpriseLead)

        if exclude_suppressed:
            query = query.filter(GlobalEnterpriseLead.compliance_status != "SUPPRESSED")

        if category and category.strip():
            query = query.filter(GlobalEnterpriseLead.category.ilike(f"%{category.strip()}%"))

        if region and region.strip():
            query = query.filter(GlobalEnterpriseLead.region.ilike(f"%{region.strip()}%"))

        if country_code and country_code.strip():
            query = query.filter(GlobalEnterpriseLead.country_code == country_code.strip().upper())

        if platform_cms and platform_cms.strip():
            query = query.filter(GlobalEnterpriseLead.platform_cms.ilike(f"%{platform_cms.strip()}%"))

        if min_score > 0:
            query = query.filter(GlobalEnterpriseLead.confidence_score >= min_score)

        if search and search.strip():
            s = search.strip()
            query = query.filter(
                or_(
                    GlobalEnterpriseLead.company_name.ilike(f"%{s}%"),
                    GlobalEnterpriseLead.source_domain.ilike(f"%{s}%"),
                    GlobalEnterpriseLead.contact_email.ilike(f"%{s}%"),
                    GlobalEnterpriseLead.contact_phone.ilike(f"%{s}%"),
                    GlobalEnterpriseLead.category.ilike(f"%{s}%"),
                    GlobalEnterpriseLead.region.ilike(f"%{s}%"),
                    GlobalEnterpriseLead.platform_cms.ilike(f"%{s}%"),
                    GlobalEnterpriseLead.tech_stack.ilike(f"%{s}%"),
                )
            )

        total = query.count()
        leads = query.order_by(desc(GlobalEnterpriseLead.confidence_score), desc(GlobalEnterpriseLead.created_at)).offset(skip).limit(limit).all()
        return leads, total

    @staticmethod
    def get_platforms_breakdown(session: Session) -> List[Dict[str, Any]]:
        from src.database.models import GlobalEnterpriseLead
        results = (
            session.query(
                GlobalEnterpriseLead.platform_cms,
                func.count(GlobalEnterpriseLead.id).label("count"),
            )
            .group_by(GlobalEnterpriseLead.platform_cms)
            .order_by(desc("count"))
            .all()
        )
        return [{"platform": p, "count": cnt} for p, cnt in results if p]

    @staticmethod
    def get_categories_breakdown(session: Session) -> List[Dict[str, Any]]:
        from src.database.models import GlobalEnterpriseLead
        results = (
            session.query(
                GlobalEnterpriseLead.category,
                func.count(GlobalEnterpriseLead.id).label("count"),
            )
            .group_by(GlobalEnterpriseLead.category)
            .order_by(desc("count"))
            .all()
        )
        return [{"category": cat, "count": cnt} for cat, cnt in results if cat]

    @staticmethod
    def get_regions_breakdown(session: Session) -> List[Dict[str, Any]]:
        from src.database.models import GlobalEnterpriseLead
        results = (
            session.query(
                GlobalEnterpriseLead.region,
                GlobalEnterpriseLead.country_code,
                func.count(GlobalEnterpriseLead.id).label("count"),
            )
            .group_by(GlobalEnterpriseLead.region, GlobalEnterpriseLead.country_code)
            .order_by(desc("count"))
            .all()
        )
        return [{"region": reg, "country_code": cc, "count": cnt} for reg, cc, cnt in results if reg]

    @staticmethod
    def upsert_lead(session: Session, data: Dict[str, Any]) -> tuple[Any, bool]:
        from src.database.models import GlobalEnterpriseLead, SuppressionRecord

        domain = data.get("source_domain", "").strip().lower()
        if not domain:
            domain = data.get("live_url", "").replace("https://", "").replace("http://", "").split("/")[0].strip().lower()

        domain_hash = hashlib.sha256(domain.encode("utf-8")).hexdigest()

        # Check suppression
        email = (data.get("contact_email") or "").strip().lower()
        is_suppressed = session.query(SuppressionRecord).filter(
            or_(
                SuppressionRecord.domain_or_email == domain,
                SuppressionRecord.domain_or_email == email,
            )
        ).first() is not None

        compliance_status = "SUPPRESSED" if is_suppressed else data.get("compliance_status", "VERIFIED_PUBLIC")

        existing = session.query(GlobalEnterpriseLead).filter(GlobalEnterpriseLead.domain_hash == domain_hash).first()
        if existing:
            if data.get("contact_email") and not existing.contact_email:
                existing.contact_email = data["contact_email"]
            if data.get("contact_phone") and not existing.contact_phone:
                existing.contact_phone = data["contact_phone"]
            if data.get("platform_cms") and (not existing.platform_cms or existing.platform_cms == "Custom"):
                existing.platform_cms = data["platform_cms"]
            if data.get("tech_stack"):
                existing.tech_stack = json.dumps(data["tech_stack"]) if isinstance(data["tech_stack"], list) else str(data["tech_stack"])
            if compliance_status == "SUPPRESSED":
                existing.compliance_status = "SUPPRESSED"
            session.flush()
            return existing, False

        tech_json = json.dumps(data.get("tech_stack", [])) if isinstance(data.get("tech_stack"), list) else data.get("tech_stack")

        new_lead = GlobalEnterpriseLead(
            domain_hash=domain_hash,
            company_name=data.get("company_name", domain.capitalize()),
            category=data.get("category", "General Business"),
            region=data.get("region", "Global"),
            country_code=data.get("country_code", "GLOBAL"),
            live_url=data.get("live_url", f"https://{domain}"),
            source_domain=domain,
            contact_email=email or None,
            contact_phone=data.get("contact_phone"),
            platform_cms=data.get("platform_cms", "Custom"),
            tech_stack=tech_json,
            source=data.get("source", "Crawlee Ingestion"),
            confidence_score=data.get("confidence_score", 95),
            compliance_status=compliance_status,
            raw_metadata=data.get("raw_metadata"),
        )
        session.add(new_lead)
        session.flush()
        return new_lead, True


# ==============================================================================
# Suppression & Compliance Repository
# ==============================================================================

class SuppressionRepository:
    @staticmethod
    def is_suppressed(session: Session, domain_or_email: str) -> bool:
        from src.database.models import SuppressionRecord
        clean = domain_or_email.strip().lower()
        return session.query(SuppressionRecord).filter(SuppressionRecord.domain_or_email == clean).first() is not None

    @staticmethod
    def add_suppression(session: Session, domain_or_email: str, reason: str = "Opt-Out", scope: str = "GLOBAL", notes: str = "") -> Any:
        from src.database.models import SuppressionRecord, GlobalEnterpriseLead
        clean = domain_or_email.strip().lower()
        rec = session.query(SuppressionRecord).filter(SuppressionRecord.domain_or_email == clean).first()
        if not rec:
            rec = SuppressionRecord(
                domain_or_email=clean,
                reason=reason,
                scope=scope,
                notes=notes,
            )
            session.add(rec)

        # Mark any existing matching global leads as SUPPRESSED
        session.query(GlobalEnterpriseLead).filter(
            or_(
                GlobalEnterpriseLead.source_domain == clean,
                GlobalEnterpriseLead.contact_email == clean,
            )
        ).update({"compliance_status": "SUPPRESSED"}, synchronize_session=False)

        session.flush()
        return rec

    @staticmethod
    def remove_suppression(session: Session, domain_or_email: str) -> bool:
        from src.database.models import SuppressionRecord, GlobalEnterpriseLead
        clean = domain_or_email.strip().lower()
        rec = session.query(SuppressionRecord).filter(SuppressionRecord.domain_or_email == clean).first()
        if rec:
            session.delete(rec)
            # Restore status to VERIFIED_PUBLIC
            session.query(GlobalEnterpriseLead).filter(
                or_(
                    GlobalEnterpriseLead.source_domain == clean,
                    GlobalEnterpriseLead.contact_email == clean,
                )
            ).update({"compliance_status": "VERIFIED_PUBLIC"}, synchronize_session=False)
            session.flush()
            return True
        return False

    @staticmethod
    def get_all(session: Session, skip: int = 0, limit: int = 100) -> tuple[List[Any], int]:
        from src.database.models import SuppressionRecord
        q = session.query(SuppressionRecord).order_by(desc(SuppressionRecord.added_at))
        total = q.count()
        return q.offset(skip).limit(limit).all(), total


# ==============================================================================
# Ingestion Job Repository
# ==============================================================================

class IngestionJobRepository:
    @staticmethod
    def create_job(session: Session, pipeline_type: str, category: str, region: str) -> Any:
        from src.database.models import IngestionPipelineJob
        job = IngestionPipelineJob(
            pipeline_type=pipeline_type,
            category_filter=category,
            region_filter=region,
            status="RUNNING",
        )
        session.add(job)
        session.flush()
        return job

    @staticmethod
    def update_job(session: Session, job_id: int, status: str, seeds: int = 0, pages: int = 0, leads: int = 0, error: str = None) -> Optional[Any]:
        from src.database.models import IngestionPipelineJob
        from datetime import datetime, timezone
        job = session.query(IngestionPipelineJob).filter(IngestionPipelineJob.id == job_id).first()
        if job:
            job.status = status
            job.seeds_discovered = seeds
            job.pages_crawled = pages
            job.leads_extracted = leads
            job.error_log = error
            if status in ["COMPLETED", "FAILED"]:
                job.finished_at = datetime.now(timezone.utc)
            session.flush()
        return job

    @staticmethod
    def get_recent(session: Session, limit: int = 20) -> List[Any]:
        from src.database.models import IngestionPipelineJob
        return session.query(IngestionPipelineJob).order_by(desc(IngestionPipelineJob.started_at)).limit(limit).all()

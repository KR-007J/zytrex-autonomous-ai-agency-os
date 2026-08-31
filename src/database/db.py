"""Database session and repository management for LeadGen system."""

from __future__ import annotations
import os
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

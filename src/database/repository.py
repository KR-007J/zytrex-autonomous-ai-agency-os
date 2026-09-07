"""Data access repository for Leads and Intelligence objects."""

from __future__ import annotations
from datetime import datetime, timezone
import json
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import func, or_, desc
from sqlalchemy.orm import Session
from src.database.models import Lead, LeadEvent, DiscoveryJob, ApiKey, AuditLog


class LeadRepository:

    @classmethod
    def get_lead_by_domain(cls, session: Session, domain: str) -> Optional[Lead]:
        return session.query(Lead).filter(Lead.domain == domain.lower().strip()).first()

    @classmethod
    def get_lead_by_id(cls, session: Session, lead_id: int) -> Optional[Lead]:
        return session.query(Lead).filter(Lead.id == lead_id).first()

    @classmethod
    def upsert_lead(
        cls,
        session: Session,
        domain: str,
        canonical_url: str,
        business_name: Optional[str] = None,
        description: Optional[str] = None,
        country: Optional[str] = None,
        region: Optional[str] = None,
        industry: Optional[str] = None,
        status: str = "LIVE",
        http_status: Optional[int] = 200,
        has_ssl: bool = True,
        response_time_ms: float = 0.0,
        primary_technology: Optional[str] = None,
        technology_category: Optional[str] = None,
        technology_confidence: float = 0.0,
        evidence: Optional[List[str]] = None,
        technologies: Optional[List[Dict[str, Any]]] = None,
        emails: Optional[List[Dict[str, Any]]] = None,
        phones: Optional[List[Dict[str, Any]]] = None,
        socials: Optional[Dict[str, str]] = None,
        lead_score: int = 0,
        score_label: str = "LOW",
        score_reasons: Optional[List[str]] = None,
        source: str = "LIVE_CRAWL",
        is_demo: bool = False,
    ) -> Tuple[Lead, bool]:
        domain_clean = domain.lower().strip()
        now = datetime.now(timezone.utc)
        lead = cls.get_lead_by_domain(session, domain_clean)
        is_created = False

        evidence = evidence or []
        technologies = technologies or []
        emails = emails or []
        phones = phones or []
        socials = socials or {}
        score_reasons = score_reasons or []

        primary_email = emails[0]["value"] if emails else None
        primary_phone = phones[0]["value"] if phones else None

        if not lead:
            lead = Lead(
                domain=domain_clean,
                canonical_url=canonical_url,
                business_name=business_name or domain_clean,
                description=description,
                country=country,
                region=region,
                industry=industry,
                status=status,
                http_status=http_status,
                has_ssl=has_ssl,
                response_time_ms=response_time_ms,
                primary_technology=primary_technology,
                technology_category=technology_category,
                technology_confidence=technology_confidence,
                evidence_json=json.dumps(evidence),
                technologies_json=json.dumps(technologies),
                emails_json=json.dumps(emails),
                primary_email=primary_email,
                phones_json=json.dumps(phones),
                primary_phone=primary_phone,
                socials_json=json.dumps(socials),
                lead_score=lead_score,
                score_label=score_label,
                score_reasons_json=json.dumps(score_reasons),
                source=source,
                is_demo=is_demo,
                discovered_at=now,
                last_verified_at=now,
                last_changed_at=now,
            )
            session.add(lead)
            session.flush()
            is_created = True

            event = LeadEvent(
                lead_id=lead.id,
                event_type="LEAD_CREATED",
                description=f"Discovered via {source} with technology {primary_technology or 'Unknown'}",
            )
            session.add(event)
        else:
            # Check technology change detection
            if primary_technology and lead.primary_technology and lead.primary_technology != primary_technology:
                event = LeadEvent(
                    lead_id=lead.id,
                    event_type="TECHNOLOGY_CHANGED",
                    description=f"Migrated from {lead.primary_technology} to {primary_technology}",
                )
                session.add(event)
                lead.last_changed_at = now

            lead.canonical_url = canonical_url
            if business_name:
                lead.business_name = business_name
            if description:
                lead.description = description
            if country:
                lead.country = country
            if region:
                lead.region = region
            if industry:
                lead.industry = industry
            lead.status = status
            lead.http_status = http_status
            lead.has_ssl = has_ssl
            lead.response_time_ms = response_time_ms

            if primary_technology:
                lead.primary_technology = primary_technology
            if technology_category:
                lead.technology_category = technology_category
            lead.technology_confidence = technology_confidence

            lead.evidence_json = json.dumps(evidence)
            lead.technologies_json = json.dumps(technologies)
            if emails:
                lead.emails_json = json.dumps(emails)
                lead.primary_email = primary_email
            if phones:
                lead.phones_json = json.dumps(phones)
                lead.primary_phone = primary_phone
            if socials:
                lead.socials_json = json.dumps(socials)

            lead.lead_score = lead_score
            lead.score_label = score_label
            lead.score_reasons_json = json.dumps(score_reasons)
            lead.last_verified_at = now

        return lead, is_created

    @classmethod
    def query_leads(
        cls,
        session: Session,
        technology: Optional[str] = None,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        status: Optional[str] = None,
        has_email: Optional[bool] = None,
        min_score: Optional[int] = None,
        query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "score",
    ) -> Tuple[List[Lead], int]:
        q = session.query(Lead)

        if technology:
            q = q.filter(Lead.primary_technology.ilike(f"%{technology}%"))
        if country:
            q = q.filter(Lead.country.ilike(f"%{country}%"))
        if industry:
            q = q.filter(Lead.industry.ilike(f"%{industry}%"))
        if status:
            q = q.filter(Lead.status == status)
        if has_email is True:
            q = q.filter(Lead.primary_email.isnot(None))
        if min_score is not None:
            q = q.filter(Lead.lead_score >= min_score)
        if query:
            pat = f"%{query}%"
            q = q.filter(or_(
                Lead.domain.ilike(pat),
                Lead.business_name.ilike(pat),
                Lead.primary_email.ilike(pat),
                Lead.primary_technology.ilike(pat)
            ))

        total = q.count()

        if sort_by == "score":
            q = q.order_by(desc(Lead.lead_score))
        elif sort_by == "recent":
            q = q.order_by(desc(Lead.last_verified_at))
        elif sort_by == "domain":
            q = q.order_by(Lead.domain)
        else:
            q = q.order_by(desc(Lead.id))

        items = q.offset(offset).limit(limit).all()
        return items, total

    @classmethod
    def get_stats(cls, session: Session) -> Dict[str, Any]:
        total_leads = session.query(Lead).count()
        live_leads = session.query(Lead).filter(Lead.status == "LIVE").count()
        hot_leads = session.query(Lead).filter(Lead.lead_score >= 85).count()
        with_email = session.query(Lead).filter(Lead.primary_email.isnot(None)).count()

        # Tech breakdown
        tech_counts = (
            session.query(Lead.primary_technology, func.count(Lead.id))
            .filter(Lead.primary_technology.isnot(None))
            .group_by(Lead.primary_technology)
            .order_by(desc(func.count(Lead.id)))
            .limit(10)
            .all()
        )

        return {
            "total_leads": total_leads,
            "live_leads": live_leads,
            "hot_leads": hot_leads,
            "with_email": with_email,
            "technologies": [{"name": t[0], "count": t[1]} for t in tech_counts if t[0]],
        }

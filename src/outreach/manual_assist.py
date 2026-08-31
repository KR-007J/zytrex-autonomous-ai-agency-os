"""Manual-assist outreach queue manager and LinkedIn action generator."""

from __future__ import annotations
import urllib.parse
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.config import RootConfig, load_config
from src.database.models import Lead, OutreachDraft, ContactedMemory
from src.outreach.personalizer import OutreachPersonalizer
from src.scraper.dedupe import is_already_contacted, record_contacted


class ManualAssistQueueManager:
    def __init__(self, config: Optional[RootConfig] = None):
        self.config = config or load_config()
        self.personalizer = OutreachPersonalizer(self.config)

    @staticmethod
    def generate_linkedin_search_url(company_name: str, contact_name: Optional[str] = None) -> str:
        """Generate targeted LinkedIn search deep link."""
        query_terms = [company_name]
        if contact_name and contact_name.strip():
            query_terms.append(contact_name.strip())
        else:
            query_terms.append("founder OR CEO OR 'growth' OR 'marketing'")

        query_str = " ".join(query_terms)
        encoded = urllib.parse.quote_plus(query_str)
        return f"https://www.linkedin.com/search/results/people/?keywords={encoded}&origin=GLOBAL_SEARCH_HEADER"

    def populate_outreach_queue(self, session: Session, limit: int = 50) -> int:
        """Generate personalized drafts for top uncontacted leads."""
        # Find leads with status 'new' or 'enriched'
        candidates = (
            session.query(Lead)
            .filter(Lead.status.in_(["new", "enriched"]))
            .order_by(desc(Lead.lead_score), desc(Lead.created_at))
            .limit(limit)
            .all()
        )

        drafts_created = 0
        for lead in candidates:
            # Check if already contacted
            if is_already_contacted(
                session=session,
                email=lead.email,
                domain=lead.source_domain,
                linkedin_url=lead.linkedin_url,
            ):
                lead.status = "contacted"
                continue

            # Check if active draft already exists
            existing_draft = (
                session.query(OutreachDraft)
                .filter(OutreachDraft.lead_id == lead.id)
                .filter(OutreachDraft.status.in_(["pending_review", "approved"]))
                .first()
            )
            if existing_draft:
                continue

            # Generate draft
            draft_content = self.personalizer.generate_draft_for_lead(lead)
            draft = OutreachDraft(
                lead_id=lead.id,
                template_id=draft_content["template_id"],
                subject=draft_content["subject"],
                personalized_message=draft_content["personalized_message"],
                status="pending_review",
            )
            lead.status = "drafted"
            session.add(draft)
            drafts_created += 1

        session.commit()
        return drafts_created

    def get_queue(
        self,
        session: Session,
        status: str = "pending_review",
        skip: int = 0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieve outreach queue with rich LinkedIn action metadata."""
        drafts = (
            session.query(OutreachDraft)
            .filter(OutreachDraft.status == status)
            .order_by(desc(OutreachDraft.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

        results = []
        for draft in drafts:
            lead = draft.lead
            linkedin_url = lead.linkedin_url
            search_url = self.generate_linkedin_search_url(
                company_name=lead.company_name,
                contact_name=lead.contact_name,
            )

            results.append({
                "draft_id": draft.id,
                "lead_id": lead.id,
                "company_name": lead.company_name,
                "contact_name": lead.contact_name or "Not Specified",
                "email": lead.email,
                "phone": lead.phone,
                "industry_tag": lead.industry_tag,
                "lead_score": lead.lead_score,
                "template_id": draft.template_id,
                "subject": draft.subject,
                "personalized_message": draft.personalized_message,
                "status": draft.status,
                "linkedin_profile_url": linkedin_url,
                "linkedin_search_url": search_url,
                "best_action_url": linkedin_url if linkedin_url else search_url,
                "created_at": draft.created_at.isoformat() if draft.created_at else None,
            })

        return results

    def approve_draft(self, session: Session, draft_id: int) -> bool:
        """Mark draft as approved for sending."""
        draft = session.query(OutreachDraft).filter(OutreachDraft.id == draft_id).first()
        if not draft:
            return False
        draft.status = "approved"
        session.commit()
        return True

    def mark_draft_sent(
        self,
        session: Session,
        draft_id: int,
        channel: str = "linkedin_manual",
        notes: Optional[str] = None,
    ) -> bool:
        """Mark draft as sent, update lead status, and record persistent contacted memory."""
        draft = session.query(OutreachDraft).filter(OutreachDraft.id == draft_id).first()
        if not draft:
            return False

        draft.status = "sent"
        draft.sent_at = datetime.now(timezone.utc)
        draft.notes = notes

        lead = draft.lead
        if lead:
            lead.status = "contacted"
            # Record identifiers in contacted memory
            if lead.email:
                record_contacted(session, lead.email, lead_id=lead.id, channel=channel, notes=notes)
            if lead.source_domain:
                record_contacted(session, lead.source_domain, lead_id=lead.id, channel=channel, notes=notes)
            if lead.linkedin_url:
                record_contacted(session, lead.linkedin_url, lead_id=lead.id, channel=channel, notes=notes)

        session.commit()
        return True

    def reject_draft(self, session: Session, draft_id: int, reason: Optional[str] = None) -> bool:
        """Reject a draft and mark lead as rejected."""
        draft = session.query(OutreachDraft).filter(OutreachDraft.id == draft_id).first()
        if not draft:
            return False

        draft.status = "rejected"
        draft.notes = reason
        if draft.lead:
            draft.lead.status = "rejected"

        session.commit()
        return True

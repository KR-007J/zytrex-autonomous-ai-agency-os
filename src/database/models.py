"""SQLAlchemy ORM Models for Lead Generation & Outreach Agent."""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import json

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Index,
    Boolean,
    Float,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=False, index=True)
    contact_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(100), nullable=True)
    source_url = Column(String(1024), nullable=True)
    source_domain = Column(String(255), nullable=True, index=True)
    industry_tag = Column(String(100), nullable=True, index=True)
    location = Column(String(255), nullable=True)
    linkedin_url = Column(String(1024), nullable=True)
    lead_score = Column(Integer, default=0)
    status = Column(String(50), default="new", index=True)  # new, enriched, drafted, contacted, rejected
    raw_snippet = Column(Text, nullable=True)
    custom_metadata = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    drafts = relationship("OutreachDraft", back_populates="lead", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "company_name": self.company_name,
            "contact_name": self.contact_name,
            "email": self.email,
            "phone": self.phone,
            "source_url": self.source_url,
            "source_domain": self.source_domain,
            "industry_tag": self.industry_tag,
            "location": self.location,
            "linkedin_url": self.linkedin_url,
            "lead_score": self.lead_score,
            "status": self.status,
            "raw_snippet": self.raw_snippet,
            "custom_metadata": json.loads(self.custom_metadata) if self.custom_metadata else {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_name = Column(String(255), nullable=False)
    target_site = Column(String(255), nullable=False)
    status = Column(String(50), default="running")  # running, completed, failed
    leads_found = Column(Integer, default=0)
    leads_new = Column(Integer, default=0)
    error_log = Column(Text, nullable=True)
    started_at = Column(DateTime, default=utc_now, nullable=False)
    finished_at = Column(DateTime, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "job_name": self.job_name,
            "target_site": self.target_site,
            "status": self.status,
            "leads_found": self.leads_found,
            "leads_new": self.leads_new,
            "error_log": self.error_log,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }


class OutreachDraft(Base):
    __tablename__ = "outreach_drafts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    template_id = Column(String(100), nullable=False)
    subject = Column(String(512), nullable=False)
    personalized_message = Column(Text, nullable=False)
    status = Column(String(50), default="pending_review", index=True)  # pending_review, approved, sent, rejected
    created_at = Column(DateTime, default=utc_now, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    lead = relationship("Lead", back_populates="drafts")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "template_id": self.template_id,
            "subject": self.subject,
            "personalized_message": self.personalized_message,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "notes": self.notes,
            "lead": self.lead.to_dict() if self.lead else None,
        }


class ContactedMemory(Base):
    __tablename__ = "contacted_memory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    identifier = Column(String(255), unique=True, nullable=False, index=True)  # email, domain, or linkedin url
    lead_id = Column(Integer, nullable=True)
    channel = Column(String(50), default="linkedin_manual")  # linkedin_manual, linkedin_api, email
    contacted_at = Column(DateTime, default=utc_now, nullable=False)
    notes = Column(Text, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "identifier": self.identifier,
            "lead_id": self.lead_id,
            "channel": self.channel,
            "contacted_at": self.contacted_at.isoformat() if self.contacted_at else None,
            "notes": self.notes,
        }

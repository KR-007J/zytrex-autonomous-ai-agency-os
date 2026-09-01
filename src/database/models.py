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


# ==============================================================================
# ENTERPRISE GLOBAL LEAD GEN DATA PLATFORM MODELS
# ==============================================================================

class GlobalEnterpriseLead(Base):
    __tablename__ = "global_enterprise_leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain_hash = Column(String(64), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    region = Column(String(100), nullable=False, index=True)
    country_code = Column(String(10), nullable=False, index=True)
    live_url = Column(String(1024), nullable=False)
    source_domain = Column(String(255), nullable=False, index=True)
    contact_email = Column(String(255), nullable=True, index=True)
    contact_phone = Column(String(100), nullable=True)
    platform_cms = Column(String(100), default="Custom", nullable=False, index=True)  # OpenCart, WordPress, Shopify, Next.js, Custom
    tech_stack = Column(Text, nullable=True)  # JSON array string
    source = Column(String(100), default="Crawlee Ingestion", nullable=False)
    confidence_score = Column(Integer, default=95, index=True)
    compliance_status = Column(String(50), default="VERIFIED_PUBLIC", index=True)  # VERIFIED_PUBLIC, CORPORATE_GENERIC, SUPPRESSED
    raw_metadata = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_global_cat_reg_score", "category", "region", "confidence_score"),
        Index("idx_global_country_cat", "country_code", "category"),
        Index("idx_global_platform", "platform_cms"),
    )

    def to_dict(self) -> Dict[str, Any]:
        techs = []
        if self.tech_stack:
            try:
                techs = json.loads(self.tech_stack)
            except Exception:
                techs = [s.strip() for s in self.tech_stack.split(",") if s.strip()]

        return {
            "id": self.id,
            "domain_hash": self.domain_hash,
            "company_name": self.company_name,
            "category": self.category,
            "region": self.region,
            "country_code": self.country_code,
            "live_url": self.live_url,
            "source_domain": self.source_domain,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "platform_cms": self.platform_cms,
            "tech_stack": techs,
            "source": self.source,
            "confidence_score": self.confidence_score,
            "compliance_status": self.compliance_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SuppressionRecord(Base):
    __tablename__ = "suppression_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain_or_email = Column(String(255), unique=True, nullable=False, index=True)
    reason = Column(String(100), default="User Requested Opt-Out / Compliance DNC", nullable=False)
    scope = Column(String(50), default="GLOBAL", nullable=False)  # GLOBAL, REGION_EU, REGION_US
    notes = Column(Text, nullable=True)
    added_at = Column(DateTime, default=utc_now, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "domain_or_email": self.domain_or_email,
            "reason": self.reason,
            "scope": self.scope,
            "notes": self.notes,
            "added_at": self.added_at.isoformat() if self.added_at else None,
        }


class IngestionPipelineJob(Base):
    __tablename__ = "ingestion_pipeline_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pipeline_type = Column(String(100), nullable=False)  # crawlee_search_seed, common_crawl_bulk, open_knowledge_api
    category_filter = Column(String(100), nullable=False)
    region_filter = Column(String(100), nullable=False)
    status = Column(String(50), default="RUNNING")  # RUNNING, COMPLETED, FAILED
    seeds_discovered = Column(Integer, default=0)
    pages_crawled = Column(Integer, default=0)
    leads_extracted = Column(Integer, default=0)
    error_log = Column(Text, nullable=True)
    started_at = Column(DateTime, default=utc_now, nullable=False)
    finished_at = Column(DateTime, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "pipeline_type": self.pipeline_type,
            "category_filter": self.category_filter,
            "region_filter": self.region_filter,
            "status": self.status,
            "seeds_discovered": self.seeds_discovered,
            "pages_crawled": self.pages_crawled,
            "leads_extracted": self.leads_extracted,
            "error_log": self.error_log,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }

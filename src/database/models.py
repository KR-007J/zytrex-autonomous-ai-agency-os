"""SQLAlchemy database models for LeadForge."""

from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    canonical_url = Column(String(1024), nullable=False)
    business_name = Column(String(255), nullable=True, index=True)
    description = Column(Text, nullable=True)

    country = Column(String(100), nullable=True, index=True)
    region = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True, index=True)

    status = Column(String(50), default="UNKNOWN", index=True)  # LIVE, OFFLINE, STALE
    http_status = Column(Integer, nullable=True)
    has_ssl = Column(Boolean, default=False)
    response_time_ms = Column(Float, default=0.0)

    primary_technology = Column(String(100), nullable=True, index=True)
    technology_category = Column(String(100), nullable=True)
    technology_confidence = Column(Float, default=0.0)

    evidence_json = Column(Text, default="[]")
    technologies_json = Column(Text, default="[]")
    emails_json = Column(Text, default="[]")
    primary_email = Column(String(255), nullable=True, index=True)
    phones_json = Column(Text, default="[]")
    primary_phone = Column(String(100), nullable=True)
    socials_json = Column(Text, default="{}")

    lead_score = Column(Integer, default=0, index=True)
    score_label = Column(String(20), default="LOW")
    score_reasons_json = Column(Text, default="[]")

    source = Column(String(100), default="LIVE_CRAWL")
    is_demo = Column(Boolean, default=False)

    discovered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_verified_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_changed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    events = relationship("LeadEvent", back_populates="lead", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "domain": self.domain,
            "canonical_url": self.canonical_url,
            "business_name": self.business_name or self.domain,
            "description": self.description,
            "country": self.country,
            "region": self.region,
            "industry": self.industry or "General",
            "status": self.status,
            "http_status": self.http_status,
            "has_ssl": self.has_ssl,
            "response_time_ms": self.response_time_ms,
            "primary_technology": self.primary_technology or "Custom / Unknown",
            "technology_category": self.technology_category,
            "technology_confidence": self.technology_confidence,
            "evidence": json.loads(self.evidence_json or "[]"),
            "technologies": json.loads(self.technologies_json or "[]"),
            "emails": json.loads(self.emails_json or "[]"),
            "primary_email": self.primary_email,
            "phones": json.loads(self.phones_json or "[]"),
            "primary_phone": self.primary_phone,
            "socials": json.loads(self.socials_json or "{}"),
            "lead_score": self.lead_score,
            "score_label": self.score_label,
            "score_reasons": json.loads(self.score_reasons_json or "[]"),
            "source": self.source,
            "is_demo": self.is_demo,
            "discovered_at": self.discovered_at.isoformat() if self.discovered_at else None,
            "last_verified_at": self.last_verified_at.isoformat() if self.last_verified_at else None,
        }


class LeadEvent(Base):
    __tablename__ = "lead_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    lead = relationship("Lead", back_populates="events")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "event_type": self.event_type,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DiscoveryJob(Base):
    __tablename__ = "discovery_jobs"

    id = Column(String(64), primary_key=True)
    technology = Column(String(100), nullable=False)
    country = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    status = Column(String(50), default="QUEUED")  # QUEUED, RUNNING, COMPLETED, FAILED
    progress_percent = Column(Integer, default=0)
    candidates_count = Column(Integer, default=0)
    verified_count = Column(Integer, default=0)
    qualified_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "technology": self.technology,
            "country": self.country,
            "industry": self.industry,
            "status": self.status,
            "progress_percent": self.progress_percent,
            "candidates_count": self.candidates_count,
            "verified_count": self.verified_count,
            "qualified_count": self.qualified_count,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    prefix = Column(String(12), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "prefix": self.prefix,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "is_active": self.is_active,
        }


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(100), nullable=True)
    details_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": json.loads(self.details_json or "{}"),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

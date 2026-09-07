"""SQLAlchemy database models for LeadForge Multi-Tenant Architecture."""

from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="organization", cascade="all, delete-orphan")
    lead_lists = relationship("LeadList", back_populates="organization", cascade="all, delete-orphan")
    saved_searches = relationship("SavedSearch", back_populates="organization", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="organization")
    webhooks = relationship("Webhook", back_populates="organization", cascade="all, delete-orphan")
    export_jobs = relationship("ExportJob", back_populates="organization", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="viewer", nullable=False)  # "owner", "admin", "analyst", "viewer"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    organization = relationship("Organization", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    organization = relationship("Organization", back_populates="projects")
    leads = relationship("Lead", back_populates="project")
    lead_lists = relationship("LeadList", back_populates="project")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LeadList(Base):
    __tablename__ = "lead_lists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    organization = relationship("Organization", back_populates="lead_lists")
    project = relationship("Project", back_populates="lead_lists")
    members = relationship("LeadListMember", back_populates="lead_list", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LeadListMember(Base):
    __tablename__ = "lead_list_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    list_id = Column(Integer, ForeignKey("lead_lists.id"), nullable=False, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    lead_list = relationship("LeadList", back_populates="members")
    lead = relationship("Lead", back_populates="list_memberships")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "list_id": self.list_id,
            "lead_id": self.lead_id,
            "added_at": self.added_at.isoformat() if self.added_at else None,
        }


class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    filters_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    organization = relationship("Organization", back_populates="saved_searches")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "name": self.name,
            "filters": json.loads(self.filters_json or "{}"),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)

    domain = Column(String(255), nullable=False, index=True)
    canonical_url = Column(String(1024), nullable=False)
    business_name = Column(String(255), nullable=True, index=True)
    description = Column(Text, nullable=True)

    country = Column(String(100), nullable=True, index=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
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

    # Relationships
    organization = relationship("Organization", back_populates="leads")
    project = relationship("Project", back_populates="leads")
    events = relationship("LeadEvent", back_populates="lead", cascade="all, delete-orphan")
    technology_changes = relationship("TechnologyChange", back_populates="lead", cascade="all, delete-orphan")
    list_memberships = relationship("LeadListMember", back_populates="lead", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "project_id": self.project_id,
            "domain": self.domain,
            "canonical_url": self.canonical_url,
            "business_name": self.business_name or self.domain,
            "description": self.description,
            "country": self.country,
            "region": self.region,
            "city": self.city,
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
            "last_changed_at": self.last_changed_at.isoformat() if self.last_changed_at else None,
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


class TechnologyChange(Base):
    __tablename__ = "technology_changes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    old_technology = Column(String(100), nullable=True)
    new_technology = Column(String(100), nullable=False)
    evidence_json = Column(Text, default="[]")
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    lead = relationship("Lead", back_populates="technology_changes")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "old_technology": self.old_technology,
            "new_technology": self.new_technology,
            "evidence": json.loads(self.evidence_json or "[]"),
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
        }


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    url = Column(String(1024), nullable=False)
    secret = Column(String(255), nullable=False)
    events_json = Column(Text, default="[]")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="webhooks")
    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "url": self.url,
            "events": json.loads(self.events_json or "[]"),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# Model alias for enterprise naming consistency
WebhookEndpoint = Webhook


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    webhook_id = Column(Integer, ForeignKey("webhooks.id"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    payload_json = Column(Text, default="{}")
    status_code = Column(Integer, nullable=True)
    success = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    delivered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    webhook = relationship("Webhook", back_populates="deliveries")

    @property
    def endpoint_id(self) -> int:
        return self.webhook_id

    @endpoint_id.setter
    def endpoint_id(self, val: int) -> None:
        self.webhook_id = val

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "webhook_id": self.webhook_id,
            "endpoint_id": self.webhook_id,
            "event_type": self.event_type,
            "payload": json.loads(self.payload_json or "{}"),
            "status_code": self.status_code,
            "success": self.success,
            "error_message": self.error_message,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
        }


class ExportJob(Base):
    __tablename__ = "export_jobs"

    id = Column(String(64), primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    format = Column(String(20), nullable=False)
    status = Column(String(50), default="PENDING")
    row_count = Column(Integer, default=0)
    file_path = Column(String(1024), nullable=True)
    file_size = Column(Integer, default=0)
    filters_json = Column(Text, default="{}")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    organization = relationship("Organization", back_populates="export_jobs")

    @property
    def total_records(self) -> int:
        return self.row_count

    @total_records.setter
    def total_records(self, val: int) -> None:
        self.row_count = val

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "format": self.format,
            "status": self.status,
            "row_count": self.row_count,
            "total_records": self.row_count,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "error_message": self.error_message,
            "filters": json.loads(self.filters_json or "{}"),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    prefix = Column(String(12), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_used_at = Column(DateTime, nullable=True)

    organization = relationship("Organization", back_populates="api_keys")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "name": self.name,
            "prefix": self.prefix,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(100), nullable=True)
    details_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": json.loads(self.details_json or "{}"),
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

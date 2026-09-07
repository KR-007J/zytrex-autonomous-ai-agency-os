"""Multi-Tenant Data Access Repositories for LeadForge Enterprise."""

from __future__ import annotations
import json
import secrets
import hashlib
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any

from sqlalchemy import func, or_, desc
from sqlalchemy.orm import Session

from src.database.models import (
    Organization,
    User,
    Project,
    LeadList,
    LeadListMember,
    SavedSearch,
    Lead,
    LeadEvent,
    TechnologyChange,
    Webhook,
    WebhookDelivery,
    ExportJob,
    ApiKey,
    AuditLog,
    DiscoveryJob,
)
from src.security.auth import hash_password, verify_password


class OrganizationRepository:
    """Repository for managing organizations."""

    @classmethod
    def create_organization(cls, session: Session, name: str, slug: Optional[str] = None) -> Organization:
        clean_slug = slug or name.lower().replace(" ", "-").replace("_", "-")
        org = Organization(name=name, slug=clean_slug)
        session.add(org)
        session.flush()
        return org

    @classmethod
    def get_by_id(cls, session: Session, org_id: int) -> Optional[Organization]:
        return session.query(Organization).filter(Organization.id == org_id).first()

    @classmethod
    def get_by_slug(cls, session: Session, slug: str) -> Optional[Organization]:
        return session.query(Organization).filter(Organization.slug == slug).first()

    @classmethod
    def list_all(cls, session: Session) -> List[Organization]:
        return session.query(Organization).order_by(Organization.id).all()

    @classmethod
    def delete_organization(cls, session: Session, org_id: int) -> bool:
        org = cls.get_by_id(session, org_id)
        if not org:
            return False
        session.delete(org)
        session.flush()
        return True


class UserRepository:
    """Repository for managing users and credentials."""

    @classmethod
    def create_user(
        cls,
        session: Session,
        organization_id: int,
        email: str,
        password: str,
        role: str = "viewer",
        is_active: bool = True,
    ) -> User:
        user = User(
            organization_id=organization_id,
            email=email.lower().strip(),
            hashed_password=hash_password(password),
            role=role,
            is_active=is_active,
        )
        session.add(user)
        session.flush()
        return user

    @classmethod
    def get_by_id(cls, session: Session, user_id: int, organization_id: Optional[int] = None) -> Optional[User]:
        q = session.query(User).filter(User.id == user_id)
        if organization_id is not None:
            q = q.filter(User.organization_id == organization_id)
        return q.first()

    @classmethod
    def get_by_email(cls, session: Session, email: str) -> Optional[User]:
        return session.query(User).filter(User.email == email.lower().strip()).first()

    @classmethod
    def list_by_org(cls, session: Session, organization_id: int) -> List[User]:
        return session.query(User).filter(User.organization_id == organization_id).order_by(User.id).all()

    @classmethod
    def update_role(
        cls, session: Session, user_id: int, new_role: str, organization_id: Optional[int] = None
    ) -> Optional[User]:
        user = cls.get_by_id(session, user_id, organization_id)
        if not user:
            return None
        user.role = new_role
        session.flush()
        return user

    @classmethod
    def authenticate(cls, session: Session, email: str, password: str) -> Optional[User]:
        user = cls.get_by_email(session, email)
        if not user or not user.is_active:
            return None
        if verify_password(password, user.hashed_password):
            return user
        return None

    @classmethod
    def delete_user(cls, session: Session, user_id: int, organization_id: Optional[int] = None) -> bool:
        user = cls.get_by_id(session, user_id, organization_id)
        if not user:
            return False
        session.delete(user)
        session.flush()
        return True


class ProjectRepository:
    """Repository for multi-tenant workspace projects."""

    @classmethod
    def create_project(
        cls,
        session: Session,
        organization_id: int,
        name: str,
        description: Optional[str] = None,
    ) -> Project:
        project = Project(
            organization_id=organization_id,
            name=name,
            description=description,
        )
        session.add(project)
        session.flush()
        return project

    @classmethod
    def get_by_id(cls, session: Session, project_id: int, organization_id: Optional[int] = None) -> Optional[Project]:
        q = session.query(Project).filter(Project.id == project_id)
        if organization_id is not None:
            q = q.filter(Project.organization_id == organization_id)
        return q.first()

    @classmethod
    def list_by_org(cls, session: Session, organization_id: int) -> List[Project]:
        return session.query(Project).filter(Project.organization_id == organization_id).order_by(Project.id).all()

    @classmethod
    def delete_project(cls, session: Session, project_id: int, organization_id: Optional[int] = None) -> bool:
        project = cls.get_by_id(session, project_id, organization_id)
        if not project:
            return False
        session.delete(project)
        session.flush()
        return True


class LeadListRepository:
    """Repository for lead lists and memberships."""

    @classmethod
    def create_list(
        cls,
        session: Session,
        organization_id: int,
        name: str,
        description: Optional[str] = None,
        project_id: Optional[int] = None,
    ) -> LeadList:
        lead_list = LeadList(
            organization_id=organization_id,
            name=name,
            description=description,
            project_id=project_id,
        )
        session.add(lead_list)
        session.flush()
        return lead_list

    @classmethod
    def get_by_id(cls, session: Session, list_id: int, organization_id: Optional[int] = None) -> Optional[LeadList]:
        q = session.query(LeadList).filter(LeadList.id == list_id)
        if organization_id is not None:
            q = q.filter(LeadList.organization_id == organization_id)
        return q.first()

    @classmethod
    def list_by_org(
        cls, session: Session, organization_id: int, project_id: Optional[int] = None
    ) -> List[LeadList]:
        q = session.query(LeadList).filter(LeadList.organization_id == organization_id)
        if project_id is not None:
            q = q.filter(LeadList.project_id == project_id)
        return q.order_by(LeadList.id).all()

    @classmethod
    def add_lead_to_list(cls, session: Session, list_id: int, lead_id: int) -> LeadListMember:
        member = session.query(LeadListMember).filter(
            LeadListMember.list_id == list_id,
            LeadListMember.lead_id == lead_id,
        ).first()
        if not member:
            member = LeadListMember(list_id=list_id, lead_id=lead_id)
            session.add(member)
            session.flush()
        return member

    @classmethod
    def remove_lead_from_list(cls, session: Session, list_id: int, lead_id: int) -> bool:
        member = session.query(LeadListMember).filter(
            LeadListMember.list_id == list_id,
            LeadListMember.lead_id == lead_id,
        ).first()
        if not member:
            return False
        session.delete(member)
        session.flush()
        return True

    @classmethod
    def get_list_leads(cls, session: Session, list_id: int, organization_id: Optional[int] = None) -> List[Lead]:
        q = session.query(Lead).join(LeadListMember, Lead.id == LeadListMember.lead_id).filter(
            LeadListMember.list_id == list_id
        )
        if organization_id is not None:
            q = q.filter(Lead.organization_id == organization_id)
        return q.all()

    @classmethod
    def delete_list(cls, session: Session, list_id: int, organization_id: Optional[int] = None) -> bool:
        lead_list = cls.get_by_id(session, list_id, organization_id)
        if not lead_list:
            return False
        session.delete(lead_list)
        session.flush()
        return True


class SavedSearchRepository:
    """Repository for saved searches and filter presets."""

    @classmethod
    def create_search(
        cls,
        session: Session,
        organization_id: int,
        name: str,
        filters: Dict[str, Any],
    ) -> SavedSearch:
        search = SavedSearch(
            organization_id=organization_id,
            name=name,
            filters_json=json.dumps(filters),
        )
        session.add(search)
        session.flush()
        return search

    @classmethod
    def get_by_id(cls, session: Session, search_id: int, organization_id: Optional[int] = None) -> Optional[SavedSearch]:
        q = session.query(SavedSearch).filter(SavedSearch.id == search_id)
        if organization_id is not None:
            q = q.filter(SavedSearch.organization_id == organization_id)
        return q.first()

    @classmethod
    def list_by_org(cls, session: Session, organization_id: int) -> List[SavedSearch]:
        return session.query(SavedSearch).filter(SavedSearch.organization_id == organization_id).order_by(SavedSearch.id).all()

    @classmethod
    def delete_search(cls, session: Session, search_id: int, organization_id: Optional[int] = None) -> bool:
        search = cls.get_by_id(session, search_id, organization_id)
        if not search:
            return False
        session.delete(search)
        session.flush()
        return True


class TechnologyChangeRepository:
    """Repository for technology detection history and migration tracking."""

    @classmethod
    def record_change(
        cls,
        session: Session,
        lead_id: int,
        old_technology: Optional[str],
        new_technology: str,
        evidence: Optional[List[str]] = None,
    ) -> TechnologyChange:
        change = TechnologyChange(
            lead_id=lead_id,
            old_technology=old_technology,
            new_technology=new_technology,
            evidence_json=json.dumps(evidence or []),
        )
        session.add(change)
        session.flush()
        return change

    @classmethod
    def list_by_lead(cls, session: Session, lead_id: int) -> List[TechnologyChange]:
        return session.query(TechnologyChange).filter(
            TechnologyChange.lead_id == lead_id
        ).order_by(desc(TechnologyChange.detected_at)).all()

    @classmethod
    def list_recent(
        cls, session: Session, organization_id: Optional[int] = None, limit: int = 50
    ) -> List[TechnologyChange]:
        q = session.query(TechnologyChange).join(Lead, TechnologyChange.lead_id == Lead.id)
        if organization_id is not None:
            q = q.filter(Lead.organization_id == organization_id)
        return q.order_by(desc(TechnologyChange.detected_at)).limit(limit).all()


class LeadRepository:
    """Data access repository for Leads with multi-tenant isolation."""

    @classmethod
    def get_lead_by_domain(
        cls, session: Session, domain: str, organization_id: Optional[int] = None
    ) -> Optional[Lead]:
        q = session.query(Lead).filter(Lead.domain == domain.lower().strip())
        if organization_id is not None:
            q = q.filter(Lead.organization_id == organization_id)
        return q.first()

    @classmethod
    def get_lead_by_id(
        cls, session: Session, lead_id: int, organization_id: Optional[int] = None
    ) -> Optional[Lead]:
        q = session.query(Lead).filter(Lead.id == lead_id)
        if organization_id is not None:
            q = q.filter(Lead.organization_id == organization_id)
        return q.first()

    @classmethod
    def upsert_lead(
        cls,
        session: Session,
        domain: str,
        canonical_url: str,
        organization_id: Optional[int] = None,
        project_id: Optional[int] = None,
        business_name: Optional[str] = None,
        description: Optional[str] = None,
        country: Optional[str] = None,
        region: Optional[str] = None,
        city: Optional[str] = None,
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
        lead = cls.get_lead_by_domain(session, domain_clean, organization_id=organization_id)
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
                organization_id=organization_id,
                project_id=project_id,
                domain=domain_clean,
                canonical_url=canonical_url,
                business_name=business_name or domain_clean,
                description=description,
                country=country,
                region=region,
                city=city,
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
            session.flush()
        else:
            # Check technology change detection
            if primary_technology and lead.primary_technology and lead.primary_technology != primary_technology:
                event = LeadEvent(
                    lead_id=lead.id,
                    event_type="TECHNOLOGY_CHANGED",
                    description=f"Migrated from {lead.primary_technology} to {primary_technology}",
                )
                session.add(event)

                tech_change = TechnologyChange(
                    lead_id=lead.id,
                    old_technology=lead.primary_technology,
                    new_technology=primary_technology,
                    evidence_json=json.dumps(evidence),
                    detected_at=now,
                )
                session.add(tech_change)
                lead.last_changed_at = now
                session.flush()

            if organization_id is not None and lead.organization_id is None:
                lead.organization_id = organization_id
            if project_id is not None:
                lead.project_id = project_id

            lead.canonical_url = canonical_url
            if business_name:
                lead.business_name = business_name
            if description:
                lead.description = description
            if country:
                lead.country = country
            if region:
                lead.region = region
            if city:
                lead.city = city
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
        organization_id: Optional[int] = None,
        project_id: Optional[int] = None,
        technology: Optional[str] = None,
        country: Optional[str] = None,
        region: Optional[str] = None,
        city: Optional[str] = None,
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

        if organization_id is not None:
            q = q.filter(Lead.organization_id == organization_id)
        if project_id is not None:
            q = q.filter(Lead.project_id == project_id)
        if technology:
            q = q.filter(Lead.primary_technology.ilike(f"%{technology}%"))
        if country:
            q = q.filter(Lead.country.ilike(f"%{country}%"))
        if region:
            q = q.filter(Lead.region.ilike(f"%{region}%"))
        if city:
            q = q.filter(Lead.city.ilike(f"%{city}%"))
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
                Lead.primary_technology.ilike(pat),
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
    def delete_lead(cls, session: Session, lead_id: int, organization_id: Optional[int] = None) -> bool:
        q = session.query(Lead).filter(Lead.id == lead_id)
        if organization_id is not None:
            q = q.filter(Lead.organization_id == organization_id)
        target = q.first()
        if not target:
            return False
        session.delete(target)
        session.flush()
        return True

    @classmethod
    def get_stats(cls, session: Session, organization_id: Optional[int] = None) -> Dict[str, Any]:
        q = session.query(Lead)
        if organization_id is not None:
            q = q.filter(Lead.organization_id == organization_id)

        total_leads = q.count()
        live_leads = q.filter(Lead.status == "LIVE").count()
        hot_leads = q.filter(Lead.lead_score >= 85).count()
        with_email = q.filter(Lead.primary_email.isnot(None)).count()

        tech_query = session.query(Lead.primary_technology, func.count(Lead.id)).filter(
            Lead.primary_technology.isnot(None)
        )
        if organization_id is not None:
            tech_query = tech_query.filter(Lead.organization_id == organization_id)

        tech_counts = (
            tech_query.group_by(Lead.primary_technology)
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


class ApiKeyRepository:
    """Repository for managing API keys."""

    @classmethod
    def create_key(
        cls, session: Session, name: str, organization_id: Optional[int] = None
    ) -> Tuple[ApiKey, str]:
        raw_key = f"lf_{secrets.token_urlsafe(32)}"
        prefix = raw_key[:10]
        key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

        key = ApiKey(
            organization_id=organization_id,
            name=name,
            key_hash=key_hash,
            prefix=prefix,
            is_active=True,
        )
        session.add(key)
        session.flush()
        return key, raw_key

    @classmethod
    def get_by_hash(cls, session: Session, key_hash: str) -> Optional[ApiKey]:
        return session.query(ApiKey).filter(ApiKey.key_hash == key_hash, ApiKey.is_active == True).first()

    @classmethod
    def get_by_raw_key(cls, session: Session, raw_key: str) -> Optional[ApiKey]:
        h = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        return cls.get_by_hash(session, h)

    @classmethod
    def list_by_org(cls, session: Session, organization_id: Optional[int] = None) -> List[ApiKey]:
        q = session.query(ApiKey).filter(ApiKey.is_active == True)
        if organization_id is not None:
            q = q.filter(ApiKey.organization_id == organization_id)
        return q.order_by(desc(ApiKey.created_at)).all()

    @classmethod
    def revoke_key(cls, session: Session, key_id: int, organization_id: Optional[int] = None) -> bool:
        q = session.query(ApiKey).filter(ApiKey.id == key_id)
        if organization_id is not None:
            q = q.filter(ApiKey.organization_id == organization_id)
        key = q.first()
        if not key:
            return False
        key.is_active = False
        session.flush()
        return True


class AuditLogRepository:
    """Repository for auditing multi-tenant user operations."""

    @classmethod
    def log_action(
        cls,
        session: Session,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        organization_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> AuditLog:
        log = AuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            details_json=json.dumps(details or {}),
        )
        session.add(log)
        session.flush()
        return log

    @classmethod
    def list_by_org(
        cls, session: Session, organization_id: int, limit: int = 100
    ) -> List[AuditLog]:
        return session.query(AuditLog).filter(
            AuditLog.organization_id == organization_id
        ).order_by(desc(AuditLog.created_at)).limit(limit).all()


class WebhookRepository:
    """Repository for outbound event webhooks and deliveries."""

    @classmethod
    def create_webhook(
        cls,
        session: Session,
        organization_id: int,
        url: str,
        secret: str,
        events: Optional[List[str]] = None,
    ) -> Webhook:
        webhook = Webhook(
            organization_id=organization_id,
            url=url,
            secret=secret,
            events_json=json.dumps(events or ["*"]),
            is_active=True,
        )
        session.add(webhook)
        session.flush()
        return webhook

    @classmethod
    def list_by_org(cls, session: Session, organization_id: int) -> List[Webhook]:
        return session.query(Webhook).filter(
            Webhook.organization_id == organization_id,
            Webhook.is_active == True,
        ).all()

    @classmethod
    def record_delivery(
        cls,
        session: Session,
        webhook_id: int,
        event_type: str,
        payload: Dict[str, Any],
        status_code: Optional[int] = None,
        success: bool = False,
        error_message: Optional[str] = None,
    ) -> WebhookDelivery:
        delivery = WebhookDelivery(
            webhook_id=webhook_id,
            event_type=event_type,
            payload_json=json.dumps(payload),
            status_code=status_code,
            success=success,
            error_message=error_message,
        )
        session.add(delivery)
        session.flush()
        return delivery

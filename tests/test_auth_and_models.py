"""Unit and integration tests for LeadForge Multi-Tenancy, Database Models, and Auth."""

import pytest
from datetime import timedelta
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import (
    Base,
    Organization,
    User,
    Project,
    LeadList,
    LeadListMember,
    SavedSearch,
    Lead,
    LeadEvent,
    TechnologyChange,
    ApiKey,
    AuditLog,
    Webhook,
    WebhookDelivery,
)
from src.database.repository import (
    OrganizationRepository,
    UserRepository,
    ProjectRepository,
    LeadListRepository,
    SavedSearchRepository,
    TechnologyChangeRepository,
    LeadRepository,
    ApiKeyRepository,
    AuditLogRepository,
    WebhookRepository,
)
from src.security.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    has_role_permission,
    check_role,
    require_role,
    seed_default_data,
)


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite database session for tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# ==========================================
# 1. Password Verification Tests
# ==========================================

def test_password_hashing_and_verification():
    raw_pass = "SuperSecret_2026!"
    hashed = hash_password(raw_pass)

    assert hashed.startswith("pbkdf2_sha256$")
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(raw_pass, "") is False
    assert verify_password(raw_pass, "corrupted_hash") is False

    # Unique salts ensure distinct hashes for identical plain passwords
    hashed2 = hash_password(raw_pass)
    assert hashed != hashed2
    assert verify_password(raw_pass, hashed2) is True


# ==========================================
# 2. Token Authentication Tests
# ==========================================

def test_jwt_token_creation_and_validation():
    payload = {"sub": "42", "email": "analyst@leadforge.io", "role": "analyst", "org_id": 1}
    token = create_access_token(payload, expires_delta=timedelta(minutes=15))

    decoded = decode_access_token(token)
    assert decoded["sub"] == "42"
    assert decoded["email"] == "analyst@leadforge.io"
    assert decoded["role"] == "analyst"
    assert decoded["org_id"] == 1
    assert "exp" in decoded
    assert "iat" in decoded


def test_jwt_token_tampering_and_expiration():
    payload = {"sub": "1", "role": "admin"}
    token = create_access_token(payload, expires_delta=timedelta(hours=1))

    # Tampered signature
    parts = token.split(".")
    tampered_token = f"{parts[0]}.{parts[1]}.tamperedSignature123"
    with pytest.raises(ValueError, match="Invalid token signature"):
        decode_access_token(tampered_token)

    # Expired token
    expired_token = create_access_token(payload, expires_delta=timedelta(seconds=-10))
    with pytest.raises(ValueError, match="Token has expired"):
        decode_access_token(expired_token)

    # Malformed token
    with pytest.raises(ValueError, match="Token must have exactly 3 parts"):
        decode_access_token("invalid.token")


# ==========================================
# 3. Role Permissions Tests
# ==========================================

def test_role_hierarchy_and_permissions():
    # Owner has complete authority
    assert has_role_permission("owner", ["owner"]) is True
    assert has_role_permission("owner", ["admin"]) is True
    assert has_role_permission("owner", ["analyst"]) is True
    assert has_role_permission("owner", ["viewer"]) is True

    # Admin authority
    assert has_role_permission("admin", ["admin"]) is True
    assert has_role_permission("admin", ["analyst"]) is True
    assert has_role_permission("admin", ["viewer"]) is True
    assert has_role_permission("admin", ["owner"]) is False

    # Analyst authority
    assert has_role_permission("analyst", ["analyst"]) is True
    assert has_role_permission("analyst", ["viewer"]) is True
    assert has_role_permission("analyst", ["admin"]) is False
    assert has_role_permission("analyst", ["owner"]) is False

    # Viewer authority
    assert has_role_permission("viewer", ["viewer"]) is True
    assert has_role_permission("viewer", ["analyst"]) is False
    assert has_role_permission("viewer", ["admin"]) is False
    assert has_role_permission("viewer", ["owner"]) is False


def test_role_dependency_enforcement():
    viewer = User(id=10, organization_id=1, email="viewer@leadforge.io", hashed_password="x", role="viewer")
    admin = User(id=11, organization_id=1, email="admin@leadforge.io", hashed_password="x", role="admin")

    delete_permission = require_role(["owner", "admin"])

    # Viewer cannot delete -> raises HTTP 403 Forbidden
    with pytest.raises(HTTPException) as exc_info:
        delete_permission(viewer)
    assert exc_info.value.status_code == 403
    assert "Action prohibited" in exc_info.value.detail

    # Admin can delete -> returns user cleanly
    allowed_user = delete_permission(admin)
    assert allowed_user.id == 11


# ==========================================
# 4. Multi-Tenant Isolation Tests
# ==========================================

def test_tenant_lead_isolation(db_session):
    # Setup two separate organizations
    org_a = OrganizationRepository.create_organization(db_session, "Acme Corp", "acme")
    org_b = OrganizationRepository.create_organization(db_session, "Beta Ltd", "beta")

    # Add leads to Org A
    LeadRepository.upsert_lead(
        session=db_session,
        organization_id=org_a.id,
        domain="acme-store.com",
        canonical_url="https://acme-store.com",
        business_name="Acme Store",
        primary_technology="Shopify",
        country="US",
        lead_score=92,
        status="LIVE",
    )

    # Add leads to Org B
    LeadRepository.upsert_lead(
        session=db_session,
        organization_id=org_b.id,
        domain="beta-tech.com",
        canonical_url="https://beta-tech.com",
        business_name="Beta Tech",
        primary_technology="WooCommerce",
        country="DE",
        lead_score=88,
        status="LIVE",
    )

    # Org A queries leads
    org_a_leads, total_a = LeadRepository.query_leads(db_session, organization_id=org_a.id)
    assert total_a == 1
    assert len(org_a_leads) == 1
    assert org_a_leads[0].domain == "acme-store.com"

    # Org B queries leads
    org_b_leads, total_b = LeadRepository.query_leads(db_session, organization_id=org_b.id)
    assert total_b == 1
    assert len(org_b_leads) == 1
    assert org_b_leads[0].domain == "beta-tech.com"

    # Org A cannot access Org B lead by ID
    lead_b_id = org_b_leads[0].id
    isolated_lead = LeadRepository.get_lead_by_id(db_session, lead_b_id, organization_id=org_a.id)
    assert isolated_lead is None

    # Org A cannot delete Org B lead
    delete_result = LeadRepository.delete_lead(db_session, lead_b_id, organization_id=org_a.id)
    assert delete_result is False
    assert LeadRepository.get_lead_by_id(db_session, lead_b_id, organization_id=org_b.id) is not None

    # Isolated statistics
    stats_a = LeadRepository.get_stats(db_session, organization_id=org_a.id)
    assert stats_a["total_leads"] == 1
    assert stats_a["technologies"][0]["name"] == "Shopify"

    stats_b = LeadRepository.get_stats(db_session, organization_id=org_b.id)
    assert stats_b["total_leads"] == 1
    assert stats_b["technologies"][0]["name"] == "WooCommerce"


# ==========================================
# 5. Technology Changes Detection & Audit Log
# ==========================================

def test_technology_change_detection(db_session):
    org = OrganizationRepository.create_organization(db_session, "Tech Tracker Org", "tech-tracker")

    # 1. Initial discovery with Magento
    lead, created = LeadRepository.upsert_lead(
        session=db_session,
        organization_id=org.id,
        domain="fashion-store.io",
        canonical_url="https://fashion-store.io",
        primary_technology="Magento",
        evidence=["magento-cookie", "skin/frontend"],
    )
    assert created is True
    assert lead.primary_technology == "Magento"

    # Verify no tech change logged initially
    changes = TechnologyChangeRepository.list_by_lead(db_session, lead.id)
    assert len(changes) == 0

    # 2. Re-crawl detects migration to Shopify
    updated_lead, updated_created = LeadRepository.upsert_lead(
        session=db_session,
        organization_id=org.id,
        domain="fashion-store.io",
        canonical_url="https://fashion-store.io",
        primary_technology="Shopify",
        evidence=["cdn.shopify.com"],
    )
    assert updated_created is False
    assert updated_lead.primary_technology == "Shopify"

    # Verify TechnologyChange record created
    changes = TechnologyChangeRepository.list_by_lead(db_session, lead.id)
    assert len(changes) == 1
    assert changes[0].old_technology == "Magento"
    assert changes[0].new_technology == "Shopify"
    assert "cdn.shopify.com" in changes[0].to_dict()["evidence"]

    # Verify recent changes query
    recent = TechnologyChangeRepository.list_recent(db_session, organization_id=org.id)
    assert len(recent) == 1
    assert recent[0].lead_id == lead.id


# ==========================================
# 6. Projects, Lead Lists, & Saved Searches
# ==========================================

def test_projects_and_lead_lists(db_session):
    org = OrganizationRepository.create_organization(db_session, "Outreach Co", "outreach-co")

    # Project
    project = ProjectRepository.create_project(
        db_session, organization_id=org.id, name="Q4 E-Commerce Campaign", description="Targeting Shopify stores"
    )
    assert project.id is not None
    assert project.name == "Q4 E-Commerce Campaign"

    # Lead
    lead, _ = LeadRepository.upsert_lead(
        db_session,
        organization_id=org.id,
        project_id=project.id,
        domain="store123.com",
        canonical_url="https://store123.com",
        city="Austin",
    )
    assert lead.project_id == project.id
    assert lead.city == "Austin"

    # Lead List
    lead_list = LeadListRepository.create_list(
        db_session, organization_id=org.id, name="High Priority Leads", project_id=project.id
    )
    assert lead_list.id is not None

    # Add lead to list
    membership = LeadListRepository.add_lead_to_list(db_session, lead_list.id, lead.id)
    assert membership.list_id == lead_list.id
    assert membership.lead_id == lead.id

    list_leads = LeadListRepository.get_list_leads(db_session, lead_list.id, organization_id=org.id)
    assert len(list_leads) == 1
    assert list_leads[0].domain == "store123.com"

    # Saved Search
    search = SavedSearchRepository.create_search(
        db_session,
        organization_id=org.id,
        name="US Shopify High Score",
        filters={"technology": "Shopify", "country": "US", "min_score": 80},
    )
    assert search.id is not None
    searches = SavedSearchRepository.list_by_org(db_session, org.id)
    assert len(searches) == 1
    assert searches[0].to_dict()["filters"]["technology"] == "Shopify"


# ==========================================
# 7. API Keys and Audit Logging
# ==========================================

def test_api_keys_and_audit_logging(db_session):
    org = OrganizationRepository.create_organization(db_session, "Enterprise Org", "enterprise")

    # API Key creation
    key_record, raw_key = ApiKeyRepository.create_key(db_session, "Production Webhook Key", organization_id=org.id)
    assert raw_key.startswith("lf_")
    assert key_record.prefix == raw_key[:10]

    # Verify retrieval
    found = ApiKeyRepository.get_by_raw_key(db_session, raw_key)
    assert found is not None
    assert found.id == key_record.id

    # Revoke key
    ApiKeyRepository.revoke_key(db_session, key_record.id, organization_id=org.id)
    assert ApiKeyRepository.get_by_raw_key(db_session, raw_key) is None

    # Audit Logging
    user = UserRepository.create_user(db_session, org.id, "auditor@leadforge.io", "pass123", role="admin")
    log = AuditLogRepository.log_action(
        db_session,
        action="EXPORT_CREATED",
        resource_type="export_job",
        resource_id="exp_123",
        details={"format": "csv", "count": 500},
        organization_id=org.id,
        user_id=user.id,
    )
    assert log.id is not None
    logs = AuditLogRepository.list_by_org(db_session, org.id)
    assert len(logs) == 1
    assert logs[0].action == "EXPORT_CREATED"
    assert logs[0].to_dict()["details"]["format"] == "csv"


# ==========================================
# 8. Webhook Management & Seed Default Data
# ==========================================

def test_webhook_deliveries_and_seed_data(db_session):
    # Test Default Seed
    org, admin = seed_default_data(db_session)
    assert org.slug == "default-organization"
    assert admin.email == "admin@leadforge.io"
    assert admin.role == "admin"
    assert verify_password("leadforge123", admin.hashed_password) is True

    # Calling seed_default_data again is idempotent
    org2, admin2 = seed_default_data(db_session)
    assert org2.id == org.id
    assert admin2.id == admin.id

    # Test Webhooks
    hook = WebhookRepository.create_webhook(
        db_session,
        organization_id=org.id,
        url="https://webhook.site/test",
        secret="whsec_123456",
        events=["lead.created", "lead.technology_changed"],
    )
    assert hook.id is not None

    delivery = WebhookRepository.record_delivery(
        db_session,
        webhook_id=hook.id,
        event_type="lead.technology_changed",
        payload={"lead_id": 1, "old_tech": "WooCommerce", "new_tech": "Shopify"},
        status_code=200,
        success=True,
    )
    assert delivery.success is True
    assert delivery.status_code == 200

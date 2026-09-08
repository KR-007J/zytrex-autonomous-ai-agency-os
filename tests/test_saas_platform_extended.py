"""Tests for SaaS platform extended endpoints: Auth, Organization, Audit, Jobs, Dashboard, and SPA."""

import pytest
from fastapi.testclient import TestClient
from src.api.app import app
from src.database.db import get_db
from src.security.auth import seed_default_data

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_seed():
    with get_db() as session:
        seed_default_data(session)


def test_auth_endpoints():
    # 1. Successful Login
    res = client.post("/api/v1/auth/login", json={
        "email": "admin@leadforge.io",
        "password": "leadforge123"
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "admin@leadforge.io"

    # 2. Failed Login
    bad_res = client.post("/api/v1/auth/login", json={
        "email": "admin@leadforge.io",
        "password": "wrongpass"
    })
    assert bad_res.status_code == 401

    # 3. Signup New User
    import uuid
    new_email = f"testnewuser_{uuid.uuid4().hex[:8]}@example.com"
    signup_res = client.post("/api/v1/auth/signup", json={
        "email": new_email,
        "password": "securePass123!",
        "organization_name": "Acme Corp",
        "role": "admin"
    })
    assert signup_res.status_code == 200
    signup_data = signup_res.json()
    assert signup_data["user"]["email"] == new_email
    assert signup_data["organization"]["name"] == "Acme Corp"

    # 4. Get Current User Profile (/auth/me)
    token = signup_data["access_token"]
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert "user" in me_data
    assert me_data["user"]["email"] == "admin@leadforge.io" or me_data["user"]["email"] == new_email


def test_organization_endpoints():
    # 1. Get Org
    res = client.get("/api/v1/organization")
    assert res.status_code == 200
    assert "name" in res.json()

    # 2. Update Org
    patch_res = client.patch("/api/v1/organization", json={"name": "Updated LeadForge Org"})
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Updated LeadForge Org"

    # 3. Members list
    members_res = client.get("/api/v1/organization/members")
    assert members_res.status_code == 200
    members = members_res.json()
    assert len(members) >= 1

    # 4. Invite member
    invite_res = client.post("/api/v1/organization/members", json={
        "email": "teammember1@leadforge.io",
        "role": "analyst",
        "password": "Temporary123"
    })
    assert invite_res.status_code == 200
    new_user = invite_res.json()
    assert new_user["role"] == "analyst"
    user_id = new_user["id"]

    # 5. Update member
    update_res = client.patch(f"/api/v1/organization/members/{user_id}", json={
        "role": "viewer",
        "is_active": False
    })
    assert update_res.status_code == 200
    assert update_res.json()["role"] == "viewer"
    assert update_res.json()["is_active"] is False

    # 6. Delete member
    del_res = client.delete(f"/api/v1/organization/members/{user_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "SUCCESS"


def test_audit_logs():
    res = client.get("/api/v1/audit-logs")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "audit_logs" in data
    assert isinstance(data["audit_logs"], list)


def test_unified_jobs():
    res = client.get("/api/v1/jobs")
    assert res.status_code == 200
    jobs = res.json()
    assert isinstance(jobs, list)


def test_dashboard_analytics():
    res = client.get("/api/v1/dashboard/analytics")
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "total_leads" in data["summary"]
    assert "technologies" in data
    assert "geography" in data
    assert "score_distribution" in data
    assert "activity_stream" in data
    assert "providers" in data
    assert len(data["providers"]) >= 6
    assert any(p["type"] == "LiveWebProvider" for p in data["providers"])


def test_spa_catch_all_route():
    # Calling client-side routes should return 200 and index.html
    paths = ["/dashboard", "/discover", "/leads", "/projects", "/technologies", "/webhooks", "/settings"]
    for p in paths:
        res = client.get(p)
        assert res.status_code == 200
        assert "<html" in res.text.lower()

"""Integration tests for FastAPI REST API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.models import Base
from src.database.db import get_db
from src.api.main import app

# In-memory test engine with StaticPool
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"


def test_api_lead_crud_and_export():
    # 1. Create Lead
    payload = {
        "company_name": "Anthropic AI",
        "contact_name": "Dario Amodei",
        "email": "dario@anthropic.com",
        "phone": "+1-415-555-0100",
        "source_url": "https://anthropic.com",
        "industry_tag": "AI Safety & Research",
    }
    create_res = client.post("/api/leads", json=payload)
    assert create_res.status_code == 201
    lead_id = create_res.json()["lead"]["id"]

    # 2. Get Lead by ID
    get_res = client.get(f"/api/leads/{lead_id}")
    assert get_res.status_code == 200
    assert get_res.json()["company_name"] == "Anthropic AI"

    # 3. List Leads
    list_res = client.get("/api/leads?search=Anthropic")
    assert list_res.status_code == 200
    assert len(list_res.json()["items"]) >= 1

    # 4. CSV Export
    csv_res = client.get("/api/leads/export/csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "Anthropic AI" in csv_res.text


def test_api_config_endpoints():
    get_cfg = client.get("/api/config")
    assert get_cfg.status_code == 200
    cfg_data = get_cfg.json()
    assert "scraping" in cfg_data
    assert "linkedin" in cfg_data

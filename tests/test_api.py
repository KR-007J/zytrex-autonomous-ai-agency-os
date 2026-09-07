from fastapi.testclient import TestClient
from src.api.app import app
from src.database.db import get_db, init_db
from src.database.repository import LeadRepository

client = TestClient(app)

def setup_module():
    init_db()

def test_api_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["zero_cost_mode"] is True

def test_api_technologies():
    res = client.get("/api/v1/technologies")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 5
    tech_names = [t["name"] for t in data]
    assert "OpenCart" in tech_names
    assert "Shopify" in tech_names
    assert "WooCommerce" in tech_names

def test_api_keys_workflow():
    # 1. Create key
    res = client.post("/api/v1/api-keys", json={"name": "CI Test Key"})
    assert res.status_code == 200
    data = res.json()
    assert "api_key" in data
    assert data["api_key"].startswith("lf_")
    key_id = data["id"]

    # 2. List keys
    res = client.get("/api/v1/api-keys")
    assert res.status_code == 200
    keys = res.json()
    assert any(k["id"] == key_id for k in keys)

    # 3. Revoke key
    res = client.delete(f"/api/v1/api-keys/{key_id}")
    assert res.status_code == 200
    assert res.json()["status"] == "REVOKED"

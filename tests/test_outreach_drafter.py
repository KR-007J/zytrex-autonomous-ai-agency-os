"""Tests for OutreachDrafter and AI sequence generation API routes."""

import pytest
from fastapi.testclient import TestClient
from src.api.app import app
from src.outreach.ai_drafter import OutreachDrafter


def test_outreach_drafter_tones():
    domain = "teststore.com"
    tech = "Shopify"
    
    # Test founder tone
    seq_founder = OutreachDrafter.draft_sequence(domain, "TestStore", tech, tone="founder", response_time_ms=520.0)
    assert len(seq_founder.subject_lines) >= 3
    assert "founder" in seq_founder.step1_hook_email.lower()
    assert "520ms" in seq_founder.step1_hook_email
    assert len(seq_founder.pain_points_identified) >= 1
    
    # Test consultative tone
    seq_consult = OutreachDrafter.draft_sequence(domain, "TestStore", tech, tone="consultative", response_time_ms=150.0)
    assert "leadership" in seq_consult.step1_hook_email.lower()
    assert "Shopify" in seq_consult.step1_hook_email

    # Test direct tone
    seq_direct = OutreachDrafter.draft_sequence(domain, "TestStore", tech, tone="direct", response_time_ms=250.0)
    assert "Notice you are running" in seq_direct.step1_hook_email


def test_outreach_drafter_tech_customization():
    opencart_seq = OutreachDrafter.draft_sequence("opencart-shop.com", "Shop", "OpenCart", response_time_ms=300.0)
    assert any("opencart" in p.lower() or "mvc" in p.lower() for p in opencart_seq.pain_points_identified)

    woo_seq = OutreachDrafter.draft_sequence("woo-shop.com", "WooShop", "WooCommerce", response_time_ms=600.0)
    assert any("woocommerce" in p.lower() or "database" in p.lower() for p in woo_seq.pain_points_identified)


def test_outreach_api_endpoints():
    client = TestClient(app)
    payload = {
        "domain": "brandshop.com",
        "business_name": "BrandShop",
        "primary_technology": "Shopify",
        "country": "United States",
        "response_time_ms": 195.5,
        "tone": "direct"
    }
    resp = client.post("/api/v1/outreach/draft", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "subject_lines" in data
    assert "step1_hook_email" in data
    assert "step2_followup_email" in data
    assert "step3_breakup_email" in data
    assert "BrandShop" in data["step1_hook_email"]


def test_outreach_api_validation_errors():
    client = TestClient(app)
    # Empty payload with neither domain nor lead_id
    resp = client.post("/api/v1/outreach/draft", json={})
    assert resp.status_code == 400

    # Non-existent lead_id
    resp_404 = client.post("/api/v1/outreach/draft", json={"lead_id": 999999})
    assert resp_404.status_code == 404

"""Tests for Enterprise Cybersecurity Hardening."""

import pytest
from fastapi.testclient import TestClient
from src.api.app import app
from src.security.ssrf import is_ip_allowed, validate_and_resolve_url, SSRFValidationError
from src.export.exporter import EnterpriseExporter

client = TestClient(app)


def test_security_headers_present():
    """Verify that OWASP-compliant security headers are returned on all endpoints."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    headers = response.headers
    
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("x-xss-protection") == "1; mode=block"
    assert "strict-transport-security" in headers
    assert "content-security-policy" in headers
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "permissions-policy" in headers
    assert headers.get("cross-origin-opener-policy") == "same-origin"
    assert headers.get("cross-origin-resource-policy") == "same-origin"


def test_ssrf_metadata_and_ipv6_blocking():
    """Verify that cloud metadata IPs, CGNAT, and IPv4-mapped IPv6 are blocked."""
    # AWS / GCP / Azure metadata
    assert not is_ip_allowed("169.254.169.254")
    assert not is_ip_allowed("169.254.1.1")
    # Alibaba Cloud metadata
    assert not is_ip_allowed("100.100.100.200")
    # Carrier grade NAT
    assert not is_ip_allowed("100.64.0.1")
    # IPv6 loopback & link-local
    assert not is_ip_allowed("::1")
    assert not is_ip_allowed("fe80::1")
    # IPv4-mapped IPv6 loopback
    assert not is_ip_allowed("::ffff:127.0.0.1")
    # IPv4-mapped IPv6 private
    assert not is_ip_allowed("::ffff:192.168.1.1")
    # IPv4-mapped IPv6 metadata
    assert not is_ip_allowed("::ffff:169.254.169.254")
    # Real public IP is allowed
    assert is_ip_allowed("8.8.8.8")
    assert is_ip_allowed("1.1.1.1")


def test_ssrf_port_restrictions():
    """Verify that discovery rejects dangerous non-web ports."""
    with pytest.raises(SSRFValidationError, match="Port '22' is not permitted"):
        validate_and_resolve_url("http://example.com:22")

    with pytest.raises(SSRFValidationError, match="Port '6379' is not permitted"):
        validate_and_resolve_url("http://example.com:6379")

    with pytest.raises(SSRFValidationError, match="Port '3306' is not permitted"):
        validate_and_resolve_url("http://example.com:3306")

    # Permitted web ports should pass hostname resolution
    url, ip, port = validate_and_resolve_url("http://example.com:80")
    assert port == 80

    url, ip, port = validate_and_resolve_url("https://example.com:443")
    assert port == 443


def test_formula_injection_sanitization_edge_cases():
    """Verify spreadsheet sanitization strips dangerous formulas while preserving phone numbers."""
    # Classic formula injection
    assert EnterpriseExporter.sanitize_spreadsheet_value("=1+1") == "'=1+1"
    assert EnterpriseExporter.sanitize_spreadsheet_value("@SUM(1,2)") == "'@SUM(1,2)"
    assert EnterpriseExporter.sanitize_spreadsheet_value("-5+5") == "'-5+5"
    assert EnterpriseExporter.sanitize_spreadsheet_value("+CMD|' /C calc'!A0") == "'+CMD|' /C calc'!A0"

    # Edge cases: leading whitespace before formula symbol
    assert EnterpriseExporter.sanitize_spreadsheet_value("   =cmd|' /C calc'!A0") == "'   =cmd|' /C calc'!A0"
    assert EnterpriseExporter.sanitize_spreadsheet_value("\t=1+1") == "'\t=1+1"
    assert EnterpriseExporter.sanitize_spreadsheet_value("\r@calc") == "'\r@calc"

    # Legitimate phone numbers starting with + are safely preserved
    assert EnterpriseExporter.sanitize_spreadsheet_value("+44 1539 821443") == "+44 1539 821443"
    assert EnterpriseExporter.sanitize_spreadsheet_value("+1 (800) 555-0199") == "+1 (800) 555-0199"
    assert EnterpriseExporter.sanitize_spreadsheet_value("+31854013553") == "+31854013553"


def test_rate_limiter_burst_protection():
    """Verify that exceeding rate limits on discover POST yields HTTP 429."""
    hit_429 = False
    for _ in range(45):
        resp = client.post("/api/v1/discover", json={"technology": "opencart", "limit": 1})
        if resp.status_code == 429:
            hit_429 = True
            assert "RATE_LIMIT_EXCEEDED" in resp.json().get("error", "")
            break
    assert hit_429, "Expected 429 rate limit exceeded response after bursting requests"

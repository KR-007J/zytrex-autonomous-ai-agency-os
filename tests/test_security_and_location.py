"""Unit tests for Cybersecurity Hardening and Real-World Location Intelligence."""

import pytest
from pathlib import Path
from fastapi import HTTPException

from src.scraper.extractors import extract_real_location
from src.api.security import RateLimiter, validate_export_path, mask_sensitive_secrets


def test_real_location_detection_mumbai_and_india():
    # 1. Government portal / Maharashtra test
    loc1 = extract_real_location("Government of Maharashtra tenders and e-governance", "https://maharashtra.gov.in")
    assert "Mumbai" in loc1 or "Maharashtra" in loc1

    # 2. Mumbai tech / business text
    loc2 = extract_real_location("Our corporate headquarters is located at Bandra Kurla Complex (BKC)", "https://fintechcorp.in")
    assert loc2 == "Mumbai, Maharashtra"

    # 3. Bengaluru tech hub
    loc3 = extract_real_location("Software engineering team based in Koramangala and Whitefield", "https://ai-startup.io")
    assert loc3 == "Bengaluru, Karnataka"

    # 4. New York tech hub
    loc4 = extract_real_location("Design agency located in Manhattan, Wall Street", "https://designstudio.com")
    assert loc4 == "New York, NY"


def test_rate_limiter():
    limiter = RateLimiter(requests_per_minute=5)
    ip = "192.168.1.100"
    for _ in range(5):
        assert limiter.is_allowed(ip) is True
    assert limiter.is_allowed(ip) is False


def test_path_traversal_prevention(tmp_path):
    allowed_dir = tmp_path / "exports"
    allowed_dir.mkdir()
    valid_file = allowed_dir / "report.xlsx"
    valid_file.touch()

    # Valid path inside directory
    validated = validate_export_path(valid_file, allowed_dir)
    assert validated == valid_file.resolve()

    # Malicious path traversal attempt
    malicious_path = allowed_dir / ".." / ".." / "etc" / "passwd"
    with pytest.raises(HTTPException) as exc_info:
        validate_export_path(malicious_path, allowed_dir)
    assert exc_info.value.status_code == 403


def test_mask_sensitive_secrets():
    raw_cfg = {
        "app": {"name": "Test"},
        "notifications": {
            "email": {
                "smtp_user": "admin@agency.com",
                "smtp_pass": "SuperSecretPass123!",
            }
        }
    }
    masked = mask_sensitive_secrets(raw_cfg)
    assert masked["notifications"]["email"]["smtp_user"] == "admin@agency.com"
    assert masked["notifications"]["email"]["smtp_pass"] == "••••••••"

import pytest
from src.security.ssrf import validate_and_resolve_url, is_ip_allowed, SSRFValidationError

def test_blocked_ips():
    assert not is_ip_allowed("127.0.0.1")
    assert not is_ip_allowed("10.0.0.1")
    assert not is_ip_allowed("192.168.1.50")
    assert not is_ip_allowed("172.16.0.1")
    assert not is_ip_allowed("169.254.169.254")
    assert not is_ip_allowed("0.0.0.0")
    assert not is_ip_allowed("::1")
    assert is_ip_allowed("8.8.8.8")
    assert is_ip_allowed("1.1.1.1")

def test_blocked_schemes():
    with pytest.raises(SSRFValidationError):
        validate_and_resolve_url("file:///etc/passwd")
    with pytest.raises(SSRFValidationError):
        validate_and_resolve_url("ftp://ftp.example.com")
    with pytest.raises(SSRFValidationError):
        validate_and_resolve_url("gopher://127.0.0.1:70")

def test_blocked_hostnames():
    with pytest.raises(SSRFValidationError):
        validate_and_resolve_url("http://localhost:8000")
    with pytest.raises(SSRFValidationError):
        validate_and_resolve_url("http://127.0.0.1:8000")
    with pytest.raises(SSRFValidationError):
        validate_and_resolve_url("http://169.254.169.254/latest/meta-data/")

def test_allowed_public_domain():
    norm_url, ip, port = validate_and_resolve_url("https://example.com")
    assert norm_url.startswith("https://example.com")
    assert port == 443
    assert is_ip_allowed(ip)

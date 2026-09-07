import pytest
from src.verification.live_verifier import LiveVerifier

@pytest.mark.asyncio
async def test_verifier_blocks_ssrf():
    res = await LiveVerifier.verify("http://127.0.0.1:8000")
    assert not res.is_live
    assert "SSRF Block" in (res.error_message or "")

@pytest.mark.asyncio
async def test_verifier_live_public():
    res = await LiveVerifier.verify("https://example.com")
    assert res.is_live
    assert res.http_status == 200
    assert res.has_ssl
    assert res.freshness_status == "LIVE"
    assert res.response_time_ms > 0

"""Tests for ScraplingProvider and multi-source discovery integration."""

import pytest
from src.discovery.scrapling_provider import ScraplingProvider, clean_domain
from src.discovery.orchestrator import DiscoveryOrchestrator


def test_clean_domain():
    assert clean_domain("https://www.GymShark.com/products?ref=1") == "gymshark.com"
    assert clean_domain("http://VeroBride.com/") == "verobride.com"
    assert clean_domain("rugsco.ca") == "rugsco.ca"
    assert clean_domain("https://google.com/search") is None
    assert clean_domain("https://apps.shopify.com/reviews") is None
    assert clean_domain("invalid-domain") is None
    assert clean_domain("") is None


@pytest.mark.asyncio
async def test_scrapling_provider_health():
    provider = ScraplingProvider()
    health = await provider.health()
    assert health["status"] == "HEALTHY"
    assert "version" in health
    assert "strategies" in health
    assert len(health["strategies"]) >= 4


@pytest.mark.asyncio
async def test_scrapling_provider_stream_shopify():
    provider = ScraplingProvider()
    candidates = []
    async for c in provider.stream("shopify", limit=3):
        candidates.append(c)
        assert c.domain
        assert "." in c.domain
        assert c.technology_hint == "shopify"
        assert c.confidence_hint >= 0.8
    assert len(candidates) == 3


@pytest.mark.asyncio
async def test_scrapling_provider_discover_woocommerce():
    provider = ScraplingProvider()
    candidates = await provider.discover("woocommerce", limit=2)
    assert len(candidates) >= 2
    for c in candidates:
        assert c.domain
        assert "." in c.domain


@pytest.mark.asyncio
async def test_orchestrator_integration():
    orch = DiscoveryOrchestrator()
    # Ensure ScraplingProvider is registered first
    assert isinstance(orch.providers[0], ScraplingProvider)
    
    statuses = await orch.get_providers_status()
    assert any(s.get("provider") == "Scrapling Web Engine" and s.get("status") == "HEALTHY" for s in statuses)

    # Test candidate stream through orchestrator
    candidates = []
    async for c in orch.stream_candidates("shopify", limit=3):
        candidates.append(c)
    assert len(candidates) == 3

"""Tests for expanded technology signatures, discovery providers, and formula injection sanitization."""

import pytest
from unittest.mock import patch, AsyncMock
from src.fingerprint.engine import FingerprintEngine
from src.crawler.contact_extractor import ContactExtractor
from src.discovery.common_crawl import CommonCrawlProvider
from src.discovery.dns_discovery import DNSDiscoveryProvider
from src.discovery.sitemap import SitemapProvider
from src.discovery.orchestrator import orchestrator


# ============================================================================
# 1. TECHNOLOGY SIGNATURE TESTS
# ============================================================================

def test_prestashop_detection():
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <meta name="generator" content="PrestaShop 8.1.0" />
        <script>var prestashop = { theme: "classic" };</script>
        <link rel="stylesheet" href="/themes/classic/assets/css/theme.css" />
      </head>
      <body>
        <div id="wrapper">PrestaShop Store</div>
      </body>
    </html>
    """
    cookies = {"PrestaShop-abc123": "session_data_here"}
    results = FingerprintEngine.detect(html=html, cookies=cookies)
    presta = next((r for r in results if r.tech_id == "prestashop"), None)
    assert presta is not None, "PrestaShop should be detected"
    assert presta.status == "CONFIRMED"
    assert presta.confidence >= 0.70
    assert len(presta.evidence) >= 2


def test_drupal_detection():
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <meta name="generator" content="Drupal 10 (https://www.drupal.org)" />
        <script>Drupal.settings = { path: { baseUrl: "/" } };</script>
      </head>
      <body><h1>Drupal Site</h1></body>
    </html>
    """
    headers = {"X-Generator": "Drupal 10", "X-Drupal-Cache": "HIT"}
    results = FingerprintEngine.detect(html=html, headers=headers)
    drupal = next((r for r in results if r.tech_id == "drupal"), None)
    assert drupal is not None, "Drupal should be detected"
    assert drupal.status == "CONFIRMED"
    assert drupal.confidence >= 0.70


def test_react_detection():
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>React App</title>
        <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
        <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
      </head>
      <body>
        <div id="root" data-reactroot="">
          <div _reactFiber="true">React Component</div>
        </div>
      </body>
    </html>
    """
    results = FingerprintEngine.detect(html=html)
    react = next((r for r in results if r.tech_id == "react"), None)
    assert react is not None, "React should be detected"
    assert react.status == "CONFIRMED"
    assert react.confidence >= 0.70


def test_cloudflare_detection():
    headers = {
        "cf-ray": "8bf123456789-DFW",
        "server": "cloudflare",
        "cf-cache-status": "HIT",
    }
    cookies = {"__cf_bm": "random_token_val_123"}
    results = FingerprintEngine.detect(html="<html><body>Cloudflare Protected</body></html>", headers=headers, cookies=cookies)
    cf = next((r for r in results if r.tech_id == "cloudflare"), None)
    assert cf is not None, "Cloudflare should be detected"
    assert cf.status == "CONFIRMED"
    assert cf.confidence >= 0.70


def test_tailwind_detection():
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <style>@tailwind base; @tailwind components; @tailwind utilities;</style>
        <script src="https://cdn.tailwindcss.com"></script>
      </head>
      <body class="flex items-center justify-between px-4 py-2 bg-blue-600 text-white">
        <div class="grid grid-cols-2 gap-4">Tailwind Layout</div>
      </body>
    </html>
    """
    results = FingerprintEngine.detect(html=html)
    tailwind = next((r for r in results if r.tech_id == "tailwind"), None)
    assert tailwind is not None, "Tailwind CSS should be detected"
    assert tailwind.status == "CONFIRMED"
    assert tailwind.confidence >= 0.65


# ============================================================================
# 2. DISCOVERY PROVIDER TESTS
# ============================================================================

def test_orchestrator_registered_providers():
    provider_names = [p.name for p in orchestrator.providers]
    assert "Scrapling Web Engine" in provider_names
    assert "Live Web & Seed Index" in provider_names
    assert "Certificate Transparency (crt.sh)" in provider_names
    assert "Common Crawl Index" in provider_names
    assert "DNS Infrastructure Discovery" in provider_names
    assert "Sitemap & XML Index Discovery" in provider_names
    assert len(orchestrator.providers) == 7


@pytest.mark.asyncio
async def test_dns_discovery_resolution():
    provider = DNSDiscoveryProvider()
    
    # Mock resolve_records to simulate DNS records for Shopify and Cloudflare infrastructure
    async def mock_resolve(domain: str, record_type: str = "CNAME"):
        if record_type == "CNAME":
            return ["shops.myshopify.com"]
        if record_type == "MX":
            return ["1 aspmx.l.google.com"]
        if record_type == "NS":
            return ["ns1.cloudflare.com"]
        return []

    with patch.object(provider, "resolve_records", side_effect=mock_resolve):
        infra = await provider.inspect_domain_infrastructure("example-shop.com")
        assert "shopify" in infra["detected_technologies"]
        assert "cloudflare" in infra["detected_technologies"]
        assert len(infra["evidence"]) >= 2

    # Verify stream method yields candidate domains
    candidates = []
    async for item in provider.stream("shopify", limit=2):
        candidates.append(item)
    assert len(candidates) > 0
    assert candidates[0].source == "DNS_DISCOVERY"


@pytest.mark.asyncio
async def test_common_crawl_fallback_handling():
    provider = CommonCrawlProvider()

    # Simulate network timeout/error when reaching Common Crawl index API
    with patch("httpx.AsyncClient.get", side_effect=Exception("Connection timed out")):
        candidates = await provider.discover("prestashop", limit=5)
        # Should gracefully fall back to pre-defined fallback domains without crashing
        assert len(candidates) > 0
        assert all(c.source == "COMMON_CRAWL_FALLBACK" for c in candidates)
        assert any("prestashop" in c.domain for c in candidates)


@pytest.mark.asyncio
async def test_sitemap_provider_parsing():
    provider = SitemapProvider()
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://store.targetdomain.com/products/item-1</loc></url>
      <url><loc>https://checkout.partnerplatform.com/cart</loc></url>
    </urlset>
    """

    class MockResponse:
        status_code = 200
        text = sample_xml

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=MockResponse())):
        domains = await provider.fetch_and_parse_sitemap("https://example.com/sitemap.xml", limit=10)
        assert "store.targetdomain.com" in domains
        assert "checkout.partnerplatform.com" in domains


# ============================================================================
# 3. FORMULA INJECTION & ADDRESS EXTRACTION TESTS
# ============================================================================

def test_formula_injection_sanitization():
    # Dangerous formula injection payloads
    assert ContactExtractor.sanitize_formula("=cmd|' /C calc'!A0") == "'=cmd|' /C calc'!A0"
    assert ContactExtractor.sanitize_formula("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert ContactExtractor.sanitize_formula("-100+20") == "'-100+20"
    assert ContactExtractor.sanitize_formula("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"
    assert ContactExtractor.sanitize_formula("\t=dangerous") == "'\t=dangerous"

    # Legitimate values should remain unaffected
    assert ContactExtractor.sanitize_formula("Acme Inc") == "Acme Inc"
    assert ContactExtractor.sanitize_formula("+18005550199", is_phone=True) == "+18005550199"
    assert ContactExtractor.sanitize_formula("+44 20 7946 0912", is_phone=True) == "+44 20 7946 0912"


def test_contact_extractor_with_injection_and_address():
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>=MaliciousCorp - Injected Title</title>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "LocalBusiness",
          "name": "@MaliciousOrg",
          "address": {
            "@type": "PostalAddress",
            "streetAddress": "456 Mission Street",
            "addressLocality": "San Francisco",
            "addressRegion": "CA",
            "postalCode": "94105",
            "addressCountry": "US"
          }
        }
        </script>
      </head>
      <body>
        <p>Email: <a href="mailto:=evil@domain.com">=evil@domain.com</a></p>
        <p>Phone: <a href="tel:+18005550199">+1 (800) 555-0199</a></p>
        <footer>
          <address class="office-location">456 Mission Street, San Francisco, CA 94105</address>
        </footer>
      </body>
    </html>
    """
    res = ContactExtractor.extract_from_html(html, "https://maliciouscorp.com")
    
    # Business name sanitized against '@'
    assert res["business_name"].startswith("'")
    assert "@MaliciousOrg" in res["business_name"]
    
    # Email sanitized against '='
    assert len(res["emails"]) >= 1
    assert res["emails"][0]["value"] == "'=evil@domain.com"
    
    # Legitimate phone preserved with leading '+'
    assert len(res["phones"]) >= 1
    assert res["phones"][0]["value"] == "+18005550199"
    
    # Physical address extracted from JSON-LD or address tag
    assert res["address"] is not None
    assert "Mission Street" in res["address"]
    assert "San Francisco" in res["address"]

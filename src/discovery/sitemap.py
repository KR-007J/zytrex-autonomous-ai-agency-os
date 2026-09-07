"""Sitemap & XML Index Discovery Provider."""

from __future__ import annotations
import logging
from urllib.parse import urlparse
from typing import List, Optional, AsyncGenerator, Dict, Any
import xml.etree.ElementTree as ET
import httpx
from src.discovery.base import DiscoveryProvider, CandidateDomain

logger = logging.getLogger(__name__)

# Technology directory and ecosystem seed domains for sitemap discovery
SITEMAP_SEEDS: Dict[str, List[str]] = {
    "prestashop": ["https://addons.prestashop.com/sitemap.xml", "https://www.prestashop.com/sitemap.xml"],
    "opencart": ["https://www.opencart.com/sitemap.xml"],
    "shopify": ["https://www.shopify.com/sitemap.xml"],
    "wordpress": ["https://wordpress.org/sitemap.xml"],
    "magento": ["https://business.adobe.com/sitemap.xml"],
    "drupal": ["https://www.drupal.org/sitemap.xml"],
}


class SitemapProvider(DiscoveryProvider):
    name = "Sitemap & XML Index Discovery"
    description = "Fetches and parses sitemap.xml and sitemap indexes for target domain discovery."

    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout

    async def fetch_and_parse_sitemap(self, sitemap_url: str, limit: int = 50) -> List[str]:
        """Fetch a sitemap.xml and extract discovered domain candidates."""
        discovered_domains: List[str] = []
        headers = {
            "User-Agent": "LeadForge/2.0 (Sitemap Discovery Intelligence)",
            "Accept": "application/xml, text/xml, */*",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(sitemap_url, headers=headers)
                if resp.status_code == 200 and resp.text:
                    # Strip XML namespaces for simplified ElementTree parsing
                    xml_content = resp.text
                    root = ET.fromstring(xml_content)
                    
                    for elem in root.iter():
                        if elem.tag.endswith("loc") and elem.text:
                            url = elem.text.strip()
                            parsed = urlparse(url)
                            domain = parsed.netloc.lower().split(":")[0].lstrip("www.")
                            if (
                                domain
                                and "." in domain
                                and len(domain) > 4
                                and domain not in discovered_domains
                                and not domain.endswith((".local", ".internal"))
                            ):
                                discovered_domains.append(domain)
                                if len(discovered_domains) >= limit:
                                    break
        except Exception as e:
            logger.debug(f"Failed to fetch/parse sitemap {sitemap_url}: {e}")

        return discovered_domains

    async def discover(
        self,
        technology: str,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        limit: int = 25,
    ) -> List[CandidateDomain]:
        candidates: List[CandidateDomain] = []
        async for item in self.stream(technology, country, industry, limit):
            candidates.append(item)
        return candidates

    async def stream(
        self,
        technology: str,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        limit: int = 25,
    ) -> AsyncGenerator[CandidateDomain, None]:
        tech_key = technology.lower().strip()
        seed_urls = SITEMAP_SEEDS.get(tech_key, [f"https://{tech_key}.com/sitemap.xml"])

        seen_domains = set()
        count = 0

        for url in seed_urls:
            domains = await self.fetch_and_parse_sitemap(url, limit=limit)
            for domain in domains:
                if domain not in seen_domains:
                    seen_domains.add(domain)
                    yield CandidateDomain(
                        domain=domain,
                        source="SITEMAP",
                        technology_hint=technology,
                        country_hint=country,
                        industry_hint=industry,
                        confidence_hint=0.75,
                    )
                    count += 1
                    if count >= limit:
                        return

    async def health(self) -> Dict[str, Any]:
        return {
            "status": "HEALTHY",
            "cost": "ZERO_COST",
            "provider": self.name,
        }

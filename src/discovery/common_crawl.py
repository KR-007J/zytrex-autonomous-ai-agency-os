"""Common Crawl Index Discovery Provider."""

from __future__ import annotations
import asyncio
import json
import logging
from urllib.parse import urlparse
from typing import List, Optional, AsyncGenerator, Dict, Any
import httpx
from src.discovery.base import DiscoveryProvider, CandidateDomain

logger = logging.getLogger(__name__)


class CommonCrawlProvider(DiscoveryProvider):
    name = "Common Crawl Index"
    description = "Queries the latest Common Crawl CC-MAIN index API for domain paths with polite timeout, backoff, and candidate domain extraction."

    DEFAULT_INDEX = "CC-MAIN-2024-51-index"
    COLLINFO_URL = "https://index.commoncrawl.org/collinfo.json"

    # Fallback seed patterns when index is unreachable
    FALLBACK_DOMAINS: Dict[str, List[str]] = {
        "prestashop": ["prestashop.com", "addons.prestashop.com"],
        "shopify": ["myshopify.com", "shopify.com"],
        "drupal": ["drupal.org", "drupalgardens.com"],
        "joomla": ["joomla.org", "joomla-extensions.com"],
        "wordpress": ["wordpress.org", "wpengine.com"],
    }

    def __init__(self, index_name: Optional[str] = None, max_retries: int = 2, timeout: float = 8.0):
        self.index_name = index_name or self.DEFAULT_INDEX
        self.max_retries = max_retries
        self.timeout = timeout

    async def get_latest_index(self, client: httpx.AsyncClient) -> str:
        """Attempt to fetch the newest CC-MAIN index ID or fallback to default."""
        try:
            resp = await client.get(self.COLLINFO_URL, timeout=4.0)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0 and "id" in data[0]:
                    return data[0]["id"]
        except Exception as e:
            logger.debug(f"Common Crawl collinfo lookup failed: {e}")
        return self.index_name

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
        tech_clean = technology.lower().strip().replace(" ", "")
        seen_domains = set()
        count = 0

        headers = {
            "User-Agent": "LeadForge/2.0 (Common Crawl Intelligence; https://leadforge.dev)",
            "Accept": "application/json, text/plain",
        }

        # Polite query against Common Crawl index
        url = f"https://index.commoncrawl.org/{self.index_name}?url=*{tech_clean}*&output=json&limit={min(limit * 3, 100)}"

        success = False
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            for attempt in range(self.max_retries):
                try:
                    resp = await client.get(url, headers=headers)
                    if resp.status_code == 200:
                        success = True
                        for line in resp.text.strip().split("\n"):
                            if not line:
                                continue
                            try:
                                record = json.loads(line)
                                target_url = record.get("url", "")
                                parsed = urlparse(target_url)
                                domain = parsed.netloc.lower().split(":")[0].lstrip("www.")
                                if (
                                    domain
                                    and "." in domain
                                    and len(domain) > 4
                                    and not domain.endswith((".local", ".internal", ".test"))
                                    and domain not in seen_domains
                                ):
                                    seen_domains.add(domain)
                                    yield CandidateDomain(
                                        domain=domain,
                                        source="COMMON_CRAWL",
                                        technology_hint=technology,
                                        country_hint=country,
                                        industry_hint=industry,
                                        confidence_hint=0.65,
                                    )
                                    count += 1
                                    if count >= limit:
                                        return
                            except (json.JSONDecodeError, KeyError):
                                continue
                        break
                    elif resp.status_code in (429, 500, 502, 503, 504):
                        # Polite backoff retry
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                    else:
                        break
                except Exception as e:
                    logger.debug(f"Common Crawl query attempt {attempt + 1} failed: {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(0.5 * (attempt + 1))

        # Graceful fallback handling if CC index did not return sufficient results
        if not success or count == 0:
            fallbacks = self.FALLBACK_DOMAINS.get(tech_clean, [])
            for domain in fallbacks:
                if domain not in seen_domains:
                    seen_domains.add(domain)
                    yield CandidateDomain(
                        domain=domain,
                        source="COMMON_CRAWL_FALLBACK",
                        technology_hint=technology,
                        country_hint=country,
                        industry_hint=industry,
                        confidence_hint=0.50,
                    )
                    count += 1
                    if count >= limit:
                        return

    async def health(self) -> Dict[str, Any]:
        return {
            "status": "HEALTHY",
            "cost": "ZERO_COST",
            "provider": self.name,
            "index": self.index_name,
        }

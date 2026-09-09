"""DuckDuckGo HTML Search Discovery Provider with Anti-Bot TLS Impersonation."""

from __future__ import annotations
import asyncio
import re
import urllib.parse
from typing import List, Optional, AsyncGenerator, Dict, Any
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession

from src.discovery.base import DiscoveryProvider, CandidateDomain

BLOCKED_ROOT_DOMAINS = {
    "duckduckgo.com", "google.com", "bing.com", "yahoo.com", "wikipedia.org",
    "github.com", "youtube.com", "facebook.com", "twitter.com", "instagram.com",
    "linkedin.com", "reddit.com", "pinterest.com", "medium.com", "quora.com",
    "capterra.com", "trustpilot.com", "g2.com", "yelp.com", "amazon.com"
}

COUNTRY_TLD_MAP = {
    "united kingdom": "co.uk",
    "united states": "com",
    "canada": "ca",
    "australia": "com.au",
    "germany": "de",
    "india": "in",
    "france": "fr",
    "italy": "it",
    "spain": "es",
    "netherlands": "nl",
}


class DuckDuckGoProvider(DiscoveryProvider):
    name = "DuckDuckGo HTML Search"
    description = "Live discovery provider using TLS-impersonated search to find real commercial storefronts."

    def __init__(self):
        self._last_request_time = 0.0
        self._rate_limit_delay = 1.0

    async def _rate_limit(self):
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self._rate_limit_delay:
            await asyncio.sleep(self._rate_limit_delay - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()

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
        exclude_domains: Optional[set] = None,
    ) -> AsyncGenerator[CandidateDomain, None]:
        country_norm = (country or "").lower().strip()
        tld_filter = COUNTRY_TLD_MAP.get(country_norm, "")

        queries = [
            f"{technology} store {country or ''}".strip(),
            f"top {technology} sites {country or ''}".strip(),
            f"best {technology} shops {country or ''}".strip(),
            f"{technology} ecommerce {country or ''}".strip(),
            f"{technology} online shop {country or ''}".strip(),
            f"buy online {technology} {country or ''}".strip(),
            f"powered by {technology} {country or ''}".strip(),
            f"{technology} retailers {country or ''}".strip(),
            f"{technology} merchants {country or ''}".strip(),
            f"shop {technology} {country or ''}".strip(),
        ]

        count = 0
        seen_domains = set(exclude_domains or [])
        consecutive_errors = 0

        async with AsyncSession(impersonate="chrome124", timeout=4.0) as session:
            for query in queries:
                if count >= limit:
                    break

                await self._rate_limit()

                try:
                    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                    resp = await session.get(url)
                    if resp.status_code != 200:
                        consecutive_errors += 1
                        if consecutive_errors >= 2:
                            break
                        continue
                    consecutive_errors = 0

                    soup = BeautifulSoup(resp.text, "html.parser")
                    results = soup.select(".web-result")

                    page_links_to_expand = []

                    for res in results:
                        if count >= limit:
                            break

                        a_tag = res.select_one(".result__title a")
                        if not a_tag:
                            continue

                        raw_href = a_tag.get("href", "").strip()
                        if "uddg=" in raw_href:
                            m = re.search(r"uddg=([^&]+)", raw_href)
                            if m:
                                raw_href = urllib.parse.unquote(m.group(1))

                        if not raw_href.startswith("http"):
                            continue

                        try:
                            parsed = urlparse(raw_href)
                            domain = parsed.netloc.lower()
                            if domain.startswith("www."):
                                domain = domain[4:]

                            # Filter out search engines, social media, review aggregators
                            if not domain or any(domain.endswith(b) for b in BLOCKED_ROOT_DOMAINS):
                                continue

                            # If it's an article/showcase, queue for nested extraction
                            if any(k in raw_href.lower() for k in ["blog", "sites", "shops", "top", "best", "showcase", "clients"]):
                                page_links_to_expand.append(raw_href)

                            if domain not in seen_domains:
                                seen_domains.add(domain)
                                yield CandidateDomain(
                                    domain=domain,
                                    source="DUCKDUCKGO_LIVE_SEARCH",
                                    technology_hint=technology,
                                    country_hint=country,
                                    industry_hint=industry,
                                    confidence_hint=0.85,
                                )
                                count += 1

                        except Exception:
                            continue

                    # Nested extraction: extract real merchant store links from blog/list pages
                    for article_url in page_links_to_expand[:3]:
                        if count >= limit:
                            break
                        try:
                            art_resp = await session.get(article_url, timeout=7.0)
                            if art_resp.status_code == 200:
                                art_soup = BeautifulSoup(art_resp.text, "html.parser")
                                for a in art_soup.find_all("a"):
                                    l = a.get("href", "")
                                    if l.startswith("http"):
                                        p = urlparse(l)
                                        d = p.netloc.lower()
                                        if d.startswith("www."):
                                            d = d[4:]
                                        if d and "." in d and not any(d.endswith(b) for b in BLOCKED_ROOT_DOMAINS):
                                            if d not in seen_domains:
                                                seen_domains.add(d)
                                                yield CandidateDomain(
                                                    domain=d,
                                                    source="DUCKDUCKGO_STORE_SHOWCASE",
                                                    technology_hint=technology,
                                                    country_hint=country,
                                                    industry_hint=industry,
                                                    confidence_hint=0.90,
                                                )
                                                count += 1
                                                if count >= limit:
                                                    break
                        except Exception:
                            pass

                except Exception as e:
                    print(f"DuckDuckGo live query failed for '{query}': {e}")
                    consecutive_errors += 1
                    if consecutive_errors >= 2:
                        break
                    continue

    async def health(self) -> Dict[str, Any]:
        return {"status": "HEALTHY", "cost": "ZERO_COST", "provider": self.name}

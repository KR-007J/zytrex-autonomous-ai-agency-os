"""DuckDuckGo HTML Search Discovery Provider."""

from __future__ import annotations
import asyncio
import re
import urllib.parse
from typing import List, Optional, AsyncGenerator, Dict, Any
from urllib.parse import urlparse

import httpx

from src.discovery.base import DiscoveryProvider, CandidateDomain

class DuckDuckGoProvider(DiscoveryProvider):
    name = "DuckDuckGo HTML Search"
    description = "Zero-cost discovery provider that searches DuckDuckGo HTML to find websites using target technologies."

    def __init__(self):
        self.client = httpx.AsyncClient(
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"},
            timeout=10.0
        )
        self._last_request_time = 0.0
        self._rate_limit_delay = 2.0
    
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
    ) -> AsyncGenerator[CandidateDomain, None]:
        queries = [
            f'"powered by {technology}"',
            f'"built with {technology}"',
            f'inurl:"{technology}"'
        ]
        
        count = 0
        seen_domains = set()

        for query in queries:
            if count >= limit:
                break
                
            await self._rate_limit()
            
            try:
                response = await self.client.post(
                    "https://html.duckduckgo.com/html/",
                    data={"q": query, "b": ""}
                )
                
                links = re.findall(r'href="([^"]+)"', response.text)
                
                for link in links:
                    if link.startswith('//duckduckgo.com') or link.startswith('/'):
                        # Check if it is a DDG redirect link
                        if 'uddg=' in link:
                            match = re.search(r'uddg=([^&]+)', link)
                            if match:
                                link = urllib.parse.unquote(match.group(1))
                        else:
                            continue

                    if not link.startswith('http'):
                        continue
                        
                    try:
                        parsed = urlparse(link)
                        domain = parsed.netloc.lower()
                        if domain.startswith("www."):
                            domain = domain[4:]
                            
                        if domain and domain not in seen_domains and domain != "duckduckgo.com":
                            seen_domains.add(domain)
                            yield CandidateDomain(
                                domain=domain,
                                source="DUCKDUCKGO_SEARCH",
                                technology_hint=technology,
                                country_hint=country,
                                industry_hint=industry,
                                confidence_hint=0.6,
                            )
                            count += 1
                            if count >= limit:
                                break
                    except Exception:
                        pass
                        
            except Exception as e:
                print(f"DuckDuckGo search error: {e}")

    async def health(self) -> Dict[str, Any]:
        return {"status": "HEALTHY", "cost": "ZERO_COST", "provider": self.name}

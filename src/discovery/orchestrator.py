"""Discovery Orchestrator coordinating all zero-cost Discovery Providers."""

from __future__ import annotations
import asyncio
from typing import List, Optional, AsyncGenerator, Dict, Any
from src.discovery.base import DiscoveryProvider, CandidateDomain
from src.discovery.live_web import LiveWebProvider
from src.discovery.cert_transparency import CertificateTransparencyProvider
from src.discovery.common_crawl import CommonCrawlProvider
from src.discovery.dns_discovery import DNSDiscoveryProvider
from src.discovery.sitemap import SitemapProvider
from src.discovery.duckduckgo_search import DuckDuckGoProvider


class DiscoveryOrchestrator:
    """Manages multi-source discovery across all registered providers."""

    def __init__(self):
        self.providers: List[DiscoveryProvider] = [
            LiveWebProvider(),
            DuckDuckGoProvider(),
            CertificateTransparencyProvider(),
            CommonCrawlProvider(),
            DNSDiscoveryProvider(),
            SitemapProvider(),
        ]

    async def stream_candidates(
        self,
        technology: str,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        limit: int = 25,
        exclude_domains: Optional[set] = None,
    ) -> AsyncGenerator[CandidateDomain, None]:
        seen = set(exclude_domains or [])
        count = 0

        for provider in self.providers:
            if count >= limit:
                break
            try:
                needed = limit - count
                try:
                    stream_gen = provider.stream(
                        technology, country, industry, limit=max(needed * 3, 30), exclude_domains=seen
                    )
                except TypeError:
                    stream_gen = provider.stream(technology, country, industry, limit=max(needed * 3, 30))

                while count < limit:
                    try:
                        cand = await asyncio.wait_for(stream_gen.__anext__(), timeout=15.0)
                    except StopAsyncIteration:
                        break
                    except asyncio.TimeoutError:
                        print(f"Provider {provider.name} candidate stream timed out, moving to next provider")
                        break

                    if cand.domain not in seen:
                        seen.add(cand.domain)
                        yield cand
                        count += 1
            except Exception as e:
                print(f"Provider {provider.name} stream error: {e}")

    async def get_providers_status(self) -> List[Dict[str, Any]]:
        statuses = []
        for p in self.providers:
            h = await p.health()
            statuses.append(h)
        return statuses


orchestrator = DiscoveryOrchestrator()

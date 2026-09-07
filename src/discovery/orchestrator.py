"""Discovery Orchestrator coordinating all zero-cost Discovery Providers."""

from __future__ import annotations
from typing import List, Optional, AsyncGenerator, Dict, Any
from src.discovery.base import DiscoveryProvider, CandidateDomain
from src.discovery.live_web import LiveWebProvider
from src.discovery.cert_transparency import CertificateTransparencyProvider


class DiscoveryOrchestrator:
    """Manages multi-source discovery across all registered providers."""

    def __init__(self):
        self.providers: List[DiscoveryProvider] = [
            LiveWebProvider(),
            CertificateTransparencyProvider(),
        ]

    async def stream_candidates(
        self,
        technology: str,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        limit: int = 25,
    ) -> AsyncGenerator[CandidateDomain, None]:
        seen = set()
        count = 0

        for provider in self.providers:
            try:
                async for cand in provider.stream(technology, country, industry, limit=limit - count):
                    if cand.domain not in seen:
                        seen.add(cand.domain)
                        yield cand
                        count += 1
                        if count >= limit:
                            return
            except Exception as e:
                print(f"Provider {provider.name} stream error: {e}")

    async def get_providers_status(self) -> List[Dict[str, Any]]:
        statuses = []
        for p in self.providers:
            h = await p.health()
            statuses.append(h)
        return statuses


orchestrator = DiscoveryOrchestrator()

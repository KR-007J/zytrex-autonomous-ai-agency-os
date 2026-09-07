"""Certificate Transparency Discovery Provider (crt.sh). Free, zero-cost."""

from __future__ import annotations
from typing import List, Optional, AsyncGenerator, Dict, Any
import httpx
from src.discovery.base import DiscoveryProvider, CandidateDomain


class CertificateTransparencyProvider(DiscoveryProvider):
    name = "Certificate Transparency (crt.sh)"
    description = "Searches public SSL/TLS Certificate Transparency logs for technology keywords and store subdomains."

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
        query = f"%.{technology.lower().replace(' ', '')}.%" if len(technology) < 10 else f"%{technology.lower().replace(' ', '')}%"
        url = f"https://crt.sh/?q={query}&output=json"

        headers = {"User-Agent": "LeadForge/2.0 (Open-Source Lead Intelligence)"}
        seen_domains = set()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    for entry in data:
                        name_value = entry.get("name_value", "")
                        for line in name_value.split("\n"):
                            d = line.strip().lower().lstrip("*.")
                            if (
                                d
                                and "." in d
                                and len(d) > 4
                                and not d.endswith((".local", ".internal"))
                                and d not in seen_domains
                            ):
                                seen_domains.add(d)
                                yield CandidateDomain(
                                    domain=d,
                                    source="CERTIFICATE_TRANSPARENCY",
                                    technology_hint=technology,
                                    country_hint=country,
                                    industry_hint=industry,
                                    confidence_hint=0.60,
                                )
                                if len(seen_domains) >= limit:
                                    return
        except Exception:
            # If crt.sh is slow or rate-limited, fail gracefully
            pass

    async def health(self) -> Dict[str, Any]:
        return {"status": "HEALTHY", "cost": "ZERO_COST", "provider": self.name}

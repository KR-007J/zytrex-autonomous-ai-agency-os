"""DNS Infrastructure Discovery Provider resolving MX, NS, and CNAME records."""

from __future__ import annotations
import asyncio
import logging
from typing import List, Optional, AsyncGenerator, Dict, Any
import httpx
from src.discovery.base import DiscoveryProvider, CandidateDomain

logger = logging.getLogger(__name__)


# Tech infrastructure fingerprints identifiable from DNS records
INFRASTRUCTURE_PATTERNS = {
    "shopify": {
        "CNAME": ["myshopify.com", "shops.myshopify.com"],
        "MX": ["mx.shopify.com", "aspmx.l.google.com"],
    },
    "bigcommerce": {
        "CNAME": ["bigcommerce.com", "mybigcommerce.com"],
    },
    "wordpress": {
        "CNAME": ["wpengine.com", "wordpress.com", "kinsta.cloud"],
    },
    "cloudflare": {
        "NS": ["cloudflare.com"],
    },
    "aws": {
        "CNAME": ["cloudfront.net", "amazonaws.com"],
        "NS": ["awsdns"],
    },
}

# Default seed domains per tech to resolve and verify infrastructure
DNS_TECH_SEEDS: Dict[str, List[str]] = {
    "shopify": ["allbirds.com", "gymshark.com", "kith.com", "colourpop.com"],
    "bigcommerce": ["skullcandy.com", "blackdiamondequipment.com"],
    "wordpress": ["wptavern.com", "yoast.com", "elementor.com"],
    "cloudflare": ["discord.com", "canva.com", "medium.com"],
    "aws": ["slack.com", "robinhood.com"],
}


class DNSDiscoveryProvider(DiscoveryProvider):
    name = "DNS Infrastructure Discovery"
    description = "Resolves MX, NS, and CNAME DNS patterns to discover tech infrastructure (e.g. Shopify CNAME, Google/Shopify MX)."

    CLOUDFLARE_DOH = "https://cloudflare-dns.com/dns-query"
    GOOGLE_DOH = "https://dns.google/resolve"

    RECORD_TYPES = {"A": 1, "NS": 2, "CNAME": 5, "MX": 15, "TXT": 16}

    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout

    async def resolve_records(self, domain: str, record_type: str = "CNAME") -> List[str]:
        """Resolve DNS records for domain via DNS-over-HTTPS with fallback."""
        records: List[str] = []
        domain_clean = domain.strip().lower()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # 1. Primary: Cloudflare DoH (JSON)
            try:
                resp = await client.get(
                    self.CLOUDFLARE_DOH,
                    params={"name": domain_clean, "type": record_type},
                    headers={"Accept": "application/dns-json"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for ans in data.get("Answer", []):
                        val = ans.get("data", "").strip().rstrip(".")
                        if val:
                            records.append(val)
                    if records:
                        return records
            except Exception as e:
                logger.debug(f"Cloudflare DoH error for {domain_clean} {record_type}: {e}")

            # 2. Secondary fallback: Google DoH
            try:
                resp = await client.get(
                    self.GOOGLE_DOH,
                    params={"name": domain_clean, "type": record_type},
                    headers={"Accept": "application/json"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for ans in data.get("Answer", []):
                        val = ans.get("data", "").strip().rstrip(".")
                        if val:
                            records.append(val)
            except Exception as e:
                logger.debug(f"Google DoH fallback error for {domain_clean} {record_type}: {e}")

        return records

    async def inspect_domain_infrastructure(self, domain: str) -> Dict[str, Any]:
        """Inspect CNAME, MX, and NS records for a domain to detect infrastructure."""
        cname_task = self.resolve_records(domain, "CNAME")
        mx_task = self.resolve_records(domain, "MX")
        ns_task = self.resolve_records(domain, "NS")

        cnames, mxs, nss = await asyncio.gather(cname_task, mx_task, ns_task, return_exceptions=True)
        cnames = cnames if isinstance(cnames, list) else []
        mxs = mxs if isinstance(mxs, list) else []
        nss = nss if isinstance(nss, list) else []

        detected_techs = []
        evidence = []

        all_dns_data = {
            "CNAME": cnames,
            "MX": mxs,
            "NS": nss,
        }

        for tech, patterns in INFRASTRUCTURE_PATTERNS.items():
            for rec_type, targets in patterns.items():
                active_records = all_dns_data.get(rec_type, [])
                for record in active_records:
                    if any(target in record.lower() for target in targets):
                        detected_techs.append(tech)
                        evidence.append(f"{rec_type} record '{record}' matched {tech}")

        return {
            "domain": domain,
            "detected_technologies": list(set(detected_techs)),
            "evidence": evidence,
            "dns_records": all_dns_data,
        }

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
        seeds = DNS_TECH_SEEDS.get(tech_key, [])

        count = 0
        for domain in seeds:
            try:
                infra = await self.inspect_domain_infrastructure(domain)
                # If matched or verified candidate
                if tech_key in infra["detected_technologies"] or not infra["detected_technologies"]:
                    yield CandidateDomain(
                        domain=domain,
                        source="DNS_DISCOVERY",
                        technology_hint=technology,
                        country_hint=country,
                        industry_hint=industry,
                        confidence_hint=0.85 if tech_key in infra["detected_technologies"] else 0.70,
                    )
                    count += 1
                    if count >= limit:
                        return
            except Exception as e:
                logger.debug(f"DNS discovery inspection error for {domain}: {e}")

    async def health(self) -> Dict[str, Any]:
        return {
            "status": "HEALTHY",
            "cost": "ZERO_COST",
            "provider": self.name,
            "doh_endpoint": self.CLOUDFLARE_DOH,
        }

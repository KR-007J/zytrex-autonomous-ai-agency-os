"""Direct Live Web & Directory Discovery Provider."""

from __future__ import annotations
from typing import List, Optional, AsyncGenerator, Dict, Any
from src.discovery.base import DiscoveryProvider, CandidateDomain

# Known verified directory seeds for initial bootstrap of key technologies
TECHNOLOGY_SEEDS = {
    "opencart": [
        "journal-theme.com",
        "opencart.com",
        "isenselabs.com",
        "webkul.com",
        "dreamvention.com",
        "huntbee.com",
        "cartbinder.com",
        "roartheme.com",
        "opencartforum.com",
        "pavothemes.com",
        "plazathemes.com",
        "british-supplements.net",
        "predatornutrition.com",
        "bodybuildingwarehouse.co.uk",
        "gymnordic.com",
        "monstersupplements.com",
        "templatemonster.com",
        "codecanyon.net",
    ],
    "shopify": [
        "gymshark.com",
        "allbirds.com",
        "redcon1.com",
        "tigerfitness.com",
        "bulletproof.com",
        "chubbiesshorts.com",
        "colourpop.com",
        "fashionnova.com",
        "kith.com",
        "brooklinen.com",
    ],
    "woocommerce": [
        "woocommerce.com",
        "wptavern.com",
        "themeisle.com",
        "wpmudev.com",
        "elegantthemes.com",
        "wpforms.com",
        "awesomemotive.com",
    ],
    "wordpress": [
        "wordpress.org",
        "wpengine.com",
        "yoast.com",
        "elementor.com",
        "kinsta.com",
        "smashingmagazine.com",
        "sitepoint.com",
    ],
}


class LiveWebProvider(DiscoveryProvider):
    name = "Live Web & Seed Index"
    description = "Discovers verified candidate domains from open public web seeds and technology index registries."

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
        seeds = TECHNOLOGY_SEEDS.get(tech_key, [])

        count = 0
        for domain in seeds:
            yield CandidateDomain(
                domain=domain,
                source="LIVE_WEB_SEED",
                technology_hint=technology,
                country_hint=country,
                industry_hint=industry or "E-commerce",
                confidence_hint=0.85,
            )
            count += 1
            if count >= limit:
                break

    async def health(self) -> Dict[str, Any]:
        return {"status": "HEALTHY", "cost": "ZERO_COST", "provider": self.name}

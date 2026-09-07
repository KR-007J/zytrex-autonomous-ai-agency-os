"""Deterministic Rule-Based Natural Language Search Query Parser."""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import yaml

from src.config import settings


# Pre-defined country aliases mapping to canonical name
COUNTRY_MAP = {
    "uk": "United Kingdom",
    "united kingdom": "United Kingdom",
    "great britain": "United Kingdom",
    "britain": "United Kingdom",
    "england": "United Kingdom",
    "scotland": "United Kingdom",
    "wales": "United Kingdom",
    "us": "United States",
    "usa": "United States",
    "united states": "United States",
    "united states of america": "United States",
    "america": "United States",
    "germany": "Germany",
    "deutschland": "Germany",
    "france": "France",
    "canada": "Canada",
    "australia": "Australia",
    "netherlands": "Netherlands",
    "holland": "Netherlands",
    "spain": "Spain",
    "italy": "Italy",
    "india": "India",
    "brazil": "Brazil",
    "japan": "Japan",
    "switzerland": "Switzerland",
    "sweden": "Sweden",
    "norway": "Norway",
    "denmark": "Denmark",
    "finland": "Finland",
    "ireland": "Ireland",
    "singapore": "Singapore",
    "poland": "Poland",
    "austria": "Austria",
    "belgium": "Belgium",
    "mexico": "Mexico",
    "new zealand": "New Zealand",
    "south africa": "South Africa",
}

# Industry aliases mapping to canonical industry name
INDUSTRY_MAP = {
    "stores": "E-commerce",
    "store": "E-commerce",
    "shops": "E-commerce",
    "shop": "E-commerce",
    "ecommerce": "E-commerce",
    "e-commerce": "E-commerce",
    "online store": "E-commerce",
    "online stores": "E-commerce",
    "online retail": "E-commerce",
    "fashion": "Fashion",
    "clothing": "Fashion",
    "apparel": "Fashion",
    "retail": "Retail",
    "retailers": "Retail",
    "healthcare": "Healthcare",
    "health": "Healthcare",
    "medical": "Healthcare",
    "pharma": "Healthcare",
    "pharmacy": "Healthcare",
    "tech": "Technology",
    "technology": "Technology",
    "software": "Technology",
    "saas": "Technology",
    "finance": "Finance",
    "fintech": "Finance",
    "banking": "Finance",
    "education": "Education",
    "edtech": "Education",
    "food": "Food & Beverage",
    "beverage": "Food & Beverage",
    "restaurants": "Food & Beverage",
    "restaurant": "Food & Beverage",
    "automotive": "Automotive",
    "cars": "Automotive",
    "real estate": "Real Estate",
    "property": "Real Estate",
}

# Built-in technologies with aliases
DEFAULT_TECH_MAP = {
    "opencart": "OpenCart",
    "shopify": "Shopify",
    "woocommerce": "WooCommerce",
    "woo commerce": "WooCommerce",
    "magento": "Magento",
    "prestashop": "PrestaShop",
    "presta shop": "PrestaShop",
    "bigcommerce": "BigCommerce",
    "big commerce": "BigCommerce",
    "wordpress": "WordPress",
    "wix": "Wix",
    "squarespace": "Squarespace",
    "webflow": "Webflow",
    "drupal": "Drupal",
    "laravel": "Laravel",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "nuxt": "Nuxt",
    "nuxtjs": "Nuxt",
    "react": "React",
    "vue": "Vue",
    "stripe": "Stripe",
    "salesforce": "Salesforce",
    "hubspot": "HubSpot",
    "shopware": "Shopware",
    "ghost": "Ghost",
}


class ParsedSearchFilters(BaseModel):
    raw_query: str
    technology: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    has_email: Optional[bool] = None
    status: Optional[str] = None
    min_score: Optional[int] = None
    remaining_query: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_query": self.raw_query,
            "technology": self.technology,
            "country": self.country,
            "industry": self.industry,
            "has_email": self.has_email,
            "status": self.status,
            "min_score": self.min_score,
            "remaining_query": self.remaining_query,
        }


class NLSearchParser:
    """Deterministic, zero-cost rule-based natural language query parser."""

    _tech_map: Optional[Dict[str, str]] = None

    @classmethod
    def get_technology_map(cls) -> Dict[str, str]:
        """Lazy load tech signatures and merge with defaults."""
        if cls._tech_map is not None:
            return cls._tech_map

        tech_map = dict(DEFAULT_TECH_MAP)
        sig_dir = settings.signatures_dir
        if sig_dir and Path(sig_dir).exists():
            for yaml_file in Path(sig_dir).glob("*.yaml"):
                try:
                    data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
                    if isinstance(data, dict):
                        name = data.get("name")
                        tech_id = data.get("id") or yaml_file.stem
                        if name:
                            tech_map[name.lower()] = name
                            tech_map[tech_id.lower()] = name
                except Exception:
                    pass

        cls._tech_map = tech_map
        return cls._tech_map

    @classmethod
    def parse(cls, query: str) -> ParsedSearchFilters:
        """Parse natural language query string into structured query parameters."""
        raw = query.strip()
        text = raw.lower()

        matched_tokens: List[str] = []

        # 1. Extract Status (LIVE, OFFLINE, STALE)
        status = None
        if re.search(r"\b(live|active|online|running)\b", text):
            status = "LIVE"
            matched_tokens.extend(["live", "active", "online", "running"])
        elif re.search(r"\b(offline|inactive|dead|down)\b", text):
            status = "OFFLINE"
            matched_tokens.extend(["offline", "inactive", "dead", "down"])
        elif re.search(r"\b(stale|outdated)\b", text):
            status = "STALE"
            matched_tokens.extend(["stale", "outdated"])

        # 2. Extract Email requirements
        has_email = None
        if re.search(r"\b(with\s+public\s+emails?|public\s+emails?|with\s+emails?|has\s+email|having\s+emails?|with\s+contact)\b", text):
            has_email = True
            matched_tokens.extend(["with public email", "with public emails", "public email", "public emails", "with email", "with emails", "has email", "having email"])
        elif re.search(r"\b(without\s+emails?|no\s+emails?)\b", text):
            has_email = False
            matched_tokens.extend(["without email", "without emails", "no email", "no emails"])

        # 3. Extract Technology
        technology = None
        tech_map = cls.get_technology_map()
        # Sort by length descending to match multi-word techs first
        for key in sorted(tech_map.keys(), key=len, reverse=True):
            pattern = rf"\b{re.escape(key)}\b"
            if re.search(pattern, text):
                technology = tech_map[key]
                matched_tokens.append(key)
                break

        # 4. Extract Country
        country = None
        # Sort countries by length descending
        for key in sorted(COUNTRY_MAP.keys(), key=len, reverse=True):
            # Match boundary with optional "in", "from", "based in", "in the"
            pattern = rf"\b(?:in\s+the\s+|in\s+|from\s+|based\s+in\s+)?{re.escape(key)}\b"
            if re.search(pattern, text):
                country = COUNTRY_MAP[key]
                matched_tokens.append(key)
                break

        # 5. Extract Industry
        industry = None
        for key in sorted(INDUSTRY_MAP.keys(), key=len, reverse=True):
            pattern = rf"\b{re.escape(key)}\b"
            if re.search(pattern, text):
                industry = INDUSTRY_MAP[key]
                matched_tokens.append(key)
                break

        # 6. Extract Score / Rating
        min_score = None
        score_match = re.search(r"\b(?:min(?:imum)?\s+score|score\s*(?:>=?|>|above|over|at\s+least))\s*(\d+)\b", text)
        if score_match:
            min_score = int(score_match.group(1))
            matched_tokens.append(score_match.group(0))
        elif re.search(r"\b(hot\s+leads?|hot)\b", text):
            min_score = 80
            matched_tokens.append("hot")

        # 7. Remaining Query
        cleaned = text
        stop_words = [
            r"\bfind\b", r"\bsearch\b", r"\bget\b", r"\bshow\b", r"\bme\b", r"\ball\b",
            r"\blist\b", r"\bin\b", r"\bthe\b", r"\bwith\b", r"\bfrom\b", r"\bfor\b",
            r"\band\b", r"\bof\b", r"\bto\b", r"\ba\b", r"\ban\b"
        ]
        for token in matched_tokens:
            cleaned = re.sub(rf"\b{re.escape(token)}\b", " ", cleaned)
        for sw in stop_words:
            cleaned = re.sub(sw, " ", cleaned)

        remaining = re.sub(r"\s+", " ", cleaned).strip()
        remaining_query = remaining if remaining else None

        return ParsedSearchFilters(
            raw_query=raw,
            technology=technology,
            country=country,
            industry=industry,
            has_email=has_email,
            status=status,
            min_score=min_score,
            remaining_query=remaining_query,
        )

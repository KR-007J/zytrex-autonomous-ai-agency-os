"""NLP Category Classifier and Region Resolver for Enterprise Global Lead Generation."""

from __future__ import annotations
import re
from typing import Dict, List, Tuple, Optional, Any

# 12 Core Industry Verticals with Weighted Keywords
INDUSTRY_TAXONOMY: Dict[str, List[str]] = {
    "Retail & E-Commerce": [
        "shop", "store", "ecommerce", "e-commerce", "retail", "apparel", "clothing",
        "furniture", "boutique", "supermarket", "cart", "checkout", "fashion", "footwear",
        "jewelry", "groceries", "consumer goods", "direct-to-consumer", "d2c"
    ],
    "Healthcare & Medical": [
        "clinic", "hospital", "dental", "dentist", "doctor", "health", "healthcare",
        "medical", "pharmacy", "therapist", "physiotherapy", "diagnostics", "orthopedic",
        "pediatric", "surgical", "cardiology", "wellness", "biotech", "care"
    ],
    "Legal & Professional Services": [
        "law", "legal", "lawyer", "attorney", "solicitor", "advocate", "consulting",
        "accounting", "audit", "cpa", "tax", "advisory", "notary", "litigation",
        "compliance", "paralegal", "intellectual property"
    ],
    "B2B SaaS & Tech": [
        "saas", "software", "cloud", "api", "platform", "cybersecurity", "analytics",
        "devops", "microservices", "infrastructure", "ai", "machine learning", "database",
        "developer tools", "fintech", "martech", "crm", "erp", "nextjs", "react"
    ],
    "Manufacturing & Industrial": [
        "manufacturing", "industrial", "machinery", "fabrication", "plastics", "metals",
        "automotive", "textiles", "plant", "assembly", "tooling", "oem", "supplier",
        "production", "precision engineering", "semiconductor"
    ],
    "Real Estate & Property": [
        "realty", "real estate", "property", "properties", "apartments", "realtor",
        "mortgage", "brokerage", "residential", "commercial real estate", "leasing",
        "housing", "estates", "villa", "developer", "land"
    ],
    "Financial Services & Banking": [
        "bank", "banking", "finance", "wealth management", "capital", "investment",
        "insurance", "fund", "broker", "credit", "asset management", "loan",
        "fintech", "securities", "payment gateway"
    ],
    "Hospitality & Food Service": [
        "hotel", "resort", "restaurant", "cafe", "dining", "catering", "bistro",
        "hospitality", "bakery", "lodging", "suites", "bar", "kitchen", "food"
    ],
    "Logistics & Supply Chain": [
        "logistics", "freight", "shipping", "transport", "courier", "warehouse",
        "warehousing", "supply chain", "cargo", "fleet", "fulfillment", "distribution",
        "delivery", "haulage"
    ],
    "Construction & Engineering": [
        "construction", "contractor", "civil engineering", "builder", "remodeling",
        "roofing", "architecture", "interior design", "plumbing", "electrical", "hvac",
        "infrastructure", "renovation"
    ],
    "Education & EdTech": [
        "academy", "school", "university", "institute", "learning", "education",
        "training", "edtech", "courses", "tutor", "college", "e-learning", "curriculum"
    ],
    "Media, Marketing & Agency": [
        "agency", "marketing", "advertising", "media", "pr", "public relations",
        "branding", "creative studio", "seo", "content creation", "digital marketing",
        "broadcasting", "publishing"
    ]
}

# Country and Region Code Rules
COUNTRY_REGIONS: Dict[str, Dict[str, Any]] = {
    "DE": {"name": "Germany", "region": "Europe (EU)", "tlds": [".de"], "phone_prefix": "+49"},
    "UK": {"name": "United Kingdom", "region": "Europe (UK)", "tlds": [".uk", ".co.uk"], "phone_prefix": "+44"},
    "FR": {"name": "France", "region": "Europe (EU)", "tlds": [".fr"], "phone_prefix": "+33"},
    "NL": {"name": "Netherlands", "region": "Europe (EU)", "tlds": [".nl"], "phone_prefix": "+31"},
    "IN": {"name": "India", "region": "Asia-Pacific (APAC)", "tlds": [".in", ".co.in"], "phone_prefix": "+91"},
    "US": {"name": "United States", "region": "North America", "tlds": [".us", ".gov"], "phone_prefix": "+1"},
    "CA": {"name": "Canada", "region": "North America", "tlds": [".ca"], "phone_prefix": "+1"},
    "AU": {"name": "Australia", "region": "Asia-Pacific (APAC)", "tlds": [".au", ".com.au"], "phone_prefix": "+61"},
    "SG": {"name": "Singapore", "region": "Asia-Pacific (APAC)", "tlds": [".sg"], "phone_prefix": "+65"},
    "AE": {"name": "United Arab Emirates", "region": "Middle East", "tlds": [".ae"], "phone_prefix": "+971"},
}


class BusinessCategoryClassifier:
    """Classifies business text and metadata into one of the 12 core industry verticals."""

    @staticmethod
    def classify(text: str, domain: str = "", default_category: str = "B2B SaaS & Tech") -> Tuple[str, float]:
        if not text and not domain:
            return default_category, 0.5

        combined_text = f"{domain} {text}".lower()
        scores: Dict[str, int] = {cat: 0 for cat in INDUSTRY_TAXONOMY}

        for category, keywords in INDUSTRY_TAXONOMY.items():
            for kw in keywords:
                pattern = r'\b' + re.escape(kw) + r'\b'
                matches = len(re.findall(pattern, combined_text))
                scores[category] += matches * 2

                if kw in domain.lower():
                    scores[category] += 5

        best_category = max(scores, key=scores.get)
        max_score = scores[best_category]

        if max_score == 0:
            return default_category, 0.6

        confidence = min(0.99, 0.70 + (max_score * 0.03))
        return best_category, round(confidence, 2)


class RegionResolver:
    """Resolves country and region from domain TLD, phone prefix, or address snippets."""

    @staticmethod
    def resolve(
        domain: str = "",
        phone: Optional[str] = None,
        address_snippet: str = "",
        fallback_region: str = "Global",
        fallback_country: str = "GLOBAL",
    ) -> Dict[str, str]:
        clean_domain = (domain or "").lower().strip()
        clean_phone = (phone or "").strip()
        clean_addr = (address_snippet or "").lower()

        # 1. Match by Phone Prefix
        if clean_phone:
            for cc, info in COUNTRY_REGIONS.items():
                prefix = info["phone_prefix"]
                if clean_phone.startswith(prefix) or f"({prefix})" in clean_phone:
                    return {
                        "country_code": cc,
                        "country_name": info["name"],
                        "region": info["region"],
                        "matched_by": "phone_prefix",
                    }

        # 2. Match by TLD
        for cc, info in COUNTRY_REGIONS.items():
            for tld in info["tlds"]:
                if clean_domain.endswith(tld):
                    return {
                        "country_code": cc,
                        "country_name": info["name"],
                        "region": info["region"],
                        "matched_by": "tld",
                    }

        # 3. Match by City / Country in Address
        city_country_map = {
            "mumbai": "IN", "bangalore": "IN", "bengaluru": "IN", "delhi": "IN", "pune": "IN", "hyderabad": "IN",
            "berlin": "DE", "munich": "DE", "frankfurt": "DE", "hamburg": "DE", "germany": "DE",
            "london": "UK", "manchester": "UK", "birmingham": "UK", "united kingdom": "UK",
            "paris": "FR", "lyon": "FR", "france": "FR",
            "amsterdam": "NL", "rotterdam": "NL", "netherlands": "NL",
            "new york": "US", "san francisco": "US", "austin": "US", "chicago": "US", "seattle": "US", "united states": "US",
            "toronto": "CA", "vancouver": "CA", "montreal": "CA", "canada": "CA",
            "sydney": "AU", "melbourne": "AU", "brisbane": "AU", "australia": "AU",
            "singapore": "SG",
            "dubai": "AE", "abu dhabi": "AE", "uae": "AE",
        }

        for keyword, cc in city_country_map.items():
            if keyword in clean_addr or keyword in clean_domain:
                info = COUNTRY_REGIONS.get(cc, {"name": cc, "region": "International"})
                return {
                    "country_code": cc,
                    "country_name": info["name"],
                    "region": info["region"],
                    "matched_by": "address_or_city",
                }

        # Default Fallback
        return {
            "country_code": fallback_country,
            "country_name": fallback_region,
            "region": fallback_region,
            "matched_by": "fallback",
        }

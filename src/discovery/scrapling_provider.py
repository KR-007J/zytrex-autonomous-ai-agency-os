"""Scrapling-Powered Multi-Source Live Web Discovery Provider.

Leverages the Scrapling framework (scrapling[all]>=0.4.15) to discover real,
live, commercial leads from high-yield web platforms without recurring costs.
"""

from __future__ import annotations
import asyncio
import logging
import re
from typing import List, Optional, AsyncGenerator, Dict, Any, Set
from urllib.parse import urlparse

import scrapling
from scrapling.fetchers import Fetcher

from src.discovery.base import DiscoveryProvider, CandidateDomain

logger = logging.getLogger("leadforge.discovery.scrapling")

# Domain blocklist to filter out platforms, CDNs, social networks, and aggregators
BLOCKED_DOMAINS = {
    "shopify.com", "myshopify.com", "woocommerce.com", "automattic.com",
    "wordpress.com", "wordpress.org", "apple.com", "google.com", "bing.com",
    "duckduckgo.com", "facebook.com", "x.com", "twitter.com", "instagram.com",
    "linkedin.com", "youtube.com", "github.com", "startupranking.com", "myip.ms",
    "cloudflare.com", "amazon.com", "aws.amazon.com", "fastly.com", "akamai.com",
    "jsdelivr.net", "clarity.ms", "googletagmanager.com", "newrelic.com", "schema.org",
    "ahrefs.com", "srbooster.com", "dictionary.com", "thefreedictionary.com", "wiktionary.org"
}

# Top Shopify apps whose review sections contain daily live merchant feedback
SHOPIFY_APPS = [
    "judgeme",
    "klaviyo-email-marketing",
    "loox",
    "pagefly",
    "privy",
    "omnisend",
    "recharge-subscriptions",
    "gorgias",
    "smile-io",
    "pushowl",
    "tidio"
]

# Country codes / slugs for StartupRanking
COUNTRY_SLUGS = {
    "united states": "united-states",
    "us": "united-states",
    "united kingdom": "united-kingdom",
    "uk": "united-kingdom",
    "canada": "canada",
    "australia": "australia",
    "germany": "germany",
    "india": "india",
    "france": "france",
    "spain": "spain",
    "italy": "italy",
    "netherlands": "netherlands",
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def clean_domain(raw: str) -> Optional[str]:
    """Clean and normalize domain names."""
    if not raw:
        return None
    raw = raw.strip().lower()
    raw = re.sub(r"^https?://", "", raw)
    raw = raw.split("/")[0].split("?")[0].split(":")[0].strip()
    if raw.startswith("www."):
        raw = raw[4:]
    if not raw or "." not in raw:
        return None
    if any(blocked in raw for blocked in BLOCKED_DOMAINS):
        return None
    # Validate basic domain format
    if not re.match(r"^[a-z0-9][a-z0-9\.\-]{1,61}[a-z0-9]\.[a-z]{2,}$", raw):
        return None
    return raw


class ScraplingProvider(DiscoveryProvider):
    name = "Scrapling Web Engine"
    description = "Zero-cost adaptive web scraper mining live e-commerce stores, active merchants, and high-growth SaaS startups."

    def __init__(self):
        self._timeout = 10
        self._headers = {"User-Agent": USER_AGENT}

    async def health(self) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "status": "HEALTHY",
            "version": getattr(scrapling, "__version__", "unknown"),
            "engine": "Scrapling Adaptive Fetcher (HTTPX + Parsel + Playwright stealth)",
            "strategies": [
                "Shopify App Store Merchant Reviews",
                "StartupRanking Global SaaS Directory",
                "WooCommerce Official Showcase",
                "MyIP.ms Cloud Infrastructure Database",
            ]
        }

    async def discover(
        self,
        technology: str,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        limit: int = 25,
    ) -> List[CandidateDomain]:
        candidates: List[CandidateDomain] = []
        async for candidate in self.stream(technology, country, industry, limit):
            candidates.append(candidate)
        return candidates

    async def stream(
        self,
        technology: str,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        limit: int = 25,
        exclude_domains: Optional[Set[str]] = None,
    ) -> AsyncGenerator[CandidateDomain, None]:
        seen = set(exclude_domains or set())
        tech_lower = (technology or "").lower().strip()
        count = 0

        # Determine strategy execution order based on target technology
        is_shopify = any(t in tech_lower for t in ["shopify", "e-commerce", "ecommerce", "store"])
        is_woo = any(t in tech_lower for t in ["woo", "woocommerce", "wordpress"])
        is_saas = any(t in tech_lower for t in ["saas", "react", "nextjs", "vue", "angular", "tailwind", "stripe", "api", "ai"])

        strategies = []
        if is_shopify:
            strategies = [self._stream_shopify_reviews, self._stream_myip_hosts, self._stream_startupranking]
        elif is_woo:
            strategies = [self._stream_woo_showcase, self._stream_shopify_reviews, self._stream_startupranking]
        elif is_saas:
            strategies = [self._stream_startupranking, self._stream_woo_showcase, self._stream_shopify_reviews]
        else:
            strategies = [
                self._stream_shopify_reviews,
                self._stream_woo_showcase,
                self._stream_startupranking,
                self._stream_myip_hosts,
            ]

        for strat in strategies:
            if count >= limit:
                break
            try:
                async for cand in strat(tech_lower, country, industry, limit - count):
                    if cand.domain not in seen:
                        seen.add(cand.domain)
                        count += 1
                        yield cand
                        if count >= limit:
                            break
            except Exception as e:
                logger.warning(f"Scrapling strategy {strat.__name__} encountered error: {e}")

    async def _stream_shopify_reviews(
        self, technology: str, country: Optional[str], industry: Optional[str], needed: int
    ) -> AsyncGenerator[CandidateDomain, None]:
        """Scrape active Shopify merchants who submitted reviews to top e-commerce apps."""
        yielded = 0
        for app in SHOPIFY_APPS:
            if yielded >= needed:
                break
            url = f"https://apps.shopify.com/{app}/reviews"
            try:
                page = await asyncio.to_thread(Fetcher.get, url, headers=self._headers, timeout=self._timeout)
                if page.status != 200:
                    continue

                reviews = page.css("[data-merchant-review]")
                for r in reviews:
                    if yielded >= needed:
                        break
                    html = r.prettify()
                    texts = [
                        t.strip() for t in re.findall(r">([^<]+)<", html)
                        if t.strip() and t.strip() not in ["Show more", "Show less"]
                    ]
                    short = [
                        t for t in texts
                        if 2 < len(t) < 40 and not any(k in t.lower() for k in ["2026", "2025", "using the app", "star", "stars", "reply", "helpful"])
                    ]
                    if not short:
                        continue

                    raw_name = short[-2] if len(short) >= 2 else short[0]
                    merchant_country = short[-1] if len(short) >= 2 else country

                    candidate = clean_domain(raw_name)
                    if not candidate:
                        slug = re.sub(r"[^a-z0-9]", "", raw_name.lower())
                        if len(slug) >= 3:
                            candidate = clean_domain(f"{slug}.com")

                    if candidate:
                        yielded += 1
                        yield CandidateDomain(
                            domain=candidate,
                            source="scrapling_shopify_reviews",
                            technology_hint="shopify",
                            country_hint=merchant_country or country,
                            industry_hint=industry or "e-commerce",
                            confidence_hint=0.88,
                        )
            except Exception as e:
                logger.debug(f"Error scraping Shopify reviews for {app}: {e}")

    async def _stream_woo_showcase(
        self, technology: str, country: Optional[str], industry: Optional[str], needed: int
    ) -> AsyncGenerator[CandidateDomain, None]:
        """Scrape verified enterprise WooCommerce stores from the official WooCommerce Showcase."""
        yielded = 0
        for page_num in range(1, 4):
            if yielded >= needed:
                break
            url = f"https://woocommerce.com/showcase/page/{page_num}/" if page_num > 1 else "https://woocommerce.com/showcase/"
            try:
                page = await asyncio.to_thread(Fetcher.get, url, headers=self._headers, timeout=self._timeout)
                if page.status != 200:
                    break

                for a in page.css("a"):
                    if yielded >= needed:
                        break
                    href = a.attrib.get("href", "")
                    if href.startswith("http"):
                        d = clean_domain(href)
                        if d:
                            yielded += 1
                            yield CandidateDomain(
                                domain=d,
                                source="scrapling_woo_showcase",
                                technology_hint="woocommerce",
                                country_hint=country,
                                industry_hint=industry or "e-commerce",
                                confidence_hint=0.92,
                            )
            except Exception as e:
                logger.debug(f"Error scraping WooCommerce showcase page {page_num}: {e}")

    async def _stream_myip_hosts(
        self, technology: str, country: Optional[str], industry: Optional[str], needed: int
    ) -> AsyncGenerator[CandidateDomain, None]:
        """Scrape commercial domains mapped to dedicated cloud platform IP blocks via MyIP.ms."""
        yielded = 0
        url = "https://myip.ms/browse/sites/1/own/376714"
        try:
            page = await asyncio.to_thread(Fetcher.get, url, headers=self._headers, timeout=self._timeout)
            if page.status == 200:
                rows = page.css("table#sites_tbl tbody tr")
                for r in rows[::2]:
                    if yielded >= needed:
                        break
                    links = [a.text.strip() for a in r.css("a") if a.text and a.text.strip()]
                    if links:
                        d = clean_domain(links[0])
                        if d:
                            yielded += 1
                            yield CandidateDomain(
                                domain=d,
                                source="scrapling_myip_hosts",
                                technology_hint="shopify",
                                country_hint=links[3] if len(links) >= 4 else country,
                                industry_hint=industry or "e-commerce",
                                confidence_hint=0.85,
                            )
        except Exception as e:
            logger.debug(f"Error scraping MyIP.ms hosts: {e}")

    async def _stream_startupranking(
        self, technology: str, country: Optional[str], industry: Optional[str], needed: int
    ) -> AsyncGenerator[CandidateDomain, None]:
        """Scrape modern tech and SaaS startups from StartupRanking directories."""
        yielded = 0
        country_key = (country or "united states").lower().strip()
        slug = COUNTRY_SLUGS.get(country_key, "united-states")
        url = f"https://www.startupranking.com/top/country/{slug}"

        try:
            page = await asyncio.to_thread(Fetcher.get, url, headers=self._headers, timeout=self._timeout)
            if page.status != 200:
                return

            rows = page.css("tr[id^=\"startup_\"]")
            for r in rows:
                if yielded >= needed:
                    break
                row_id = r.attrib.get("id", "")
                startup_slug = row_id.replace("startup_", "").strip()
                if not startup_slug:
                    continue

                profile_url = f"https://www.startupranking.com/startup/{startup_slug}"
                try:
                    profile_page = await asyncio.to_thread(
                        Fetcher.get, profile_url, headers=self._headers, timeout=5
                    )
                    domain = None
                    if profile_page.status == 200:
                        ref_link = profile_page.css("a[href*=\"utm_medium=referral\"]")
                        if ref_link:
                            href = ref_link[0].attrib.get("href", "")
                            m = re.search(r"https?://([^/?]+)", href)
                            if m:
                                domain = clean_domain(m.group(1))

                    if not domain:
                        domain = clean_domain(f"{startup_slug}.com")

                    if domain:
                        yielded += 1
                        yield CandidateDomain(
                            domain=domain,
                            source="scrapling_startupranking",
                            technology_hint=technology if technology else "saas",
                            country_hint=country or "United States",
                            industry_hint=industry or "technology",
                            confidence_hint=0.90,
                        )
                except Exception as ex:
                    logger.debug(f"Error fetching startup profile {startup_slug}: {ex}")
        except Exception as e:
            logger.debug(f"Error scraping StartupRanking country {slug}: {e}")

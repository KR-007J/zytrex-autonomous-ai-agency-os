"""Multi-Social Platform & Search Scraper Engine (Bing, LinkedIn, Twitter/X, GitHub, Reddit)."""

from __future__ import annotations
import time
import random
import logging
import urllib.parse
import urllib.robotparser
import re
import base64
from typing import Optional, List, Dict, Any, Tuple
from bs4 import BeautifulSoup
import httpx
from sqlalchemy.orm import Session

from src.config import RootConfig, load_config, ClassifiedSiteConfig
from src.database.db import LeadRepository, get_db_session
from src.database.models import ScrapeJob, Lead
from src.scraper.extractors import (
    extract_emails,
    extract_phones,
    extract_linkedin_url,
    calculate_lead_score,
    extract_field_by_selector,
    clean_text,
    normalize_domain,
)
from src.scraper.dedupe import normalize_lead_dict, normalize_company_name

logger = logging.getLogger("leadgen.scraper")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Public search and API engines that provide public search interfaces
EXEMPT_SEARCH_ENGINES = {"bing.com", "duckduckgo.com", "google.com", "api.github.com", "news.ycombinator.com"}


def decode_bing_url(url: str) -> str:
    """Extract real destination URL from Bing click tracker."""
    if not url or "bing.com/ck/a" not in url:
        return url
    try:
        match = re.search(r"[?&]u=a1([^&]+)", url)
        if match:
            encoded_val = match.group(1)
            padding = 4 - (len(encoded_val) % 4)
            if padding and padding != 4:
                encoded_val += "=" * padding
            decoded = base64.b64decode(encoded_val).decode("utf-8", errors="ignore")
            if decoded.startswith("http"):
                return decoded
    except Exception:
        pass
    return url


class ScraperEngine:
    def __init__(self, config: Optional[RootConfig] = None):
        self.config = config or load_config()
        self.robots_cache: Dict[str, urllib.robotparser.RobotFileParser] = {}
        self.client = httpx.Client(
            timeout=self.config.scraping.rate_limiting.timeout_seconds,
            follow_redirects=True,
            verify=False,
        )

    def _get_user_agent(self) -> str:
        agents = self.config.scraping.user_agents
        if agents:
            return random.choice(agents)
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

    def _apply_rate_limit(self) -> None:
        rl = self.config.scraping.rate_limiting
        delay = random.uniform(rl.min_delay_seconds, rl.max_delay_seconds)
        if rl.jitter:
            delay += random.uniform(0.1, 0.5)
        time.sleep(delay)

    def is_allowed_by_robots(self, url: str) -> bool:
        """Check if URL fetch is permitted under target domain's robots.txt."""
        if not self.config.scraping.rate_limiting.respect_robots_txt:
            return True

        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        if not domain:
            return True

        # Public search portals and open APIs are permitted
        if any(se in domain for se in EXEMPT_SEARCH_ENGINES):
            return True

        if domain not in self.robots_cache:
            robots_url = f"{parsed.scheme}://{domain}/robots.txt"
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)
            try:
                resp = self.client.get(
                    robots_url,
                    headers={"User-Agent": self._get_user_agent()},
                    timeout=5.0,
                )
                if resp.status_code == 200:
                    rp.parse(resp.text.splitlines())
                else:
                    rp.allow_all = True
            except Exception:
                rp.allow_all = True
            self.robots_cache[domain] = rp

        allowed = self.robots_cache[domain].can_fetch("*", url)
        if not allowed:
            logger.warning(f"URL {url} restricted by domain robots.txt policy.")
        return allowed

    def fetch_page(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Fetch URL content with rate limiting, rotating user-agents, and robots check."""
        if not self.is_allowed_by_robots(url):
            return None, "Blocked by robots.txt policy"

        self._apply_rate_limit()

        headers = {
            "User-Agent": self._get_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        retries = self.config.scraping.rate_limiting.max_retries
        for attempt in range(1, retries + 1):
            try:
                resp = self.client.get(url, headers=headers)
                if resp.status_code == 200:
                    return resp.text, None
                elif resp.status_code in (403, 429):
                    time.sleep(attempt * 1.5)
                else:
                    return None, f"HTTP Error {resp.status_code}"
            except Exception as e:
                if attempt == retries:
                    return None, str(e)
                time.sleep(attempt * 1.0)

        return None, "Max retries exceeded"

    def scrape_classified_site(self, site: ClassifiedSiteConfig, session: Session) -> ScrapeJob:
        """Scrape configured directory/classified site with dynamic CSS/XPath selectors."""
        job = ScrapeJob(
            job_name=f"Site: {site.name}",
            target_site=site.base_url,
            status="running",
        )
        session.add(job)
        session.commit()

        html_content, error = self.fetch_page(site.base_url)
        if not html_content:
            job.status = "failed"
            job.error_log = error or "Failed to retrieve page content"
            session.commit()
            return job

        soup = BeautifulSoup(html_content, "html.parser")
        listing_selectors = [s.strip() for s in site.listing_selector.split(",") if s.strip()]

        cards = []
        for selector in listing_selectors:
            found = soup.select(selector)
            if found:
                cards = found
                break

        found_count = 0
        new_count = 0

        for card in cards:
            card_text = card.get_text(separator=" ", strip=True)
            card_html = str(card)

            company_name = extract_field_by_selector(card, site.fields.get("company_name", ""))
            contact_name = extract_field_by_selector(card, site.fields.get("contact_name", ""))
            email = extract_field_by_selector(card, site.fields.get("email", ""))
            phone = extract_field_by_selector(card, site.fields.get("phone", ""))
            source_url = extract_field_by_selector(card, site.fields.get("source_url", ""))
            industry_tag = extract_field_by_selector(card, site.fields.get("industry_tag", ""))
            location = extract_field_by_selector(card, site.fields.get("location", ""))

            # Regex text fallbacks
            if not email:
                emails_found = extract_emails(card_html)
                if emails_found:
                    email = emails_found[0]

            if not phone:
                phones_found = extract_phones(card_text)
                if phones_found:
                    phone = phones_found[0]

            linkedin_url = extract_linkedin_url(card_html)

            if not company_name:
                words = card_text.split()
                if words:
                    company_name = " ".join(words[:4])
                else:
                    continue

            lead_score = calculate_lead_score(
                has_email=bool(email),
                has_phone=bool(phone),
                has_contact_name=bool(contact_name),
                has_linkedin=bool(linkedin_url),
                has_domain=bool(source_url),
            )

            raw_data = {
                "company_name": company_name,
                "contact_name": contact_name,
                "email": email,
                "phone": phone,
                "source_url": source_url or site.base_url,
                "industry_tag": industry_tag or site.name,
                "location": location or "USA",
                "linkedin_url": linkedin_url,
                "lead_score": lead_score,
                "raw_snippet": card_text[:500],
            }

            normalized = normalize_lead_dict(raw_data)
            lead, is_new = LeadRepository.create_or_update(session, normalized)
            found_count += 1
            if is_new:
                new_count += 1

        job.leads_found = found_count
        job.leads_new = new_count
        job.status = "completed"
        session.commit()
        return job

    def scrape_social_platform(self, platform: str, query: str, session: Session) -> ScrapeJob:
        """Scrape specialized social platform discovery footprints."""
        platform_dorks = {
            "linkedin": f"site:linkedin.com/in/ OR site:linkedin.com/company/ {query}",
            "twitter": f"site:twitter.com OR site:x.com {query} (founder OR CEO)",
            "github": f"site:github.com {query} (email OR contact)",
            "reddit": f"site:reddit.com/r/startups OR site:reddit.com/r/SaaS {query}",
            "producthunt": f"site:producthunt.com/products {query}",
        }

        full_query = platform_dorks.get(platform.lower(), query)
        job_name = f"{platform.upper()} Discovery: {query}"
        
        job = ScrapeJob(
            job_name=job_name,
            target_site=platform.capitalize(),
            status="running",
        )
        session.add(job)
        session.commit()

        encoded_query = urllib.parse.quote_plus(full_query)
        search_url = f"https://www.bing.com/search?q={encoded_query}"

        html_content, error = self.fetch_page(search_url)
        if not html_content:
            job.status = "failed"
            job.error_log = error or "Platform query returned empty result"
            session.commit()
            return job

        soup = BeautifulSoup(html_content, "html.parser")
        results = soup.select(".b_algo, .result, .results_links")

        found_count = 0
        new_count = 0

        for item in results[:15]:
            title_elem = item.select_one("h2 a, h2, .result__title")
            snippet_elem = item.select_one(".b_caption p, p, .result__snippet")
            link_elem = item.select_one("h2 a, a.result__a, a")

            title = clean_text(title_elem.get_text()) if title_elem else ""
            snippet = clean_text(snippet_elem.get_text()) if snippet_elem else ""
            raw_url = link_elem.get("href", "") if link_elem else ""
            target_url = decode_bing_url(raw_url)

            if not title and not snippet:
                continue

            full_text = f"{title} {snippet}"
            emails = extract_emails(full_text)
            phones = extract_phones(full_text)
            linkedin_url = extract_linkedin_url(full_text) or (target_url if "linkedin.com" in target_url else None)

            raw_title = title.split("-")[0].split("|")[0].split(":")[0].strip()
            company_name = normalize_company_name(raw_title)

            lead_score = calculate_lead_score(
                has_email=bool(emails),
                has_phone=bool(phones),
                has_contact_name=False,
                has_linkedin=bool(linkedin_url),
                has_domain=bool(target_url),
            )

            raw_data = {
                "company_name": company_name or f"{platform.capitalize()} Lead",
                "contact_name": None,
                "email": emails[0] if emails else None,
                "phone": phones[0] if phones else None,
                "source_url": target_url,
                "industry_tag": platform.capitalize(),
                "location": "USA",
                "linkedin_url": linkedin_url,
                "lead_score": lead_score,
                "raw_snippet": snippet[:500],
            }

            normalized = normalize_lead_dict(raw_data)
            lead, is_new = LeadRepository.create_or_update(session, normalized)
            found_count += 1
            if is_new:
                new_count += 1

        job.leads_found = found_count
        job.leads_new = new_count
        job.status = "completed"
        session.commit()
        return job

    def run_all_configured_scrapers(self, session: Session) -> List[ScrapeJob]:
        """Execute all enabled classified sites and multi-social platform discovery."""
        jobs = []

        for site in self.config.scraping.classified_sites:
            if site.enabled:
                job = self.scrape_classified_site(site, session)
                jobs.append(job)

        social_targets = [
            ("linkedin", "AI B2B SaaS startup founder"),
            ("twitter", "SaaS founder building in public"),
            ("github", "FastAPI AI developer open source"),
            ("reddit", "SaaS launch revenue growth"),
        ]

        for platform, query in social_targets:
            job = self.scrape_social_platform(platform, query, session)
            jobs.append(job)

        return jobs

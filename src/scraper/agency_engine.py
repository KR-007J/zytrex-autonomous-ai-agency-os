"""Region-specific and Software Development Intent Discovery Engine with Real Location Detection."""

from __future__ import annotations
import urllib.parse
import re
import httpx
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup

from src.config import RootConfig, load_config
from src.database.db import LeadRepository
from src.database.models import ScrapeJob, Lead
from src.scraper.extractors import (
    extract_emails,
    extract_phones,
    extract_linkedin_url,
    calculate_lead_score,
    extract_real_location,
    clean_text,
    normalize_domain,
)
from src.scraper.dedupe import normalize_lead_dict, normalize_company_name

TARGET_REGIONS = [
    # Indian Metros
    "Mumbai, Maharashtra",
    "Bengaluru, Karnataka",
    "Delhi NCR, India",
    "Pune, Maharashtra",
    "Hyderabad, Telangana",
    # US Metros
    "New York, NY",
    "San Francisco & Bay Area, CA",
    "Austin, TX",
    "Miami & South Florida, FL",
    "Chicago, IL",
    "Los Angeles, CA",
    "Seattle, WA",
    "Boston, MA",
    "Nationwide USA",
    # Global Metros
    "London, United Kingdom",
    "Dubai, UAE",
    "Singapore",
]

# Alias for backwards compatibility
US_REGIONS = TARGET_REGIONS

TARGET_NICHES = [
    "Healthcare & Medical Clinics",
    "Real Estate & Property Management",
    "Law Firms & Legal Practices",
    "Logistics, Freight & Supply Chain",
    "E-Commerce & D2C Brands",
    "Financial Services & Wealth Management",
    "Early-Stage Tech Startups",
    "Home Services & Construction",
]

INTENT_CATEGORIES = {
    "web_redesign": "Website Modernization & Digital Presence",
    "custom_app": "Custom Web & Mobile App Development",
    "saas_mvp": "SaaS MVP & Product Engineering",
    "hiring_devs": "Contract Software Engineering & Dedicated Devs",
}


class AgencyLeadDiscoveryEngine:
    def __init__(self, config: Optional[RootConfig] = None):
        self.config = config or load_config()

    @staticmethod
    def generate_regional_dorks(
        location: str,
        niche: str,
        opportunity_type: str = "web_redesign",
    ) -> List[str]:
        """Generate targeted search queries for companies needing software/web services."""
        loc_clean = location.replace("USA", "").replace("Nationwide", "").replace("& Bay Area", "").replace("& South Florida", "").strip()
        loc_clause = f'"{loc_clean}"' if loc_clean else '"India" OR "USA"'

        dorks = []
        if opportunity_type == "web_redesign":
            dorks.append(f'{niche} {loc_clause} "contact us" email OR phone')
            dorks.append(f'"{niche}" {loc_clause} "website designed by" OR "powered by" email')
            dorks.append(f'{loc_clause} "{niche}" "redesign" OR "new website" email')
        elif opportunity_type == "custom_app":
            dorks.append(f'{niche} {loc_clause} "mobile app" OR "client portal" email')
            dorks.append(f'{niche} {loc_clause} "custom software" email')
        elif opportunity_type == "saas_mvp":
            dorks.append(f'site:twitter.com OR site:x.com "founder" "{niche}" {loc_clause}')
            dorks.append(f'site:linkedin.com/in/ "founder" "{niche}" {loc_clause} email')
        else:
            dorks.append(f'{niche} {loc_clause} "hiring developer" OR "software development"')

        return dorks

    def hunt_regional_agency_leads(
        self,
        location: str,
        niche: str,
        opportunity_type: str,
        session: Session,
        max_results: int = 20,
    ) -> ScrapeJob:
        """Run deep regional search combining Bing Search and GitHub Region Discovery with accurate real location detection."""
        from src.scraper.engine import ScraperEngine, decode_bing_url

        scraper = ScraperEngine(self.config)
        opportunity_desc = INTENT_CATEGORIES.get(opportunity_type, "Software & Web Development Need")
        dorks = self.generate_regional_dorks(location, niche, opportunity_type)
        primary_query = dorks[0]

        job = ScrapeJob(
            job_name=f"Agency Hunt: {niche} in {location} ({opportunity_desc})",
            target_site=f"Regional Search ({location})",
            status="running",
        )
        session.add(job)
        session.commit()

        found_count = 0
        new_count = 0

        # STREAM 1: Bing Regional Search
        encoded_query = urllib.parse.quote_plus(primary_query)
        search_url = f"https://www.bing.com/search?q={encoded_query}"

        html_content, error = scraper.fetch_page(search_url)
        if html_content:
            soup = BeautifulSoup(html_content, "html.parser")
            results = soup.select(".b_algo, .result, .results_links")

            for item in results[:max_results]:
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
                linkedin_url = extract_linkedin_url(full_text)

                # Detect real-world geographical location dynamically
                real_location = extract_real_location(
                    text_or_html=full_text,
                    domain_or_url=target_url,
                    fallback=location,
                )

                raw_title = title.split("-")[0].split("|")[0].split(":")[0].strip()
                company_name = normalize_company_name(raw_title)

                lead_score = calculate_lead_score(
                    has_email=bool(emails),
                    has_phone=bool(phones),
                    has_contact_name=False,
                    has_linkedin=bool(linkedin_url),
                    has_domain=bool(target_url),
                )
                if emails or phones:
                    lead_score = min(lead_score + 15, 100)

                raw_data = {
                    "company_name": company_name or f"{niche} Business",
                    "contact_name": None,
                    "email": emails[0] if emails else None,
                    "phone": phones[0] if phones else None,
                    "source_url": target_url,
                    "source_domain": normalize_domain(target_url),
                    "industry_tag": f"{niche}",
                    "location": real_location,
                    "linkedin_url": linkedin_url,
                    "lead_score": lead_score,
                    "raw_snippet": f"[{opportunity_desc}] {snippet[:400]}",
                }

                normalized = normalize_lead_dict(raw_data)
                normalized["location"] = real_location
                lead, is_new = LeadRepository.create_or_update(session, normalized)
                found_count += 1
                if is_new:
                    new_count += 1

        # STREAM 2: GitHub Regional Organization Discovery
        try:
            loc_keyword = location.split(",")[0].replace("& Bay Area", "").replace("& South Florida", "").strip()
            gh_url = f"https://api.github.com/search/users?q=location:\"{loc_keyword}\"+type:org&per_page=10"
            gh_resp = scraper.client.get(gh_url, headers={"User-Agent": "LeadGen-Pro-Agent/1.0"})
            if gh_resp.status_code == 200:
                items = gh_resp.json().get("items", [])
                for org in items:
                    org_login = org.get("login", "")
                    org_url = org.get("html_url", "")
                    
                    detail_resp = scraper.client.get(f"https://api.github.com/users/{org_login}", headers={"User-Agent": "LeadGen-Pro-Agent/1.0"})
                    if detail_resp.status_code == 200:
                        detail = detail_resp.json()
                        company_name = detail.get("name") or org_login
                        blog = detail.get("blog")
                        email = detail.get("email")
                        bio = detail.get("bio") or f"Organization in {location}"
                        profile_loc = detail.get("location") or location

                        real_location = extract_real_location(
                            text_or_html=f"{profile_loc} {bio}",
                            domain_or_url=blog or org_url,
                            fallback=location,
                        )

                        lead_score = calculate_lead_score(
                            has_email=bool(email),
                            has_phone=False,
                            has_contact_name=False,
                            has_linkedin=False,
                            has_domain=bool(blog),
                        )

                        raw_data = {
                            "company_name": company_name,
                            "contact_name": None,
                            "email": email,
                            "phone": None,
                            "source_url": blog or org_url,
                            "source_domain": normalize_domain(blog or org_url),
                            "industry_tag": f"{niche}",
                            "location": real_location,
                            "linkedin_url": None,
                            "lead_score": lead_score,
                            "raw_snippet": f"[{opportunity_desc}] {bio}",
                        }
                        normalized = normalize_lead_dict(raw_data)
                        normalized["location"] = real_location
                        lead, is_new = LeadRepository.create_or_update(session, normalized)
                        found_count += 1
                        if is_new:
                            new_count += 1
        except Exception:
            pass

        job.leads_found = found_count
        job.leads_new = new_count
        job.status = "completed"
        session.commit()
        return job

"""Lead deduplication and normalization engine."""

from __future__ import annotations
import re
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from src.database.models import Lead, ContactedMemory
from src.scraper.extractors import normalize_domain, clean_text

LEGAL_SUFFIXES = [
    r"\binc\.?\b",
    r"\bincorporated\b",
    r"\bllc\.?\b",
    r"\bltd\.?\b",
    r"\blimited\b",
    r"\bcorp\.?\b",
    r"\bcorporation\b",
    r"\bgmbh\b",
    r"\bco\.?\b",
]


def normalize_company_name(name: Optional[str]) -> str:
    """Normalize company name by stripping legal suffixes and excess symbols."""
    if not name:
        return "Unknown Company"

    cleaned = name.strip()
    # Remove URL components if accidental
    cleaned = re.sub(r"^https?://", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"/.*$", "", cleaned)

    # Strip legal entity suffixes
    for suffix in LEGAL_SUFFIXES:
        cleaned = re.sub(suffix, "", cleaned, flags=re.IGNORECASE).strip()

    # Clean whitespace and trailing punctuation
    cleaned = re.sub(r"[\s\-_,\.]+$", "", cleaned)
    cleaned = re.sub(r"^\W+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned if cleaned else "Unknown Company"


def is_already_contacted(
    session: Session,
    email: Optional[str] = None,
    domain: Optional[str] = None,
    linkedin_url: Optional[str] = None,
) -> bool:
    """Check if lead has already been contacted in past runs."""
    identifiers = []
    if email and email.strip():
        identifiers.append(email.strip().lower())
    if domain and domain.strip():
        identifiers.append(domain.strip().lower())
    if linkedin_url and linkedin_url.strip():
        identifiers.append(linkedin_url.strip().lower())

    if not identifiers:
        return False

    existing = (
        session.query(ContactedMemory)
        .filter(ContactedMemory.identifier.in_(identifiers))
        .first()
    )
    return existing is not None


def record_contacted(
    session: Session,
    identifier: str,
    lead_id: Optional[int] = None,
    channel: str = "linkedin_manual",
    notes: Optional[str] = None,
) -> ContactedMemory:
    """Record an identifier as contacted in persistent memory."""
    clean_id = identifier.strip().lower()
    existing = session.query(ContactedMemory).filter(ContactedMemory.identifier == clean_id).first()
    if existing:
        existing.notes = notes
        return existing

    record = ContactedMemory(
        identifier=clean_id,
        lead_id=lead_id,
        channel=channel,
        notes=notes,
    )
    session.add(record)
    session.flush()
    return record


def normalize_lead_dict(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize a raw scraped lead dictionary."""
    company_name = normalize_company_name(raw_data.get("company_name"))
    contact_name = clean_text(raw_data.get("contact_name"))
    email = raw_data.get("email")
    if email:
        email = email.strip().lower()
    phone = clean_text(raw_data.get("phone"))
    source_url = clean_text(raw_data.get("source_url"))
    source_domain = normalize_domain(source_url) or normalize_domain(raw_data.get("source_domain"))
    industry_tag = clean_text(raw_data.get("industry_tag")) or "B2B / Technology"
    location = clean_text(raw_data.get("location"))
    linkedin_url = clean_text(raw_data.get("linkedin_url"))

    return {
        "company_name": company_name,
        "contact_name": contact_name,
        "email": email,
        "phone": phone,
        "source_url": source_url,
        "source_domain": source_domain,
        "industry_tag": industry_tag,
        "location": location,
        "linkedin_url": linkedin_url,
        "raw_snippet": raw_data.get("raw_snippet"),
        "custom_metadata": raw_data.get("custom_metadata"),
    }

"""Deterministic public contact and business info extractor."""

from __future__ import annotations
import re
import json
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup


EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)
PHONE_REGEX = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b"
)

IGNORED_EMAIL_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js", ".woff", ".pdf"
)

ROLE_BASED_PREFIXES = (
    "info", "support", "sales", "contact", "hello", "team", "admin", "help", "enquiries", "office", "general"
)


class ExtractedContact:
    def __init__(
        self,
        value: str,
        contact_type: str,  # 'email', 'phone', 'social'
        source_url: str,
        role_type: str = "UNKNOWN",  # 'ROLE_BASED' or 'DIRECT'
        confidence: float = 0.90,
    ):
        self.value = value
        self.contact_type = contact_type
        self.source_url = source_url
        self.role_type = role_type
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "type": self.contact_type,
            "source_url": self.source_url,
            "role_type": self.role_type,
            "confidence": self.confidence,
        }


class ContactExtractor:
    """Extracts public business intelligence from web content without guessing."""

    @classmethod
    def sanitize_formula(cls, value: Optional[str], is_phone: bool = False) -> Optional[str]:
        """Neutralize formula injection (CSV/Excel/Calc injection).

        Prepends a single quote "'" to values starting with '=', '+', '-', '@', '\\t', '\\r'.
        For legitimate international phone numbers starting with '+', preserves the leading '+'
        if followed by valid phone digits and punctuation. Any formula command or operator
        is safely quoted.
        """
        if not value or not isinstance(value, str):
            return value

        if not value:
            return value

        first_char = value[0]
        if first_char in ("=", "@", "\t", "\r"):
            return "'" + value

        if first_char in ("+", "-"):
            if is_phone and first_char == "+":
                remainder = value[1:].strip()
                if re.match(r"^[\d\s().-]{6,25}$", remainder) and sum(c.isdigit() for c in remainder) >= 6:
                    return value
            return "'" + value

        val_lstrip = value.lstrip(" \t\r\n")
        if val_lstrip and val_lstrip[0] in ("=", "@", "+", "-"):
            if is_phone and val_lstrip[0] == "+":
                remainder = val_lstrip[1:].strip()
                if re.match(r"^[\d\s().-]{6,25}$", remainder) and sum(c.isdigit() for c in remainder) >= 6:
                    return value
            return "'" + value

        return value

    @classmethod
    def extract_from_html(cls, html: str, source_url: str) -> Dict[str, Any]:
        if not html:
            return {
                "business_name": None,
                "description": None,
                "emails": [],
                "phones": [],
                "socials": {},
                "address": None,
                "location": None,
            }

        soup = BeautifulSoup(html[:600000], "html.parser")

        # 1. Business Name, Description & Physical Address
        business_name = None
        description = None
        address = None

        # Check JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, list):
                    data = data[0]
                if isinstance(data, dict):
                    schema_type = str(data.get("@type", "")).lower()
                    if any(k in schema_type for k in ("organization", "store", "business", "corporation", "localbusiness", "place")):
                        if "name" in data and isinstance(data["name"], str) and not business_name:
                            business_name = data["name"].strip()
                        if "description" in data and isinstance(data["description"], str) and not description:
                            description = data["description"].strip()
                        if "address" in data and not address:
                            addr_raw = data["address"]
                            if isinstance(addr_raw, str):
                                address = addr_raw.strip()
                            elif isinstance(addr_raw, dict):
                                parts = [
                                    str(addr_raw.get(k, "")).strip()
                                    for k in ("streetAddress", "addressLocality", "addressRegion", "postalCode", "addressCountry")
                                    if addr_raw.get(k)
                                ]
                                if parts:
                                    address = ", ".join(parts)
            except Exception:
                pass

        # Check OpenGraph & Meta
        if not business_name:
            og_name = soup.find("meta", property="og:site_name")
            if og_name and og_name.get("content"):
                business_name = og_name["content"].strip()

        if not business_name and soup.title and soup.title.string:
            title_text = soup.title.string.strip()
            parts = re.split(r"[\s\-_\|•]+", title_text)
            if parts:
                business_name = parts[0].strip()

        if not description:
            meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description")
            if meta_desc and meta_desc.get("content"):
                description = meta_desc["content"].strip()

        # HTML Address / Location Extraction fallback
        if not address:
            addr_tag = soup.find("address")
            if addr_tag:
                cleaned = re.sub(r"\s+", " ", addr_tag.get_text(separator=" ")).strip()
                if 10 <= len(cleaned) <= 300:
                    address = cleaned

        if not address:
            itemprop_addr = soup.find(attrs={"itemprop": "address"})
            if itemprop_addr:
                cleaned = re.sub(r"\s+", " ", itemprop_addr.get_text(separator=" ")).strip()
                if 10 <= len(cleaned) <= 300:
                    address = cleaned

        if not address:
            footer = soup.find("footer")
            if footer:
                loc_elem = footer.find(
                    attrs={"class": re.compile(r"address|location|office|street|postal", re.IGNORECASE)}
                ) or footer.find(
                    attrs={"id": re.compile(r"address|location|office|street|postal", re.IGNORECASE)}
                )
                if loc_elem:
                    cleaned = re.sub(r"\s+", " ", loc_elem.get_text(separator=" ")).strip()
                    if 10 <= len(cleaned) <= 300:
                        address = cleaned

        # 2. Extract Emails
        emails: List[Dict[str, Any]] = []
        seen_emails = set()

        # Search mailto: links first (highest fidelity)
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if href.lower().startswith("mailto:"):
                clean_email = href[7:].split("?")[0].strip().lower()
                clean_email = cls.sanitize_formula(clean_email)
                if clean_email and "@" in clean_email and clean_email not in seen_emails:
                    seen_emails.add(clean_email)
                    prefix = clean_email.lstrip("'").split("@")[0]
                    role = "ROLE_BASED" if any(prefix.startswith(r) for r in ROLE_BASED_PREFIXES) else "DIRECT"
                    emails.append(ExtractedContact(clean_email, "email", source_url, role, 0.98).to_dict())

        # Search raw text for emails
        text_content = soup.get_text(separator=" ")
        for match in EMAIL_REGEX.finditer(text_content):
            cand = match.group(0).lower()
            if not any(cand.endswith(ext) for ext in IGNORED_EMAIL_EXTENSIONS):
                sanitized_cand = cls.sanitize_formula(cand)
                if sanitized_cand not in seen_emails and len(sanitized_cand) < 80:
                    seen_emails.add(sanitized_cand)
                    prefix = sanitized_cand.lstrip("'").split("@")[0]
                    role = "ROLE_BASED" if any(prefix.startswith(r) for r in ROLE_BASED_PREFIXES) else "DIRECT"
                    emails.append(ExtractedContact(sanitized_cand, "email", source_url, role, 0.88).to_dict())

        # 3. Extract Phones
        phones: List[Dict[str, Any]] = []
        seen_phones = set()

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if href.lower().startswith("tel:"):
                clean_phone = href[4:].strip()
                sanitized_phone = cls.sanitize_formula(clean_phone, is_phone=True)
                if len(sanitized_phone) >= 7 and sanitized_phone not in seen_phones:
                    seen_phones.add(sanitized_phone)
                    phones.append(ExtractedContact(sanitized_phone, "phone", source_url, "DIRECT", 0.95).to_dict())

        # 4. Extract Social Links
        socials: Dict[str, str] = {}
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            lower_href = href.lower()
            if "linkedin.com/company" in lower_href and "linkedin" not in socials:
                socials["linkedin"] = href
            elif ("twitter.com/" in lower_href or "x.com/" in lower_href) and "twitter" not in socials:
                socials["twitter"] = href
            elif "github.com/" in lower_href and "github" not in socials:
                socials["github"] = href
            elif "facebook.com/" in lower_href and "facebook" not in socials:
                socials["facebook"] = href
            elif "instagram.com/" in lower_href and "instagram" not in socials:
                socials["instagram"] = href

        sanitized_business_name = cls.sanitize_formula(business_name)
        sanitized_address = cls.sanitize_formula(address)

        return {
            "business_name": sanitized_business_name,
            "description": description,
            "emails": emails,
            "phones": phones,
            "socials": socials,
            "address": sanitized_address,
            "location": sanitized_address,
        }

"""Extractors, normalizers, and location intelligence for emails, phones, domains, and locations."""

from __future__ import annotations
import re
import urllib.parse
from typing import Optional, List, Dict, Any, Tuple
from bs4 import BeautifulSoup, Tag

# Regex for standard emails
EMAIL_REGEX = re.compile(
    r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b",
    re.IGNORECASE,
)
# Obfuscated regex: "name [at] domain [dot] com" or "name(at)domain(dot)io"
OBFUSCATED_EMAIL_REGEX = re.compile(
    r"\b([a-zA-Z0-9_.+-]+)\s*(?:\[at\]|\(at\)|\sat\s)\s*([a-zA-Z0-9-]+)\s*(?:\[dot\]|\(dot\)|\.|\sdot\s)\s*([a-zA-Z]{2,10})\b",
    re.IGNORECASE,
)

# Regex for phone numbers (International and Indian/US/EU formats)
PHONE_REGEX = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}",
)

# Junk email domain / prefixes to ignore
IGNORED_EMAIL_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".css", ".js"}
IGNORED_EMAIL_DOMAINS = {"example.com", "sample.com", "domain.com", "yourdomain.com", "email.com"}

# Location intelligence dictionaries
CITY_MATCH_PATTERNS = [
    # Indian Metros & Tech Hubs
    (re.compile(r"\b(?:Mumbai|Bombay|Mantralaya|BKC|Bandra|Andheri|Nariman Point|Navi Mumbai|Thane|Maharashtra)\b", re.I), "Mumbai, Maharashtra"),
    (re.compile(r"\b(?:Bengaluru|Bangalore|Koramangala|Whitefield|Indiranagar|Electronic City|Karnataka)\b", re.I), "Bengaluru, Karnataka"),
    (re.compile(r"\b(?:New Delhi|Delhi|Gurgaon|Gurugram|Noida|Connaught Place|NCR)\b", re.I), "Delhi NCR, India"),
    (re.compile(r"\b(?:Pune|Hinjewadi|Viman Nagar|Kothrud|Magarpatta)\b", re.I), "Pune, Maharashtra"),
    (re.compile(r"\b(?:Hyderabad|HITEC City|Gachibowli|Secunderabad|Telangana)\b", re.I), "Hyderabad, Telangana"),
    (re.compile(r"\b(?:Chennai|Madras|OMR|T Nagar|Tamil Nadu)\b", re.I), "Chennai, Tamil Nadu"),
    (re.compile(r"\b(?:Kolkata|Calcutta|Salt Lake|West Bengal)\b", re.I), "Kolkata, West Bengal"),
    (re.compile(r"\b(?:Ahmedabad|GIFT City|Gandhinagar|Gujarat)\b", re.I), "Ahmedabad, Gujarat"),

    # US Metros
    (re.compile(r"\b(?:New York|NYC|Manhattan|Brooklyn|Queens|Wall Street)\b", re.I), "New York, NY"),
    (re.compile(r"\b(?:San Francisco|Bay Area|Silicon Valley|Palo Alto|Mountain View|Sunnyvale|Oakland)\b", re.I), "San Francisco & Bay Area, CA"),
    (re.compile(r"\b(?:Austin|Round Rock|Travis County)\b", re.I), "Austin, TX"),
    (re.compile(r"\b(?:Miami|Fort Lauderdale|Brickell|Boca Raton|South Florida)\b", re.I), "Miami & South Florida, FL"),
    (re.compile(r"\b(?:Chicago|Loop|Illinois)\b", re.I), "Chicago, IL"),
    (re.compile(r"\b(?:Los Angeles|Santa Monica|Beverly Hills|Silicon Beach|Hollywood)\b", re.I), "Los Angeles, CA"),
    (re.compile(r"\b(?:Seattle|Bellevue|Redmond|Washington)\b", re.I), "Seattle, WA"),
    (re.compile(r"\b(?:Boston|Cambridge|Massachusetts)\b", re.I), "Boston, MA"),

    # Global Hubs
    (re.compile(r"\b(?:London|Canary Wharf|City of London|Westminster)\b", re.I), "London, United Kingdom"),
    (re.compile(r"\b(?:Dubai|Abu Dhabi|DIFC|UAE|United Arab Emirates)\b", re.I), "Dubai, UAE"),
    (re.compile(r"\b(?:Singapore|Marina Bay)\b", re.I), "Singapore"),
    (re.compile(r"\b(?:Toronto|Ontario|Vancouver)\b", re.I), "Toronto, Canada"),
]


def clean_text(text: Optional[str]) -> Optional[str]:
    """Clean whitespace and remove special non-printable characters."""
    if not text:
        return None
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned if cleaned else None


def normalize_domain(url: Optional[str]) -> Optional[str]:
    """Extract clean domain name from URL."""
    if not url:
        return None
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain if domain else None
    except Exception:
        return None


def extract_real_location(
    text_or_html: str,
    domain_or_url: Optional[str] = None,
    fallback: Optional[str] = None,
) -> str:
    """Intelligently detect real geographical city/state from website content or domain."""
    full_target = f"{domain_or_url or ''} {text_or_html or ''}".lower()

    if ".gov.in" in full_target or ".nic.in" in full_target or "maharashtra.gov" in full_target:
        if "maharashtra" in full_target or "mumbai" in full_target:
            return "Mumbai, Maharashtra"
        return "National, India"

    for pattern, resolved_location in CITY_MATCH_PATTERNS:
        if pattern.search(full_target):
            return resolved_location

    if domain_or_url:
        dom = domain_or_url.lower()
        if dom.endswith(".in") or ".co.in" in dom:
            return "Mumbai, Maharashtra"
        if dom.endswith(".uk") or ".co.uk" in dom:
            return "London, UK"
        if dom.endswith(".ca"):
            return "Canada"
        if dom.endswith(".ae"):
            return "Dubai, UAE"

    return fallback or "Mumbai, Maharashtra"


def clean_email_string(raw_email: str) -> str:
    """Strip trailing punctuation from extracted email."""
    cleaned = raw_email.strip().rstrip(".,;:!?)\"'>")
    cleaned = cleaned.lstrip("(\"'<")
    return cleaned.lower()


def is_valid_email(email: str) -> bool:
    """Validate that email is not an asset artifact or dummy placeholder."""
    if not email or "@" not in email:
        return False
    parts = email.split("@")
    if len(parts) != 2:
        return False
    user, domain = parts
    if not user or not domain or "." not in domain:
        return False
    tld = domain.split(".")[-1]
    if len(tld) < 2 or not tld.isalpha():
        return False
    if any(email.endswith(ext) for ext in IGNORED_EMAIL_EXTENSIONS):
        return False
    if domain in IGNORED_EMAIL_DOMAINS:
        return False
    if len(email) > 100 or len(email) < 5:
        return False
    return True


def extract_emails(text_or_html: str) -> List[str]:
    """Extract and validate public emails from text or HTML."""
    if not text_or_html:
        return []

    found = set()

    # 1. Look for mailto links first
    mailto_matches = re.findall(r"mailto:([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", text_or_html, re.I)
    for raw in mailto_matches:
        cleaned = clean_email_string(raw)
        if is_valid_email(cleaned):
            found.add(cleaned)

    # 2. Standard Regex Search
    for match in EMAIL_REGEX.finditer(text_or_html):
        raw = match.group(0)
        cleaned = clean_email_string(raw)
        if is_valid_email(cleaned):
            found.add(cleaned)

    # 3. Obfuscated Regex Search
    for match in OBFUSCATED_EMAIL_REGEX.finditer(text_or_html):
        user, domain_name, tld = match.groups()
        deobfuscated = f"{user}@{domain_name}.{tld}".lower()
        if is_valid_email(deobfuscated):
            found.add(deobfuscated)

    return sorted(list(found))


def extract_phones(text: str) -> List[str]:
    """Extract and normalize phone numbers."""
    if not text:
        return []

    found = []
    for match in PHONE_REGEX.finditer(text):
        raw = match.group(0).strip()
        digits = re.sub(r"\D", "", raw)
        if 7 <= len(digits) <= 15:
            found.append(raw)

    return found


def extract_linkedin_url(text_or_html: str) -> Optional[str]:
    """Extract official LinkedIn company or profile URL."""
    if not text_or_html:
        return None

    match = re.search(r"https?://(?:www\.)?linkedin\.com/(?:in|company)/[a-zA-Z0-9_-]+/?", text_or_html, re.I)
    if match:
        return match.group(0).rstrip("/")
    return None


def calculate_lead_score(
    has_email: bool,
    has_phone: bool,
    has_contact_name: bool,
    has_linkedin: bool,
    has_domain: bool,
) -> int:
    """Calculate lead score between 0 and 100 based on verified data richness."""
    score = 0
    if has_email:
        score += 45
    if has_phone:
        score += 20
    if has_contact_name:
        score += 15
    if has_linkedin:
        score += 10
    if has_domain:
        score += 10
    return min(score, 100)


def extract_field_by_selector(element: Tag, selector: str) -> Optional[str]:
    """Extract text or attribute using a CSS selector with intelligent link/mailto parsing."""
    if not element or not selector:
        return None

    selector = selector.strip()
    try:
        if "@" in selector:
            css_part, attr_part = selector.split("@", 1)
            target = element.select_one(css_part.strip()) if css_part.strip() else element
            if target and target.has_attr(attr_part.strip()):
                return clean_text(str(target[attr_part.strip()]))
            return None

        target = element.select_one(selector)
        if target:
            if target.name == "a" and target.has_attr("href"):
                href_val = target["href"]
                if href_val.startswith("mailto:"):
                    return href_val.replace("mailto:", "").split("?")[0].strip()
                text_val = target.get_text(strip=True)
                if not text_val or text_val.lower() in {"website", "link", "url", "visit"} or href_val.startswith("http"):
                    if href_val.startswith("http") and "email" not in selector.lower():
                        return clean_text(href_val)
                return clean_text(text_val)
            return clean_text(target.get_text())
    except Exception:
        pass

    return None

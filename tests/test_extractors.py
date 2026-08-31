"""Unit tests for extractor utilities and lead scoring."""

import pytest
from bs4 import BeautifulSoup
from src.scraper.extractors import (
    extract_emails,
    extract_phones,
    normalize_domain,
    extract_linkedin_url,
    calculate_lead_score,
    extract_field_by_selector,
)


def test_extract_emails_standard_and_mailto():
    sample_text = "Contact our team at sales@enterprise.ai or support@enterprise.ai for info."
    emails = extract_emails(sample_text)
    assert "sales@enterprise.ai" in emails
    assert "support@enterprise.ai" in emails

    html_mailto = '<p>Reach out: <a href="mailto:ceo@startup.io">CEO Email</a></p>'
    emails_html = extract_emails(html_mailto)
    assert "ceo@startup.io" in emails_html


def test_extract_obfuscated_emails():
    sample = "Reach out at founder [at] nextgen [dot] tech or alex(at)domain(dot)io."
    emails = extract_emails(sample)
    assert "founder@nextgen.tech" in emails
    assert "alex@domain.io" in emails


def test_extract_phones():
    text = "Call US: +1 (555) 234-5678 or UK: +44 20 7946 0912 for inquiries."
    phones = extract_phones(text)
    assert len(phones) >= 1
    assert any("555" in p for p in phones)


def test_normalize_domain():
    assert normalize_domain("https://www.google.com/search?q=test") == "google.com"
    assert normalize_domain("http://sub.domain.co.uk/page") == "sub.domain.co.uk"
    assert normalize_domain("acme.ai") == "acme.ai"
    assert normalize_domain(None) is None


def test_extract_linkedin_url():
    text = "Founder profile: https://www.linkedin.com/in/satyanadella/ and company https://linkedin.com/company/microsoft."
    url = extract_linkedin_url(text)
    assert url is not None
    assert "linkedin.com" in url


def test_calculate_lead_score():
    score_full = calculate_lead_score(
        has_email=True,
        has_phone=True,
        has_contact_name=True,
        has_linkedin=True,
        has_domain=True,
    )
    assert score_full == 100

    score_partial = calculate_lead_score(
        has_email=True,
        has_phone=False,
        has_contact_name=False,
        has_linkedin=False,
        has_domain=True,
    )
    assert score_partial == 55


def test_extract_field_by_selector():
    html_doc = """
    <div class="card">
        <h3 class="biz-title">Apex Technologies, Inc.</h3>
        <p class="author">Dr. Robert Chen</p>
        <a href="mailto:robert@apextech.com" class="contact-email">Email</a>
    </div>
    """
    soup = BeautifulSoup(html_doc, "html.parser")
    title = extract_field_by_selector(soup, "h3.biz-title, .title")
    author = extract_field_by_selector(soup, ".author, .founder")
    email = extract_field_by_selector(soup, "a.contact-email")

    assert title == "Apex Technologies, Inc."
    assert author == "Dr. Robert Chen"
    assert email == "robert@apextech.com"

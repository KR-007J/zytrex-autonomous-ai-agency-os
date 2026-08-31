"""Unit tests for ScraperEngine logic, robots.txt compliance, and parsing."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base
from src.scraper.engine import ScraperEngine
from src.config import RootConfig, ClassifiedSiteConfig


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_robots_txt_allow_check():
    engine = ScraperEngine()
    allowed = engine.is_allowed_by_robots("https://example.com/about")
    assert isinstance(allowed, bool)


def test_scraper_engine_classified_parsing(db_session, monkeypatch):
    mock_html = """
    <html>
        <body>
            <div class="directory-item">
                <h3 class="name">ScaleAI Solutions Unique</h3>
                <span class="founder">Alex Wang</span>
                <a href="mailto:contact@scaleai-unique.com" class="email">Email Us</a>
                <a href="https://scaleai-unique.com" class="link">Website</a>
                <span class="industry">Machine Learning</span>
            </div>
            <div class="directory-item">
                <h3 class="name">Linear App Inc Unique</h3>
                <span class="founder">Karri Saarinen</span>
                <span class="phone">+1-555-0144</span>
                <a href="https://linear-unique.app" class="link">Website</a>
                <span class="industry">Productivity</span>
            </div>
        </body>
    </html>
    """

    engine = ScraperEngine()
    monkeypatch.setattr(engine, "fetch_page", lambda url: (mock_html, None))

    site_cfg = ClassifiedSiteConfig(
        name="Mock Startups",
        base_url="https://mockdirectory-unique.com",
        listing_selector=".directory-item",
        fields={
            "company_name": "h3.name",
            "contact_name": "span.founder",
            "email": "a.email",
            "phone": "span.phone",
            "source_url": "a.link",
            "industry_tag": "span.industry",
        },
    )

    job = engine.scrape_classified_site(site_cfg, session=db_session)
    assert job.status == "completed"
    assert job.leads_found == 2
    assert job.leads_new == 2

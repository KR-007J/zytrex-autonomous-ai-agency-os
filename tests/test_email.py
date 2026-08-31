"""Unit tests for Cold Email Dispatcher Engine."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base, Lead, OutreachDraft
from src.outreach.email_engine import ColdEmailEngine


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


def test_cold_email_dry_run():
    emailer = ColdEmailEngine()
    success, err = emailer.send_single_email(
        to_email="prospect@company.com",
        subject="Growth Partnership",
        body_text="Hi Prospect, let us connect.",
        dry_run=True,
    )
    assert success is True
    assert "Simulated" in err


def test_auto_email_campaign_batch(db_session):
    lead = Lead(
        company_name="HyperScale",
        contact_name="Elena Rostova",
        email="elena@hyperscale.com",
        industry_tag="AI SaaS",
        lead_score=85,
        status="new",
    )
    db_session.add(lead)
    db_session.commit()

    emailer = ColdEmailEngine()
    res = emailer.run_auto_outreach_campaign(
        session=db_session,
        max_emails=5,
        delay_seconds=0,
        dry_run=True,
    )

    assert res["sent"] == 1
    assert lead.status == "contacted"

    # Verify draft saved in database
    draft = db_session.query(OutreachDraft).filter(OutreachDraft.lead_id == lead.id).first()
    assert draft is not None
    assert draft.status == "sent"

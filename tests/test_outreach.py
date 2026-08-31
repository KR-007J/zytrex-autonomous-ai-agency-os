"""Unit tests for outreach personalization, manual-assist queue, and state transitions."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base, Lead, OutreachDraft, ContactedMemory
from src.outreach.personalizer import OutreachPersonalizer
from src.outreach.manual_assist import ManualAssistQueueManager
from src.config import RootConfig


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


def test_personalizer_template_rendering():
    personalizer = OutreachPersonalizer()
    lead = Lead(
        company_name="CloudMatrix",
        contact_name="Sarah Miller",
        industry_tag="Cybersecurity",
        source_domain="cloudmatrix.io",
    )

    draft = personalizer.generate_draft_for_lead(lead)
    assert "Sarah Miller" in draft["subject"] or "CloudMatrix" in draft["subject"]
    assert "Sarah Miller" in draft["personalized_message"]
    assert "CloudMatrix" in draft["personalized_message"]
    assert "Cybersecurity" in draft["personalized_message"]


def test_linkedin_search_url_generation():
    url = ManualAssistQueueManager.generate_linkedin_search_url("Datadog", "Olivier Pomel")
    assert "linkedin.com/search/results/people" in url
    assert "Datadog" in url
    assert "Olivier" in url


def test_manual_assist_queue_workflow(db_session):
    manager = ManualAssistQueueManager()

    # Create 2 uncontacted leads
    lead1 = Lead(company_name="Vercel", contact_name="Guillermo Rauch", email="g@vercel.com", lead_score=90)
    lead2 = Lead(company_name="Supabase", contact_name="Paul Copplestone", email="p@supabase.com", lead_score=85)
    db_session.add_all([lead1, lead2])
    db_session.commit()

    # Populate queue
    count = manager.populate_outreach_queue(db_session)
    assert count == 2

    # Verify queue retrieval
    queue = manager.get_queue(db_session)
    assert len(queue) == 2
    assert queue[0]["company_name"] in ["Vercel", "Supabase"]

    # Test approve draft
    draft_id = queue[0]["draft_id"]
    approved = manager.approve_draft(db_session, draft_id)
    assert approved is True

    # Test mark sent & record memory
    sent = manager.mark_draft_sent(db_session, draft_id, notes="Sent via LinkedIn Web")
    assert sent is True

    # Verify lead status updated to contacted
    lead_obj = db_session.query(Lead).filter(Lead.id == queue[0]["lead_id"]).first()
    assert lead_obj.status == "contacted"

    # Verify ContactedMemory record created
    memory = db_session.query(ContactedMemory).first()
    assert memory is not None

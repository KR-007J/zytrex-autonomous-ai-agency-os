"""Unit tests for deduplication, normalization, and memory persistence."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base, Lead, ContactedMemory
from src.database.db import LeadRepository
from src.scraper.dedupe import (
    normalize_company_name,
    normalize_lead_dict,
    is_already_contacted,
    record_contacted,
)


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


def test_normalize_company_name():
    assert normalize_company_name("Acme Corporation, Inc.") == "Acme"
    assert normalize_company_name("ScaleUp Technologies LLC") == "ScaleUp Technologies"
    assert normalize_company_name("Global Solutions Ltd.") == "Global Solutions"


def test_lead_repository_deduplication(db_session):
    lead_data_1 = {
        "company_name": "Stripe",
        "email": "contact@stripe.com",
        "source_domain": "stripe.com",
        "lead_score": 50,
    }
    lead1, is_new1 = LeadRepository.create_or_update(db_session, lead_data_1)
    db_session.commit()
    assert is_new1 is True

    # Same email and domain with extra phone info
    lead_data_2 = {
        "company_name": "Stripe, Inc.",
        "email": "contact@stripe.com",
        "phone": "+1-888-123-4567",
        "source_domain": "stripe.com",
        "lead_score": 85,
    }
    lead2, is_new2 = LeadRepository.create_or_update(db_session, lead_data_2)
    db_session.commit()

    assert is_new2 is False
    assert lead2.id == lead1.id
    assert lead2.phone == "+1-888-123-4567"
    assert lead2.lead_score == 85


def test_contacted_memory_check(db_session):
    assert is_already_contacted(db_session, email="founder@alpha.io") is False

    record_contacted(db_session, identifier="founder@alpha.io", notes="Sent connection request")
    db_session.commit()

    assert is_already_contacted(db_session, email="founder@alpha.io") is True
    assert is_already_contacted(db_session, domain="alpha.io") is False

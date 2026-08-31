"""Unit tests for Regional Agency Lead Discovery Engine."""

import pytest
from src.scraper.agency_engine import AgencyLeadDiscoveryEngine, US_REGIONS, TARGET_NICHES


def test_agency_dork_generation():
    engine = AgencyLeadDiscoveryEngine()
    dorks = engine.generate_regional_dorks(
        location="New York, NY",
        niche="Real Estate & Property Management",
        opportunity_type="web_redesign",
    )
    assert len(dorks) >= 2
    assert "New York" in dorks[0]
    assert "Real Estate" in dorks[0]


def test_agency_options():
    assert "New York, NY" in US_REGIONS
    assert "Austin, TX" in US_REGIONS
    assert "Healthcare & Medical Clinics" in TARGET_NICHES

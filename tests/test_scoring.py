from src.scoring.lead_scorer import LeadScorer

def test_hot_lead_scoring():
    res = LeadScorer.calculate(
        has_tech_match=True,
        tech_confidence=0.95,
        target_country_match=True,
        target_industry_match=True,
        has_public_email=True,
        has_public_phone=True,
        has_ssl=True,
        response_time_ms=450.0,
        is_live=True,
        freshness_status="LIVE",
        tech_name="OpenCart",
    )
    assert res.score >= 85
    assert res.label in ("HOT", "HIGH")
    assert any("OpenCart" in r for r in res.reasons)
    assert any("Public business email" in r for r in res.reasons)

def test_offline_lead_scoring():
    res = LeadScorer.calculate(
        has_tech_match=True,
        tech_confidence=0.95,
        target_country_match=True,
        target_industry_match=True,
        has_public_email=False,
        has_public_phone=False,
        has_ssl=False,
        response_time_ms=0.0,
        is_live=False,
        freshness_status="OFFLINE",
    )
    assert res.score <= 30
    assert res.label == "LOW"

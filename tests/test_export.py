from src.export.exporter import EnterpriseExporter

SAMPLE_LEADS = [
    {
        "id": 1,
        "business_name": "OpenCart UK Store",
        "domain": "opencart-uk.co.uk",
        "canonical_url": "https://opencart-uk.co.uk",
        "primary_technology": "OpenCart",
        "technology_confidence": 0.95,
        "status": "LIVE",
        "http_status": 200,
        "has_ssl": True,
        "country": "United Kingdom",
        "industry": "E-commerce",
        "primary_email": "info@opencart-uk.co.uk",
        "primary_phone": "+44 20 7946 0912",
        "lead_score": 95,
        "score_label": "HOT",
        "score_reasons": ["OpenCart confirmed", "Public email found"],
        "last_verified_at": "2026-09-07T12:00:00Z"
    }
]

def test_csv_export():
    csv_data = EnterpriseExporter.to_csv(SAMPLE_LEADS)
    assert "OpenCart UK Store" in csv_data
    assert "info@opencart-uk.co.uk" in csv_data
    assert "HOT" in csv_data

def test_xlsx_export():
    xlsx_bytes = EnterpriseExporter.to_xlsx(SAMPLE_LEADS)
    assert len(xlsx_bytes) > 1000
    assert xlsx_bytes[:4] == b"PK\x03\x04"  # Zip/Excel signature

def test_json_export():
    json_str = EnterpriseExporter.to_json(SAMPLE_LEADS)
    assert '"domain": "opencart-uk.co.uk"' in json_str

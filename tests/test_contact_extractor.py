from src.crawler.contact_extractor import ContactExtractor

def test_contact_extractor_html():
    html = """
    <html>
      <head>
        <title>Alpha Corp - Cloud Technology</title>
        <meta name="description" content="Leading enterprise cloud platform." />
      </head>
      <body>
        <h1>Welcome</h1>
        <p>Email us at <a href="mailto:info@alphacorp.com">info@alphacorp.com</a></p>
        <p>Or call us: <a href="tel:+18005550199">+1 (800) 555-0199</a></p>
        <a href="https://linkedin.com/company/alpha-corp">LinkedIn</a>
      </body>
    </html>
    """
    res = ContactExtractor.extract_from_html(html, "https://alphacorp.com")
    assert res["business_name"] == "Alpha"
    assert "Leading enterprise" in (res["description"] or "")
    assert len(res["emails"]) == 1
    assert res["emails"][0]["value"] == "info@alphacorp.com"
    assert res["emails"][0]["role_type"] == "ROLE_BASED"
    assert len(res["phones"]) == 1
    assert res["phones"][0]["value"] == "+18005550199"
    assert res["socials"]["linkedin"] == "https://linkedin.com/company/alpha-corp"

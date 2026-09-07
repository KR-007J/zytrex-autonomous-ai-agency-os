from src.fingerprint.engine import FingerprintEngine

def test_opencart_detection():
    html = """
    <html>
      <head>
        <meta name="generator" content="OpenCart 3.0.3.8" />
        <script src="catalog/view/javascript/common.js"></script>
        <link rel="stylesheet" href="catalog/view/theme/default/stylesheet/stylesheet.css" />
      </head>
      <body>
        <a href="index.php?route=common/home">Home</a>
      </body>
    </html>
    """
    cookies = {"OCSESSID": "abcdef123456789"}
    results = FingerprintEngine.detect(html=html, cookies=cookies)
    assert len(results) > 0
    top = results[0]
    assert top.tech_id == "opencart"
    assert top.confidence >= 0.70
    assert top.status == "CONFIRMED"
    assert len(top.evidence) >= 3

def test_shopify_detection():
    html = """
    <html>
      <head>
        <script src="https://cdn.shopify.com/s/files/1/0000/0000/t/1/assets/app.js"></script>
      </head>
      <body>
        <script>window.Shopify = { shop: "demo.myshopify.com" };</script>
      </body>
    </html>
    """
    headers = {"X-ShopId": "987654"}
    results = FingerprintEngine.detect(html=html, headers=headers)
    assert any(r.tech_id == "shopify" and r.status == "CONFIRMED" for r in results)

def test_insufficient_evidence():
    html = "<html><body><h1>Plain static landing page</h1></body></html>"
    results = FingerprintEngine.detect(html=html)
    assert len(results) == 0

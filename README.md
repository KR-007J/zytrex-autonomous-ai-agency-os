# ⚡ LeadForge — Enterprise Lead Intelligence SaaS

> **"Find businesses by the technology they use."**  
> *Zero mandatory paid APIs. Zero per-lead software credits. 100% open-source & self-hostable.*

---

## 🌟 Overview

LeadForge is a production-grade technology-driven lead intelligence platform. Rather than paying expensive monthly fees for opaque lead databases (Apollo, ZoomInfo, BuiltWith API), LeadForge continuously discovers candidate domains across public datasets, executes safe SSRF-protected DNS & HTTP verification, fingerprints underlying technologies using modular YAML signatures, extracts verified public contacts, and deterministically scores each business opportunity.

```
Candidate Discovery (Public Web, crt.sh, DNS)
   ↓
Live Verification (DNS + HTTP + SSL Check + Latency)
   ↓
Technology Fingerprinting (Modular YAML Signatures + Evidence Provenance)
   ↓
Public Contact Extraction (Mailto/Tel, JSON-LD, Socials)
   ↓
Deterministic Lead Qualification (0–100 Transparent Scoring)
   ↓
Enterprise Export (XLSX, CSV, JSON) & REST API
```

---

## 🚀 Quick Start (Local Development)

### 1. Requirements
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) or `pip`

### 2. Run Locally
```bash
# Clone and navigate
cd leadforge

# Install dependencies
uv sync # or pip install -e .

# Start the application server
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

Open **[http://localhost:8000](http://localhost:8000)** in your browser to view the live responsive UI.  
Interactive OpenAPI / Swagger documentation is available at **[http://localhost:8000/docs](http://localhost:8000/docs)**.

---

## 🐳 Docker Deployment

Run the complete stack in a single command:
```bash
docker compose up --build -d
```

---

## 🧪 Automated Testing

Run the full automated test suite covering SSRF protection, signature matching, live verification, contact extraction, scoring, export, and REST API:
```bash
pytest tests/ -v
```

---

## ⚖️ Zero-Cost Guarantee

LeadForge functions at **Zero External API Cost**:
- **NO** Apollo / Clearbit / ZoomInfo subscription required.
- **NO** BuiltWith / Wappalyzer paid API required.
- **NO** OpenAI / Anthropic credits required for core discovery and scoring.
- **NO** Proxy or paid CAPTCHA networks required.

*Throughput is constrained solely by local hardware, network bandwidth, and polite robots.txt crawl limits.*

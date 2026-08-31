# Enterprise Lead Generation & LinkedIn Outreach Agent

> **Enterprise-Grade Multi-Source Lead Discovery, Clean Normalization & 100% ToS-Compliant LinkedIn Manual-Assist Outreach Agent with Nous Hermes Agent Integration.**

---

## 🏛️ System Overview

This system is engineered to solve two fundamental problems in modern B2B go-to-market pipelines:
1. **Module 1 — Public Lead Discovery & Normalization**: Harvests leads from search engines (Google, Bing) and custom directory sites using dynamic CSS/XPath selectors. Automatically extracts public emails, phones, and domains, deduping against a local SQLite or PostgreSQL database.
2. **Module 2 — Compliant LinkedIn Outreach Agent**: Operates on a **100% ToS-compliant Manual-Assist model**. Uses contextual enrichment to craft personalized pitch drafts queued for human 1-click review and send in LinkedIn's native interface. **Zero ban risk, zero credential sharing, zero headless bot violations.**

---

## 🚀 Quick Start (3 Steps)

### 1. Installation

Run the single-line automated installer:
```bash
bash install.sh
```

Or install manually using `uv`:
```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e .
python -c "from src.database.db import init_db; init_db()"
```

### 2. Configuration (`config.yaml`)

All scraping parameters, target sites, CSS selectors, outreach templates, and notification webhooks are managed in a single, documented `config.yaml` file:

```yaml
scraping:
  rate_limiting:
    min_delay_seconds: 1.5
    max_delay_seconds: 3.5
    respect_robots_txt: true # Strict compliance flag
  search_engines:
    queries:
      - "B2B SaaS startup founders San Francisco email contact"
      - "Artificial Intelligence agency CEO contact"
  classified_sites:
    - name: "TechDir Startups"
      base_url: "https://news.ycombinator.com/item?id=38837130"
      listing_selector: ".athing, .comment"
      fields:
        company_name: ".titleline, .commtext strong"
        email: "a[href^='mailto:'], .email"
        phone: "a[href^='tel:'], .phone"

linkedin:
  mode: "manual_assist" # 'manual_assist' (Recommended) or 'official_api'
  templates:
    b2b_growth_pitch:
      name: "B2B Value Proposition Pitch"
      subject: "Quick question for {{ contact_name or company_name }}"
      body: "Hi {{ contact_name or 'there' }},\n\nNoticed {{ company_name }}'s work in {{ industry_tag }}..."
```

### 3. Execution

#### A. Enterprise Web Dashboard & REST API
Start the local FastAPI server and open the interactive dashboard:
```bash
./.venv/bin/python leadgen-skill/scripts/run_leadgen.py --mode serve --port 8000
```
Open **`http://localhost:8000`** in your browser to view:
- **Leads Explorer**: Search, filter, inspect lead scores, and export CSV.
- **Outreach Queue**: 1-Click "Open LinkedIn", "Copy Text", and "Mark Sent".
- **Scraper Studio**: Live test search queries, directory targets, and view run logs.
- **Settings Editor**: Modify `config.yaml` settings with live saving.

#### B. Autonomous CLI Modes
```bash
# Run ad-hoc search engine discovery
./.venv/bin/python leadgen-skill/scripts/run_leadgen.py --mode scrape --query "AI startup founders New York"

# Generate outreach drafts for top uncontacted leads
./.venv/bin/python leadgen-skill/scripts/run_leadgen.py --mode outreach --limit 25

# Dispatch daily summary report to Telegram / Slack / Email
./.venv/bin/python leadgen-skill/scripts/run_leadgen.py --mode report
```

---

## 🤖 Nous Research Hermes Agent Integration

The project is packaged as a standard Hermes skill (`leadgen-skill`) conforming to the `agentskills.io` specification.

### Using inside Hermes Agent
When running Hermes Agent (`hermes`):
- Run `/leadgen-scrape` or ask the agent: *"Find 10 B2B SaaS leads and queue outreach drafts"*.
- Hermes invokes `scripts/run_leadgen.py` directly, reads database state, and provides real-time progress.
- Configure Hermes cron jobs to run daily prospecting autonomously on a background server.

---

## 🔌 REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/stats` | High-level metrics (total leads, email count, queue depth) |
| `GET` | `/api/leads` | Paginated lead listing with search and status filters |
| `POST` | `/api/leads` | Create or import a new lead |
| `GET` | `/api/leads/export/csv` | Download complete leads database as CSV |
| `POST` | `/api/scrape/run` | Trigger scraper for custom query or classified site |
| `GET` | `/api/scrape/jobs` | View recent scrape job history and logs |
| `GET` | `/api/outreach/queue` | Retrieve pending manual-assist outreach queue |
| `POST` | `/api/outreach/mark-sent/{id}` | Mark draft as sent and record in permanent dedupe memory |
| `GET` | `/api/config` | Read current `config.yaml` |
| `PUT` | `/api/config` | Update and reload `config.yaml` |

---

## 🛡️ LinkedIn Compliance & Legal Architecture

To protect clients against LinkedIn account restrictions and CFAA liability:
- **No Headless Bots**: We strictly avoid simulating browser clicks or automated direct messages, which violate LinkedIn User Agreement Section 8.2.
- **Human-in-the-Loop 1-Click Clipboard**: The agent synthesizes context and queues personalized drafts. A human reviews the draft and clicks send natively in LinkedIn.
- **Official Lead Sync API**: For inbound sponsored lead forms, the system provides native OAuth integration with LinkedIn's official Marketing Developer Platform.
- View the complete 1-page compliance PDF deliverable at: `LinkedIn_ToS_Compliance_Architecture.pdf`.

---

## 🧪 Running Automated Tests

```bash
./.venv/bin/pytest tests/ -v
```

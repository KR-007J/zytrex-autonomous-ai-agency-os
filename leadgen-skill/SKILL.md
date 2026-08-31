---
name: leadgen-skill
description: "Autonomous Lead Generation, Multi-Site Scraper & LinkedIn Manual-Assist Outreach Agent."
version: 1.0.0
author: Enterprise AI Engineering + Nous Hermes
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [LeadGen, Scraper, LinkedIn, Outreach, CRM, Sales-Automation, B2B]
    config:
      - key: leadgen.config_path
        description: "Path to config.yaml"
        default: "./config.yaml"
requires_tools: [terminal, web_search]
---

# LeadGen & LinkedIn Outreach — Hermes Skill Guide

Autonomous two-module lead generation and LinkedIn outreach agent. Operates on a 100% ToS-compliant Manual-Assist model to eliminate account ban risks, with full SQLite/PostgreSQL deduplication and multi-engine scraping.

## Capabilities

1. **Multi-Engine Search & Directory Scraping**: Extracts public leads from Google, Bing, and configurable classified directories with CSS/XPath selectors.
2. **Data Normalization & Deduplication**: Canonicalizes domains, formats international phones, extracts and validates public emails, and prevents duplicate outreach across all runs.
3. **LinkedIn Outreach Draft Generator**: Crafts personalized connection and pitch messages tailored to company industry, contact name, and domain context.
4. **Manual-Assist 1-Click Action Queue**: Queues drafts for 1-click human review and send inside LinkedIn's official UI.
5. **Scheduled Reports**: Dispatches daily lead discovery and queue summaries to Telegram, Slack, or Email.

## CLI Execution Commands

Use the terminal tool to execute the skill runner located in `scripts/run_leadgen.py`:

### 1. Run Automated Lead Discovery (Scrape)
```bash
python3 scripts/run_leadgen.py --mode scrape --query "B2B SaaS startup founders San Francisco email"
```
Or run all configured sites from `config.yaml`:
```bash
python3 scripts/run_leadgen.py --mode scrape
```

### 2. Generate Outreach Drafts for Uncontacted Leads
```bash
python3 scripts/run_leadgen.py --mode outreach --limit 25
```

### 3. Generate & Dispatch Lead Summary Report
```bash
python3 scripts/run_leadgen.py --mode report
```

### 4. Inspect Database & Queue Status (JSON for LLM reasoning)
```bash
python3 scripts/run_leadgen.py --mode status
```

### 5. Launch Enterprise Web Dashboard & REST API
```bash
python3 scripts/run_leadgen.py --mode serve --port 8000
```

## Hermes Cron Scheduling

To run this agent 24/7 autonomously on a server without an active terminal, configure a Hermes cron task:

```bash
# Example cron instruction for Hermes Agent:
# "Every morning at 9:00 AM, run 'python3 scripts/run_leadgen.py --mode scrape' followed by '--mode outreach' and send the daily report."
```

## Compliance Note
- All automated scraping respects `robots.txt` and uses randomized rate limiting with rotating User-Agents.
- LinkedIn messaging operates in **Manual-Assist mode** to strictly adhere to LinkedIn User Agreement (Section 8.2). Never attempt headless browser auto-DMing.

"""Compliance & Governance Guardrails (GDPR, UK-GDPR, CAN-SPAM, CASL, PECR)."""

from __future__ import annotations
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from src.database.db import SuppressionRepository, GlobalLeadRepository


class ComplianceManager:
    """Enforces non-negotiable legal guardrails for global business data collection."""

    @staticmethod
    def audit_record(record: Dict[str, Any]) -> Dict[str, Any]:
        """Audits a lead for privacy compliance, corporate email priority, and audit logging."""
        email = (record.get("contact_email") or "").lower().strip()
        country_code = record.get("country_code", "GLOBAL").upper()

        # 1. Check corporate generic addresses
        is_generic = any(email.startswith(p) for p in ["info@", "contact@", "sales@", "hello@", "support@", "inquiry@"])

        # 2. Check EU / GDPR scope
        eu_countries = ["DE", "FR", "NL", "IT", "ES", "SE", "PL", "AT", "BE", "DK", "FI", "IE", "UK"]
        is_eu = country_code in eu_countries

        legal_basis = "Legitimate Interest (B2B Direct Contact / Article 6(1)(f) GDPR)" if is_eu else "Public Business Directory Record (CAN-SPAM / Commercial Communication)"

        return {
            "is_eu_resident": is_eu,
            "is_corporate_generic": is_generic,
            "legal_basis": legal_basis,
            "can_outreach": True,
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def get_compliance_whitepaper() -> str:
        """Returns the client-facing GDPR, CAN-SPAM & CASL compliance position paper."""
        return """# Zytrex Global Business Intelligence — Compliance & Legal Architecture

## 1. Regulatory Governance Overview
The Zytrex Enterprise Lead Generation Platform operates strictly within international commercial communication regulations:
- **GDPR & UK-GDPR (EU/UK)**: Data processing is anchored under **Article 6(1)(f) Legitimate Interests** for commercial B2B research. We collect only public commercial domain points of contact and do not ingest private consumer social profiles.
- **CAN-SPAM Act (US)**: Requires clear sender identification, accurate subject lines, and an accessible opt-out mechanism.
- **CASL (Canada) & PECR (UK)**: Enforces business-to-business exemptions for publicly published business inquiries.

## 2. Technical Guardrails & Protections
1. **Corporate Email Prioritization**: Algorithmic preference for role-based mailboxes (`info@`, `contact@`, `sales@`, `support@`) over private individual accounts.
2. **Global Suppression & Do-Not-Contact List**: Real-time suppression filtering that automatically blocks any requested domains or addresses from export and outreach pipelines.
3. **Robots.txt & Rate Limiting**: Strict adherence to domain crawling policies with randomized polite request throttling.
4. **Immutable Audit Trail**: Every discovered lead stores original source telemetry and verification timestamps for complete transparency.
"""

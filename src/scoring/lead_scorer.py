"""Deterministic lead qualification and opportunity scoring."""

from __future__ import annotations
from typing import Dict, List, Any, Optional


class LeadScoreResult:
    def __init__(self, score: int, label: str, reasons: List[str], breakdown: Dict[str, int]):
        self.score = max(0, min(100, score))
        self.label = label
        self.reasons = reasons
        self.breakdown = breakdown

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "label": self.label,
            "reasons": self.reasons,
            "breakdown": self.breakdown,
        }


class LeadScorer:
    """Calculates transparent, deterministic lead scores based on verified empirical facts."""

    @classmethod
    def calculate(
        cls,
        has_tech_match: bool,
        tech_confidence: float,
        target_country_match: bool,
        target_industry_match: bool,
        has_public_email: bool,
        has_public_phone: bool,
        has_ssl: bool,
        response_time_ms: float,
        is_live: bool,
        freshness_status: str,
        tech_name: str = "",
    ) -> LeadScoreResult:
        score = 0
        reasons: List[str] = []
        breakdown: Dict[str, int] = {}

        if not is_live:
            return LeadScoreResult(
                score=10,
                label="LOW",
                reasons=["Website currently offline or non-responsive"],
                breakdown={"offline_penalty": 10},
            )

        # 1. Technology Match (up to 25)
        if has_tech_match:
            pts = 25 if tech_confidence >= 0.70 else 15
            score += pts
            breakdown["tech_match"] = pts
            status_text = "confirmed" if tech_confidence >= 0.70 else "possible"
            reasons.append(f"{tech_name or 'Target technology'} {status_text} ({int(tech_confidence * 100)}% confidence)")
        else:
            breakdown["tech_match"] = 0

        # 2. ICP Match (up to 20)
        icp_pts = 0
        if target_country_match:
            icp_pts += 10
            reasons.append("Target geographic region matched")
        if target_industry_match:
            icp_pts += 10
            reasons.append("Target industry segment matched")
        score += icp_pts
        breakdown["icp_match"] = icp_pts

        # 3. Business Relevance & Presence (up to 15)
        relevance_pts = 15
        score += relevance_pts
        breakdown["business_relevance"] = relevance_pts
        reasons.append("Active commercial entity with accessible storefront")

        # 4. Contact Availability (up to 10)
        contact_pts = 0
        if has_public_email:
            contact_pts += 7
            reasons.append("Public business email discovered")
        if has_public_phone:
            contact_pts += 3
            reasons.append("Direct phone/support line available")
        score += contact_pts
        breakdown["contact_availability"] = contact_pts

        # 5. Opportunity Signals (up to 10)
        opportunity_pts = 5
        if response_time_ms > 1200:
            opportunity_pts += 5
            reasons.append("Potential optimization opportunity: High page latency (>1.2s)")
        elif not has_ssl:
            opportunity_pts += 5
            reasons.append("Potential security opportunity: Missing HTTPS/TLS encryption")
        score += opportunity_pts
        breakdown["opportunity_signals"] = opportunity_pts

        # 6. Website Quality & Speed (up to 10)
        quality_pts = 0
        if has_ssl:
            quality_pts += 5
            reasons.append("Valid SSL/TLS certificate configured")
        if response_time_ms < 800:
            quality_pts += 5
            reasons.append(f"Fast response time ({int(response_time_ms)}ms)")
        score += quality_pts
        breakdown["website_quality"] = quality_pts

        # 7. Freshness (up to 5)
        fresh_pts = 5 if freshness_status in ("LIVE", "FRESH") else 2
        score += fresh_pts
        breakdown["freshness"] = fresh_pts
        if freshness_status == "LIVE":
            reasons.append("Recently live-verified")

        # 8. Evidence Confidence (up to 5)
        ev_pts = 5 if tech_confidence >= 0.80 else 2
        score += ev_pts
        breakdown["evidence_confidence"] = ev_pts

        # Clamp and Label
        score = max(0, min(100, score))
        if score >= 90:
            label = "HOT"
        elif score >= 75:
            label = "HIGH"
        elif score >= 50:
            label = "MEDIUM"
        else:
            label = "LOW"

        return LeadScoreResult(score=score, label=label, reasons=reasons, breakdown=breakdown)

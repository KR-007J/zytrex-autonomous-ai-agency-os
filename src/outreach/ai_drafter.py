"""Autonomous AI Outreach Sequence Engine.

Generates hyper-personalized, high-converting 3-step cold email sequences
based on real-time technology fingerprinting, server telemetry, and forensic evidence.
Modeled after Apollo.io and Clay.com sales automation standards.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class OutreachSequence(BaseModel):
    subject_lines: List[str] = Field(default_factory=list)
    step1_hook_email: str
    step2_followup_email: str
    step3_breakup_email: str
    technical_audit_summary: str
    recommended_offer: str
    pain_points_identified: List[str] = Field(default_factory=list)


class OutreachDrafter:
    """Generates structured 1-to-1 cold outreach sequences tailored to detected stack forensics."""

    @classmethod
    def draft_sequence(
        cls,
        domain: str,
        business_name: Optional[str] = None,
        primary_technology: Optional[str] = None,
        country: Optional[str] = None,
        industry: Optional[str] = None,
        response_time_ms: float = 0.0,
        evidence: Optional[List[str]] = None,
        tone: str = "direct",  # "direct", "consultative", "founder"
    ) -> OutreachSequence:
        domain = (domain or "").lower().strip()
        b_name = business_name or domain.split(".")[0].capitalize()
        tech = (primary_technology or "Modern Web Stack").strip()
        tech_lower = tech.lower()
        country_str = f" in {country}" if country else ""
        evidence_list = evidence or []
        evidence_str = f" (detected via {evidence_list[0]})" if evidence_list else ""

        # Identify key technical pain points based on tech and latency
        pain_points = []
        if response_time_ms > 400:
            pain_points.append(f"Server response latency is {response_time_ms:.1f}ms (ideal is <200ms)")
        if "opencart" in tech_lower:
            pain_points.append("Legacy PHP MVC routing structure with potential checkout friction")
            pain_points.append("Higher vulnerability profile compared to modern cloud-hosted checkouts")
        elif "shopify" in tech_lower:
            pain_points.append("Third-party JavaScript app script bloat impacting Core Web Vitals")
            pain_points.append("Cart abandonment on non-customized mobile checkout steps")
        elif "woocommerce" in tech_lower:
            pain_points.append("Database query bloat on large product catalog queries")
            pain_points.append("Shared hosting resource contention during peak traffic")
        elif "magento" in tech_lower:
            pain_points.append("Heavy maintenance overhead and slow catalog indexing")
        else:
            pain_points.append("Unoptimized frontend bundle delivery and potential conversion drop-off")

        # Select copy strategies based on tone
        if tone == "founder":
            subjs = [
                f"{domain} + tech stack thoughts",
                f"Quick question about {domain}'s checkout",
                f"Hey {b_name} team — {tech} performance observation",
            ]
            step1 = (
                f"Hey team at {b_name},\n\n"
                f"I came across {domain} while researching high-performing brands{country_str} and loved what you have built. "
                f"As a technical founder, I ran a quick architectural audit on your storefront and noticed you are currently running on {tech}{evidence_str}.\n\n"
                f"Your site is currently clocking a response time of {response_time_ms:.0f}ms. On {tech}, we typically see that optimizing the asset bundle and checkout pipeline recovers 8–14% of abandoned carts on mobile.\n\n"
                f"Would it be helpful if I sent over a short 3-bullet breakdown of how other {tech} stores shaved 300ms off their load time without redesigning the site?\n\n"
                f"Best,\n"
                f"Growth & Engineering Team"
            )
            step2 = (
                f"Hey team,\n\n"
                f"Following up on my note regarding {domain}. "
                f"We recently helped another brand running {tech} optimize their mobile checkout flow and saw an immediate 11.2% lift in completed transactions within 14 days.\n\n"
                f"Happy to share the exact teardown notes with your lead developer or ops team if you are exploring conversion optimizations this quarter.\n\n"
                f"Best,\n"
                f"Growth & Engineering Team"
            )
            step3 = (
                f"Hey team,\n\n"
                f"Assuming your tech roadmap for {domain} is fully locked in right now, so I will respectfully back off. "
                f"If you ever want a fresh technical pair of eyes on {tech} scaling or checkout performance down the road, feel free to keep this thread handy.\n\n"
                f"Wishing {b_name} continued growth!\n\n"
                f"Best,\n"
                f"Growth & Engineering Team"
            )
        elif tone == "consultative":
            subjs = [
                f"Technical evaluation for {b_name} ({domain})",
                f"Architectural insights: {tech} implementation at {domain}",
                f"Optimization roadmap for {b_name}",
            ]
            step1 = (
                f"Dear {b_name} Leadership,\n\n"
                f"I am writing to you following an automated technical inspection of {domain}. "
                f"Our systems confirmed that your storefront is powered by {tech} with a baseline latency of {response_time_ms:.1f}ms.\n\n"
                f"While your catalog presentation is compelling, our benchmark indicates key operational opportunities:\n"
                f"• {pain_points[0] if pain_points else 'Frontend asset optimization'}\n"
                f"• Opportunity to enhance mobile checkout throughput by up to 12%\n\n"
                f"We have prepared a complimentary 1-page Technical Architecture Teardown specific to your {tech} deployment. Would you be open to reviewing it this Thursday?\n\n"
                f"Sincerely,\n"
                f"Lead Intelligence & Optimization Practice"
            )
            step2 = (
                f"Dear {b_name} Team,\n\n"
                f"Checking in regarding our technical evaluation of {domain}. "
                f"Ensuring peak checkout efficiency on {tech} is critical heading into peak commercial cycles.\n\n"
                f"If you are the right person to review our benchmark comparison against top quartile {industry or 'commercial'} storefronts, I would be glad to forward the dossier.\n\n"
                f"Best regards,\n"
                f"Lead Intelligence Practice"
            )
            step3 = (
                f"Dear {b_name} Team,\n\n"
                f"I recognize your schedule is demanding. I will pause our outreach regarding {domain}'s {tech} infrastructure. "
                f"Please let me know if technical performance optimization becomes an initiative in future planning.\n\n"
                f"Best regards,\n"
                f"Lead Intelligence Practice"
            )
        else:  # Direct (Apollo default standard)
            subjs = [
                f"Idea for {domain}'s {tech} stack",
                f"{b_name} — quick technical observation",
                f"Improving checkout speed on {domain}",
            ]
            step1 = (
                f"Hi {b_name} team,\n\n"
                f"Notice you are running {domain} on {tech} with a current server response time of {response_time_ms:.0f}ms.\n\n"
                f"We specialize in helping {tech} brands eliminate mobile checkout drop-offs caused by {pain_points[0] if pain_points else 'unoptimized scripts'}. "
                f"Our clients typically see an immediate 10–15% increase in checkout completions without migrating platforms.\n\n"
                f"Open to a quick 5-minute chat this week to see the audit?\n\n"
                f"Thanks,\n"
                f"LeadForge Studio Intelligence"
            )
            step2 = (
                f"Hi team,\n\n"
                f"Quick follow-up on my note regarding {domain}. "
                f"Did you get a chance to review the {tech} speed metrics I mentioned? "
                f"Even shaving 200ms off your first contentful paint can move the needle on paid ad ROI.\n\n"
                f"Let me know if you would like me to send the full technical breakdown.\n\n"
                f"Thanks,\n"
                f"LeadForge Studio Intelligence"
            )
            step3 = (
                f"Hi team,\n\n"
                f"I know you are busy running {b_name}. I will close out this conversation for now. "
                f"If you ever need help fine-tuning {domain}'s {tech} performance or scaling your conversion funnel, you have my contact.\n\n"
                f"All the best,\n"
                f"LeadForge Studio Intelligence"
            )

        audit_summary = (
            f"Target {domain} is confirmed active on {tech} ({response_time_ms:.1f}ms latency). "
            f"Identified {len(pain_points)} primary optimization levers: {'; '.join(pain_points)}."
        )
        recommended_offer = (
            f"Offer complimentary 5-minute {tech} technical audit focusing on mobile checkout speed and asset consolidation."
        )

        return OutreachSequence(
            subject_lines=subjs,
            step1_hook_email=step1,
            step2_followup_email=step2,
            step3_breakup_email=step3,
            technical_audit_summary=audit_summary,
            recommended_offer=recommended_offer,
            pain_points_identified=pain_points,
        )

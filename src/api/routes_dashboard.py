"""Dashboard and SaaS Analytics API routes."""

from __future__ import annotations
from fastapi import APIRouter
from sqlalchemy import func, desc, or_
from src.database.db import get_db
from src.database.models import Lead, LeadEvent, AuditLog, DiscoveryJob, ExportJob

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/analytics")
def get_dashboard_analytics():
    with get_db() as session:
        # Summary counts
        total_leads = session.query(Lead).count()
        live_leads = session.query(Lead).filter(Lead.status == "LIVE").count()
        hot_leads = session.query(Lead).filter(Lead.lead_score >= 80).count()
        leads_with_email = session.query(Lead).filter(Lead.primary_email.isnot(None), Lead.primary_email != "").count()
        leads_with_phone = session.query(Lead).filter(Lead.primary_phone.isnot(None), Lead.primary_phone != "").count()
        ssl_leads = session.query(Lead).filter(Lead.has_ssl.is_(True)).count()

        # Averages
        avg_score_res = session.query(func.avg(Lead.lead_score)).scalar() or 0.0
        avg_score = round(float(avg_score_res), 1)

        avg_latency_res = session.query(func.avg(Lead.response_time_ms)).scalar() or 0.0
        avg_latency = round(float(avg_latency_res), 1)

        # Top Technologies Distribution
        tech_query = session.query(
            Lead.primary_technology, func.count(Lead.id).label("count")
        ).filter(Lead.primary_technology.isnot(None)).group_by(
            Lead.primary_technology
        ).order_by(desc("count")).limit(12).all()

        technologies = [{"name": t[0], "count": t[1]} for t in tech_query if t[0]]

        # Top Countries Distribution
        geo_query = session.query(
            Lead.country, func.count(Lead.id).label("count")
        ).filter(Lead.country.isnot(None)).group_by(
            Lead.country
        ).order_by(desc("count")).limit(10).all()

        geography = [{"country": g[0] or "Global", "count": g[1]} for g in geo_query]

        # Score Tiers
        tier_90_100 = session.query(Lead).filter(Lead.lead_score >= 90).count()
        tier_80_89 = session.query(Lead).filter(Lead.lead_score >= 80, Lead.lead_score < 90).count()
        tier_60_79 = session.query(Lead).filter(Lead.lead_score >= 60, Lead.lead_score < 80).count()
        tier_below_60 = session.query(Lead).filter(Lead.lead_score < 60).count()

        score_distribution = {
            "90_100": tier_90_100,
            "80_89": tier_80_89,
            "60_79": tier_60_79,
            "below_60": tier_below_60,
        }

        # Recent Activity Stream
        recent_events = session.query(LeadEvent).order_by(
            desc(LeadEvent.created_at)
        ).limit(10).all()

        activity_stream = [e.to_dict() for e in recent_events]
        if not activity_stream:
            # Fallback to recent audit logs or recent leads
            recent_leads = session.query(Lead).order_by(desc(Lead.last_verified_at)).limit(8).all()
            for rl in recent_leads:
                activity_stream.append({
                    "event_type": "lead.verified",
                    "lead_domain": rl.domain,
                    "details": {"technology": rl.primary_technology, "score": rl.lead_score},
                    "created_at": rl.last_verified_at.isoformat() if rl.last_verified_at else None,
                })

        # Registered Discovery Providers
        from src.discovery.orchestrator import orchestrator
        providers = [
            {
                "id": p.name.lower().replace(" ", "_").replace(".", "_"),
                "name": p.name,
                "status": "active",
                "type": p.__class__.__name__,
            }
            for p in orchestrator.providers
        ]

        recent_leads = [
            l.to_dict()
            for l in session.query(Lead).order_by(desc(Lead.last_verified_at)).limit(10).all()
        ]

        return {
            "summary": {
                "total_leads": total_leads,
                "live_leads": live_leads,
                "hot_leads": hot_leads,
                "leads_with_email": leads_with_email,
                "leads_with_phone": leads_with_phone,
                "ssl_leads": ssl_leads,
                "average_score": avg_score,
                "average_latency_ms": avg_latency,
            },
            "technologies": technologies,
            "geography": geography,
            "score_distribution": score_distribution,
            "activity_stream": activity_stream,
            "providers": providers,
            "recent_leads": recent_leads,
        }

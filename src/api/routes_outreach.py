"""API endpoints for AI Outreach Sequences and CRM Webhook Synchronization."""

from __future__ import annotations
import json
import logging
import httpx
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from src.database.db import get_db
from src.database.models import Lead
from src.outreach.ai_drafter import OutreachDrafter, OutreachSequence

logger = logging.getLogger("leadforge.api.outreach")

router = APIRouter(prefix="/outreach", tags=["Outreach Automation"])


class DraftOutreachRequest(BaseModel):
    lead_id: Optional[int] = None
    domain: Optional[str] = None
    business_name: Optional[str] = None
    primary_technology: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    response_time_ms: float = 0.0
    evidence: List[str] = Field(default_factory=list)
    tone: str = "direct"  # "direct", "consultative", "founder"


class WebhookSyncRequest(BaseModel):
    webhook_url: str
    lead_id: int
    step: int = 1
    custom_notes: Optional[str] = None


@router.post("/draft", response_model=OutreachSequence)
async def draft_outreach_sequence(req: DraftOutreachRequest):
    """Generate a hyper-personalized 3-step outreach sequence tailored to target stack forensics."""
    domain = req.domain
    business_name = req.business_name
    tech = req.primary_technology
    country = req.country
    industry = req.industry
    response_time = req.response_time_ms
    evidence = req.evidence or []

    # If lead_id provided, look up lead in database for authoritative data
    if req.lead_id:
        with get_db() as session:
            lead = session.query(Lead).filter(Lead.id == req.lead_id).first()
            if not lead:
                raise HTTPException(status_code=404, detail=f"Lead #{req.lead_id} not found")
            domain = domain or lead.domain
            business_name = business_name or lead.business_name or lead.domain
            tech = tech or lead.primary_technology or "Modern Web Stack"
            country = country or lead.country
            industry = industry or lead.industry
            response_time = lead.response_time_ms or response_time
            if not evidence and lead.evidence_json:
                try:
                    evidence = json.loads(lead.evidence_json)
                except Exception:
                    evidence = []

    if not domain:
        raise HTTPException(status_code=400, detail="Domain or valid lead_id is required")

    sequence = OutreachDrafter.draft_sequence(
        domain=domain,
        business_name=business_name,
        primary_technology=tech,
        country=country,
        industry=industry,
        response_time_ms=response_time,
        evidence=evidence,
        tone=req.tone,
    )
    return sequence


@router.post("/webhook-sync")
async def sync_lead_to_webhook(req: WebhookSyncRequest):
    """Sync lead and generated outreach sequence to external webhook (Instantly, Lemlist, CRM)."""
    with get_db() as session:
        lead = session.query(Lead).filter(Lead.id == req.lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail=f"Lead #{req.lead_id} not found")

        sequence = OutreachDrafter.draft_sequence(
            domain=lead.domain,
            business_name=lead.business_name,
            primary_technology=lead.primary_technology,
            country=lead.country,
            industry=lead.industry,
            response_time_ms=lead.response_time_ms,
        )

        payload = {
            "event": "leadforge.outreach_ready",
            "lead": lead.to_dict(),
            "selected_step": req.step,
            "subject": sequence.subject_lines[0] if sequence.subject_lines else "",
            "body": sequence.step1_hook_email if req.step == 1 else (
                sequence.step2_followup_email if req.step == 2 else sequence.step3_breakup_email
            ),
            "custom_notes": req.custom_notes,
        }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(req.webhook_url, json=payload)
            return {
                "success": resp.is_success,
                "status_code": resp.status_code,
                "message": "Lead payload dispatched successfully",
            }
    except Exception as e:
        logger.error(f"Failed to deliver webhook to {req.webhook_url}: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to dispatch to external webhook: {str(e)}")

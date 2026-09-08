"""Leads Intelligence and Refresh API routes."""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel
from src.database.db import get_db
from src.database.repository import LeadRepository
from src.jobs.manager import JobManager

router = APIRouter(prefix="/leads", tags=["Leads"])


class ImportDomainsRequest(BaseModel):
    domains: List[str]
    technology_hint: Optional[str] = None
    country_hint: Optional[str] = None


@router.get("")
def list_leads(
    technology: Optional[str] = None,
    country: Optional[str] = None,
    industry: Optional[str] = None,
    status: Optional[str] = None,
    has_email: Optional[bool] = None,
    min_score: Optional[int] = None,
    query: Optional[str] = None,
    limit: int = Query(25, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("score", pattern="^(score|recent|domain)$"),
):
    with get_db() as session:
        items, total = LeadRepository.query_leads(
            session=session,
            technology=technology,
            country=country,
            industry=industry,
            status=status,
            has_email=has_email,
            min_score=min_score,
            query=query,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
        )
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "leads": [lead.to_dict() for lead in items],
        }


@router.get("/{lead_id}")
def get_lead_detail(lead_id: int):
    with get_db() as session:
        lead = LeadRepository.get_lead_by_id(session, lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        data = lead.to_dict()
        data["events"] = [e.to_dict() for e in lead.events]
        return data


@router.post("/{lead_id}/refresh")
async def refresh_single_lead(lead_id: int):
    updated = await JobManager.refresh_lead(lead_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"status": "REFRESHED", "lead": updated}

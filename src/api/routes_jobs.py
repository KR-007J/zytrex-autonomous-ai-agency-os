"""Unified Background Jobs API routes."""

from __future__ import annotations
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import desc
from src.database.db import get_db
from src.database.models import DiscoveryJob, ExportJob
from src.export.async_exporter import AsyncExportManager

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("")
def list_all_jobs(
    job_type: Optional[str] = None,  # discovery, export
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
):
    results: List[dict] = []
    with get_db() as session:
        if not job_type or job_type == "discovery":
            q_disc = session.query(DiscoveryJob)
            if status:
                q_disc = q_disc.filter(DiscoveryJob.status == status.upper())
            for d in q_disc.order_by(desc(DiscoveryJob.created_at)).limit(limit).all():
                item = d.to_dict()
                item["job_type"] = "discovery"
                item["description"] = f"Discover {d.technology} in {d.country or 'Global'}"
                results.append(item)

        if not job_type or job_type == "export":
            q_exp = session.query(ExportJob)
            if status:
                q_exp = q_exp.filter(ExportJob.status == status.upper())
            for e in q_exp.order_by(desc(ExportJob.created_at)).limit(limit).all():
                item = e.to_dict()
                item["job_type"] = "export"
                item["description"] = f"Export {e.format.upper()} ({e.row_count} records)"
                results.append(item)

    # Sort unified results by created_at descending
    results.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return results[:limit]


@router.get("/{job_id}")
def get_job(job_id: str):
    with get_db() as session:
        disc = session.query(DiscoveryJob).filter(DiscoveryJob.id == job_id).first()
        if disc:
            item = disc.to_dict()
            item["job_type"] = "discovery"
            return item

        exp = session.query(ExportJob).filter(ExportJob.id == job_id).first()
        if exp:
            item = exp.to_dict()
            item["job_type"] = "export"
            return item

    raise HTTPException(status_code=404, detail="Job not found")

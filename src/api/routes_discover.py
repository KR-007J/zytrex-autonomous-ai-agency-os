"""Discovery and Streaming API routes."""

from fastapi import APIRouter, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from src.jobs.manager import JobManager
from src.jobs.sse import broadcaster
from src.database.db import get_db
from src.database.models import DiscoveryJob

router = APIRouter(prefix="/discover", tags=["Discovery"])


class DiscoverRequest(BaseModel):
    technology: str
    country: Optional[str] = None
    industry: Optional[str] = None
    require_email: bool = False
    limit: int = 20
    replace_existing: bool = False


@router.post("")
async def start_discovery(req: DiscoverRequest):
    job_id = await JobManager.start_discovery_job(
        technology=req.technology,
        country=req.country,
        industry=req.industry,
        require_email=req.require_email,
        limit=req.limit,
        replace_existing=req.replace_existing,
    )
    return {
        "job_id": job_id,
        "status": "RUNNING",
        "stream_url": f"/api/v1/discover/{job_id}/stream",
    }


@router.get("/{job_id}")
def get_discovery_status(job_id: str):
    with get_db() as session:
        job = session.query(DiscoveryJob).filter(DiscoveryJob.id == job_id).first()
        if not job:
            return {"error": "Job not found"}
        return job.to_dict()


@router.get("/{job_id}/stream")
async def stream_discovery_events(job_id: str):
    return StreamingResponse(
        broadcaster.subscribe(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

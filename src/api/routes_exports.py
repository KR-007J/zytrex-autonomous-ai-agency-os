"""Export API routes."""

from fastapi import APIRouter, Response, Query
from typing import Optional
from src.database.db import get_db
from src.database.repository import LeadRepository
from src.export.exporter import EnterpriseExporter

router = APIRouter(prefix="/exports", tags=["Exports"])


@router.get("/csv")
def export_csv(
    technology: Optional[str] = None,
    country: Optional[str] = None,
    min_score: Optional[int] = None,
):
    with get_db() as session:
        leads, _ = LeadRepository.query_leads(
            session, technology=technology, country=country, min_score=min_score, limit=5000
        )
        raw_list = [l.to_dict() for l in leads]
        csv_data = EnterpriseExporter.to_csv(raw_list)

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="leadforge_leads.csv"'},
    )


@router.get("/xlsx")
def export_xlsx(
    technology: Optional[str] = None,
    country: Optional[str] = None,
    min_score: Optional[int] = None,
):
    with get_db() as session:
        leads, _ = LeadRepository.query_leads(
            session, technology=technology, country=country, min_score=min_score, limit=5000
        )
        raw_list = [l.to_dict() for l in leads]
        xlsx_bytes = EnterpriseExporter.to_xlsx(raw_list)

    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="leadforge_leads.xlsx"'},
    )


@router.get("/json")
def export_json(
    technology: Optional[str] = None,
    country: Optional[str] = None,
    min_score: Optional[int] = None,
):
    with get_db() as session:
        leads, _ = LeadRepository.query_leads(
            session, technology=technology, country=country, min_score=min_score, limit=5000
        )
        raw_list = [l.to_dict() for l in leads]
        json_str = EnterpriseExporter.to_json(raw_list)

    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="leadforge_leads.json"'},
    )


@router.get("/markdown")
def export_markdown(
    technology: Optional[str] = None,
    country: Optional[str] = None,
    min_score: Optional[int] = None,
):
    with get_db() as session:
        leads, _ = LeadRepository.query_leads(
            session, technology=technology, country=country, min_score=min_score, limit=5000
        )
        raw_list = [l.to_dict() for l in leads]
        md_str = EnterpriseExporter.to_markdown(raw_list)

    return Response(
        content=md_str,
        media_type="text/markdown",
        headers={"Content-Disposition": 'attachment; filename="leadforge_leads.md"'},
    )


@router.get("/pdf")
def export_pdf(
    technology: Optional[str] = None,
    country: Optional[str] = None,
    min_score: Optional[int] = None,
):
    with get_db() as session:
        leads, _ = LeadRepository.query_leads(
            session, technology=technology, country=country, min_score=min_score, limit=5000
        )
        raw_list = [l.to_dict() for l in leads]
        pdf_bytes = EnterpriseExporter.to_pdf(raw_list)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="leadforge_leads.pdf"'},
    )


@router.get("/parquet")
def export_parquet(
    technology: Optional[str] = None,
    country: Optional[str] = None,
    min_score: Optional[int] = None,
):
    with get_db() as session:
        leads, _ = LeadRepository.query_leads(
            session, technology=technology, country=country, min_score=min_score, limit=5000
        )
        raw_list = [l.to_dict() for l in leads]
        parquet_bytes = EnterpriseExporter.to_parquet(raw_list)

    return Response(
        content=parquet_bytes,
        media_type="application/octet-stream",
        headers={"Content-Disposition": 'attachment; filename="leadforge_leads.parquet"'},
    )


# --- Async Export Jobs ---

from pydantic import BaseModel
from src.export.async_exporter import AsyncExportManager


class AsyncExportJobRequest(BaseModel):
    format: str  # CSV, XLSX, JSON, JSONL, PARQUET, MD, PDF
    technology: Optional[str] = None
    country: Optional[str] = None
    industry: Optional[str] = None
    status: Optional[str] = None
    has_email: Optional[bool] = None
    min_score: Optional[int] = None
    query: Optional[str] = None
    limit: Optional[int] = 5000


@router.post("/jobs")
def create_export_job(req: AsyncExportJobRequest):
    filters = {
        "technology": req.technology,
        "country": req.country,
        "industry": req.industry,
        "status": req.status,
        "has_email": req.has_email,
        "min_score": req.min_score,
        "query": req.query,
    }
    job_id = AsyncExportManager.start_export_job(
        export_format=req.format,
        filters=filters,
        limit=req.limit or 5000,
    )
    job = AsyncExportManager.get_export_job(job_id)
    return job or {"id": job_id, "status": "PENDING"}


@router.get("/jobs")
def list_export_jobs(limit: int = Query(50, ge=1, le=100)):
    return AsyncExportManager.list_export_jobs(limit=limit)


@router.get("/jobs/{job_id}")
def get_export_job_status(job_id: str):
    from fastapi import HTTPException
    job = AsyncExportManager.get_export_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    return job


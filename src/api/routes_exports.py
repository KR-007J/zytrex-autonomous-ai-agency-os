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

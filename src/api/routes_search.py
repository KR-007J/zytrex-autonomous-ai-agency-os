"""Natural Language Search API routes."""

from __future__ import annotations
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from src.search.nl_parser import NLSearchParser, ParsedSearchFilters
from src.database.db import get_db
from src.database.repository import LeadRepository


router = APIRouter(prefix="/search", tags=["Search"])


class SearchParseRequest(BaseModel):
    query: str


@router.get("/parse")
def parse_search_query_get(q: str = Query(..., min_length=1, description="Natural language search query")):
    filters = NLSearchParser.parse(q)
    return filters.to_dict()


@router.post("/parse")
def parse_search_query_post(req: SearchParseRequest):
    filters = NLSearchParser.parse(req.query)
    return filters.to_dict()


@router.get("/execute")
def execute_natural_search(
    q: str = Query(..., min_length=1, description="Natural language query to parse and execute"),
    limit: int = Query(25, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("score", pattern="^(score|recent|domain)$"),
):
    parsed = NLSearchParser.parse(q)

    with get_db() as session:
        leads, total = LeadRepository.query_leads(
            session=session,
            technology=parsed.technology,
            country=parsed.country,
            industry=parsed.industry,
            status=parsed.status,
            has_email=parsed.has_email,
            min_score=parsed.min_score,
            query=parsed.remaining_query,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
        )

        return {
            "parsed_filters": parsed.to_dict(),
            "total": total,
            "limit": limit,
            "offset": offset,
            "leads": [l.to_dict() for l in leads],
        }

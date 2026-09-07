"""Technology Catalog API routes."""

from fastapi import APIRouter
from src.fingerprint.signature_loader import registry
from src.database.db import get_db
from src.database.models import Lead
from sqlalchemy import func, desc

router = APIRouter(prefix="/technologies", tags=["Technologies"])


@router.get("")
def list_technologies():
    signatures = registry.all()
    with get_db() as session:
        counts = dict(
            session.query(Lead.primary_technology, func.count(Lead.id))
            .filter(Lead.primary_technology.isnot(None))
            .group_by(Lead.primary_technology)
            .all()
        )

    return [
        {
            "id": sig.id,
            "name": sig.name,
            "category": sig.category,
            "description": sig.description,
            "website": sig.website,
            "confidence_threshold": sig.confidence_threshold,
            "verified_leads_count": counts.get(sig.name, 0),
            "patterns_count": sum(len(v) for v in sig.patterns.values()),
        }
        for sig in signatures
    ]

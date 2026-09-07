"""Health and Statistics API routes."""

from fastapi import APIRouter
from src.config import settings
from src.database.db import get_db
from src.database.repository import LeadRepository
from src.fingerprint.signature_loader import registry

router = APIRouter(tags=["System"])


@router.get("/health")
def get_health():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "zero_cost_mode": True,
        "active_signatures": len(registry.all()),
    }


@router.get("/stats")
def get_stats():
    with get_db() as session:
        return LeadRepository.get_stats(session)

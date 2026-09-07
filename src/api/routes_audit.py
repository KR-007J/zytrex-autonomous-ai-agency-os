"""Audit Logs API routes."""

from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Query
from sqlalchemy import desc
from src.database.db import get_db
from src.database.models import AuditLog
from src.security.auth import seed_default_data

router = APIRouter(prefix="/audit-logs", tags=["Audit"])


@router.get("")
def list_audit_logs(
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    with get_db() as session:
        org, _ = seed_default_data(session)
        q = session.query(AuditLog).filter(
            (AuditLog.organization_id == org.id) | (AuditLog.organization_id.is_(None))
        )
        if action:
            q = q.filter(AuditLog.action.ilike(f"%{action}%"))
        if resource_type:
            q = q.filter(AuditLog.resource_type == resource_type)

        total = q.count()
        logs = q.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "audit_logs": [l.to_dict() for l in logs],
        }

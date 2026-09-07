"""Webhooks Management and Test Ping API routes."""

from __future__ import annotations
import secrets
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, HttpUrl

from src.database.db import get_db
from src.database.models import Webhook, WebhookDelivery
from src.webhooks.dispatcher import WebhookDispatcher


router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


# --- Schemas ---

class WebhookCreateRequest(BaseModel):
    url: str
    secret: Optional[str] = None
    events: Optional[List[str]] = ["*"]
    organization_id: Optional[int] = 1


class WebhookUpdateRequest(BaseModel):
    url: Optional[str] = None
    secret: Optional[str] = None
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None


# --- Webhook Endpoints ---

@router.get("")
def list_webhooks(organization_id: Optional[int] = None):
    with get_db() as session:
        q = session.query(Webhook)
        if organization_id is not None:
            q = q.filter(Webhook.organization_id == organization_id)
        webhooks = q.order_by(Webhook.created_at.desc()).all()
        return [w.to_dict() for w in webhooks]


@router.post("")
def create_webhook(req: WebhookCreateRequest):
    with get_db() as session:
        secret = req.secret or secrets.token_hex(24)
        events = req.events or ["*"]
        webhook = Webhook(
            url=str(req.url).strip(),
            secret=secret,
            events_json=json.dumps(events),
            organization_id=req.organization_id or 1,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        session.add(webhook)
        session.flush()
        data = webhook.to_dict()
        data["secret"] = secret  # Returned on creation
        return data


@router.get("/{webhook_id}")
def get_webhook(webhook_id: int):
    with get_db() as session:
        webhook = session.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        return webhook.to_dict()


@router.put("/{webhook_id}")
def update_webhook(webhook_id: int, req: WebhookUpdateRequest):
    with get_db() as session:
        webhook = session.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        if req.url is not None:
            webhook.url = str(req.url).strip()
        if req.secret is not None:
            webhook.secret = req.secret
        if req.events is not None:
            webhook.events_json = json.dumps(req.events)
        if req.is_active is not None:
            webhook.is_active = req.is_active
        session.flush()
        return webhook.to_dict()


@router.delete("/{webhook_id}")
def delete_webhook(webhook_id: int):
    with get_db() as session:
        webhook = session.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        session.delete(webhook)
        return {"status": "DELETED", "webhook_id": webhook_id}


@router.post("/{webhook_id}/ping")
async def ping_webhook(webhook_id: int):
    with get_db() as session:
        webhook = session.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")

    result = await WebhookDispatcher.ping_endpoint(webhook_id)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to dispatch test ping")
    return {"status": "PING_DISPATCHED", "delivery": result}


@router.get("/{webhook_id}/deliveries")
def get_webhook_deliveries(webhook_id: int, limit: int = Query(50, ge=1, le=200)):
    with get_db() as session:
        webhook = session.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        deliveries = (
            session.query(WebhookDelivery)
            .filter(WebhookDelivery.webhook_id == webhook_id)
            .order_by(WebhookDelivery.delivered_at.desc())
            .limit(limit)
            .all()
        )
        return [d.to_dict() for d in deliveries]

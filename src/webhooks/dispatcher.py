"""Enterprise Webhook Dispatcher with HMAC-SHA256 signature signing and delivery tracking."""

from __future__ import annotations
import hmac
import hashlib
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union
import httpx
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import WebhookEndpoint, WebhookDelivery


class WebhookDispatcher:
    """Manages secure delivery of event webhooks with HMAC-SHA256 signatures."""

    SIGNATURE_HEADER = "X-LeadForge-Signature"
    EVENT_HEADER = "X-LeadForge-Event"

    SUPPORTED_EVENTS = [
        "lead.created",
        "lead.updated",
        "lead.verified",
        "technology.changed",
        "export.completed",
    ]

    @classmethod
    def sign_payload(cls, payload: Union[str, bytes], secret: str) -> str:
        """Generate HMAC-SHA256 hex signature for webhook payload."""
        if isinstance(payload, str):
            payload_bytes = payload.encode("utf-8")
        else:
            payload_bytes = payload
        return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    @classmethod
    def verify_signature(cls, payload: Union[str, bytes], secret: str, signature: str) -> bool:
        """Verify HMAC-SHA256 signature."""
        expected = cls.sign_payload(payload, secret)
        return hmac.compare_digest(expected, signature)

    @classmethod
    async def dispatch(
        cls,
        event_type: str,
        data: Dict[str, Any],
        session: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """Dispatch event payload to all active subscribed endpoints."""
        def _get_endpoints(s: Session) -> List[WebhookEndpoint]:
            return s.query(WebhookEndpoint).filter(WebhookEndpoint.is_active == True).all()

        if session is not None:
            endpoints = _get_endpoints(session)
        else:
            with get_db() as s:
                endpoints = _get_endpoints(s)

        deliveries = []
        for ep in endpoints:
            subscribed_events = json.loads(ep.events_json or '["*"]')
            if "*" in subscribed_events or event_type in subscribed_events:
                delivery = await cls.send_to_endpoint(
                    endpoint_id=ep.id,
                    url=ep.url,
                    secret=ep.secret,
                    event_type=event_type,
                    data=data,
                )
                deliveries.append(delivery)

        return deliveries

    @classmethod
    async def send_to_endpoint(
        cls,
        endpoint_id: int,
        url: str,
        secret: str,
        event_type: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Send single webhook notification to endpoint and record delivery status."""
        payload_dict = {
            "event": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }
        payload_str = json.dumps(payload_dict, separators=(",", ":"))
        signature = cls.sign_payload(payload_str, secret)

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "LeadForge-Webhook-Dispatcher/2.0",
            cls.SIGNATURE_HEADER: signature,
            cls.EVENT_HEADER: event_type,
        }

        status_code = None
        success = False
        response_body = None
        error_message = None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, content=payload_str, headers=headers)
                status_code = resp.status_code
                response_body = resp.text[:2000] if resp.text else None
                success = 200 <= status_code < 300
        except Exception as exc:
            error_message = str(exc)
            success = False

        # Persist delivery status in database
        now = datetime.now(timezone.utc)
        delivery_id = None
        with get_db() as s:
            delivery = WebhookDelivery(
                webhook_id=endpoint_id,
                event_type=event_type,
                payload_json=payload_str,
                status_code=status_code,
                success=success,
                error_message=error_message,
                delivered_at=now,
            )
            s.add(delivery)
            s.flush()
            delivery_id = delivery.id
            res_dict = delivery.to_dict()

        return res_dict

    @classmethod
    async def ping_endpoint(cls, endpoint_id: int) -> Optional[Dict[str, Any]]:
        """Send test ping event to a specific webhook endpoint."""
        with get_db() as s:
            ep = s.query(WebhookEndpoint).filter(WebhookEndpoint.id == endpoint_id).first()
            if not ep:
                return None
            url = ep.url
            secret = ep.secret

        return await cls.send_to_endpoint(
            endpoint_id=endpoint_id,
            url=url,
            secret=secret,
            event_type="test.ping",
            data={
                "message": "LeadForge webhook test ping",
                "pinged_at": datetime.now(timezone.utc).isoformat(),
            },
        )

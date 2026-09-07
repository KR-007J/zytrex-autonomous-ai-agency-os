"""API Key Management routes."""

from fastapi import APIRouter, HTTPException
import hashlib
import secrets
from pydantic import BaseModel
from src.database.db import get_db
from src.database.models import ApiKey

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


class CreateKeyRequest(BaseModel):
    name: str


@router.get("")
def list_keys():
    with get_db() as session:
        keys = session.query(ApiKey).filter(ApiKey.is_active == True).all()
        return [k.to_dict() for k in keys]


@router.post("")
def generate_key(req: CreateKeyRequest):
    raw_key = f"lf_{secrets.token_urlsafe(32)}"
    prefix = raw_key[:10]
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    with get_db() as session:
        k = ApiKey(name=req.name, key_hash=key_hash, prefix=prefix, is_active=True)
        session.add(k)
        session.flush()

    return {
        "id": k.id,
        "name": k.name,
        "api_key": raw_key,  # Returned only once!
        "prefix": prefix,
        "warning": "Store this key safely; it will not be shown again.",
    }


@router.delete("/{key_id}")
def revoke_key(key_id: int):
    with get_db() as session:
        key = session.query(ApiKey).filter(ApiKey.id == key_id).first()
        if not key:
            raise HTTPException(status_code=404, detail="API Key not found")
        key.is_active = False
        return {"status": "REVOKED", "id": key_id}

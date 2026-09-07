"""Authentication, Authorization, Password Hashing, and Multi-Tenancy Security for LeadForge."""

from __future__ import annotations
import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.orm import Session

from src.config import settings
from src.database.models import Organization, User, ApiKey
from src.database.db import get_db

# Security constants
ALGORITHM = "HS256"
DEFAULT_EXPIRATION_MINUTES = 60 * 24  # 24 hours
PASSWORD_HASH_ITERATIONS = 100_000
ROLE_HIERARCHY = {
    "owner": 4,
    "admin": 3,
    "analyst": 2,
    "viewer": 1,
}

bearer_scheme = HTTPBearer(auto_error=False)
api_key_header_scheme = APIKeyHeader(name=settings.api_key_header, auto_error=False)


# --- Password Hashing & Verification ---

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a cryptographically secure random salt."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PASSWORD_HASH_ITERATIONS,
    )
    return f"pbkdf2_sha256${PASSWORD_HASH_ITERATIONS}${salt}${dk.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password using constant-time comparison."""
    if not hashed_password or not plain_password:
        return False
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_hash = parts[3]
        dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(dk.hex(), expected_hash)
    except Exception:
        return False


# --- Base64URL Helpers ---

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data + padding)


# --- JWT Token Creation & Validation (Zero External Dependencies) ---

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
    secret_key: Optional[str] = None,
) -> str:
    """Create standard RFC 7519 HS256 JWT access token."""
    secret = secret_key or settings.secret_key
    to_encode = data.copy()

    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=DEFAULT_EXPIRATION_MINUTES)

    to_encode.update({
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    })

    header = {"alg": ALGORITHM, "typ": "JWT"}
    header_bytes = json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_bytes = json.dumps(to_encode, separators=(",", ":"), sort_keys=True).encode("utf-8")

    encoded_header = _b64url_encode(header_bytes)
    encoded_payload = _b64url_encode(payload_bytes)

    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    encoded_signature = _b64url_encode(signature)

    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"


def decode_access_token(token: str, secret_key: Optional[str] = None) -> Dict[str, Any]:
    """Decode and validate standard HS256 JWT access token."""
    secret = secret_key or settings.secret_key
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Token must have exactly 3 parts")

        encoded_header, encoded_payload, encoded_signature = parts
        signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
        expected_signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()

        actual_signature = _b64url_decode(encoded_signature)
        if not hmac.compare_digest(actual_signature, expected_signature):
            raise ValueError("Invalid token signature")

        payload_bytes = _b64url_decode(encoded_payload)
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Check expiration
        exp = payload.get("exp")
        if exp is not None:
            now_ts = int(datetime.now(timezone.utc).timestamp())
            if now_ts > exp:
                raise ValueError("Token has expired")

        return payload
    except Exception as e:
        raise ValueError(f"Invalid token: {e}") from e


# --- Role-based Authorization Logic ---

def has_role_permission(user_role: str, allowed_roles: List[str]) -> bool:
    """Check if user_role satisfies allowed_roles or has higher authority."""
    if user_role in allowed_roles:
        return True
    if user_role == "owner":
        return True
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    min_allowed_level = min((ROLE_HIERARCHY.get(r, 0) for r in allowed_roles), default=999)
    return user_level >= min_allowed_level


def check_role(user: User, allowed_roles: List[str]) -> bool:
    """Convenience validator for user objects."""
    return has_role_permission(user.role, allowed_roles)


# --- Dependencies: Authentication & Role Verification ---

def get_current_user(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    api_key: Optional[str] = Security(api_key_header_scheme),
) -> User:
    """FastAPI dependency to extract and authenticate current user via JWT or API Key."""
    # 1. Bearer Token Auth
    if auth_credentials and auth_credentials.credentials:
        try:
            payload = decode_access_token(auth_credentials.credentials)
            user_id = payload.get("sub")
            email = payload.get("email")

            with get_db() as session:
                user = None
                if user_id is not None:
                    user = session.query(User).filter(User.id == int(user_id)).first()
                elif email is not None:
                    user = session.query(User).filter(User.email == email).first()

                if not user or not user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not found or inactive",
                    )
                # Detach from session by accessing required fields
                _ = user.id, user.organization_id, user.email, user.role, user.is_active
                return user
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            )

    # 2. API Key Auth
    if api_key:
        key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
        with get_db() as session:
            key_record = session.query(ApiKey).filter(
                ApiKey.key_hash == key_hash,
                ApiKey.is_active == True,
            ).first()

            if not key_record:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or revoked API Key",
                )

            key_record.last_used_at = datetime.now(timezone.utc)
            session.flush()

            org_id = key_record.organization_id or 1
            # Return synthetic or actual org admin
            admin_user = session.query(User).filter(
                User.organization_id == org_id,
                User.role.in_(["owner", "admin"]),
            ).first()

            if admin_user:
                _ = admin_user.id, admin_user.organization_id, admin_user.email, admin_user.role, admin_user.is_active
                return admin_user

            return User(
                id=999999,
                organization_id=org_id,
                email=f"apikey-{key_record.prefix}@leadforge.internal",
                role="admin",
                is_active=True,
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication credentials (provide Bearer token or X-API-Key)",
    )


def require_role(allowed_roles: List[str]):
    """Factory returning a FastAPI dependency that enforces role-based access control."""
    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if not has_role_permission(current_user.role, allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action prohibited for role '{current_user.role}'. Required: {allowed_roles}",
            )
        return current_user

    return role_dependency


# --- Database Seed Default Organization & Admin ---

def seed_default_data(session: Session) -> Tuple[Organization, User]:
    """Seed default organization and admin user if organizations or users table is empty."""
    org = session.query(Organization).filter(Organization.slug == "default-organization").first()
    if not org:
        org = Organization(
            name="Default Organization",
            slug="default-organization",
        )
        session.add(org)
        session.flush()

    user = session.query(User).filter(User.email == "admin@leadforge.io").first()
    if not user:
        user = User(
            organization_id=org.id,
            email="admin@leadforge.io",
            hashed_password=hash_password("leadforge123"),
            role="admin",
            is_active=True,
        )
        session.add(user)
        session.flush()

    return org, user

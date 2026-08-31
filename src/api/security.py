"""Cybersecurity Defense Suite — Security Headers, Rate Limiting, Path Sanitization, and Secret Masking."""

from __future__ import annotations
import time
import re
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware


class EnterpriseSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforce strict cyber security headers across all API responses."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # 1. Content Security Policy (Prevents XSS, script injections, and data exfiltration)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://fonts.googleapis.com https://fonts.gstatic.com; "
            "img-src 'self' data: https: blob:; "
            "media-src 'self' https: data: blob:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.tailwindcss.com; "
            "connect-src 'self';"
        )

        # 2. Prevent MIME Sniffing attacks
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 3. Prevent Clickjacking / UI Redressing attacks
        response.headers["X-Frame-Options"] = "DENY"

        # 4. Enable browser XSS protection filters
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 5. Strict Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 6. Restrict hardware access & permissions
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=(), payment=()"

        # 7. HTTP Strict Transport Security
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # 8. Hide server fingerprint
        response.headers["Server"] = "Enterprise-Secure-Gateway"

        return response


class RateLimiter:
    """Sliding-window IP rate limiter to protect endpoints against DDoS and brute force."""

    def __init__(self, requests_per_minute: int = 120):
        self.requests_per_minute = requests_per_minute
        self.ip_records: Dict[str, list[float]] = {}

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        window_start = now - 60.0

        timestamps = self.ip_records.get(client_ip, [])
        valid_timestamps = [t for t in timestamps if t > window_start]

        if len(valid_timestamps) >= self.requests_per_minute:
            self.ip_records[client_ip] = valid_timestamps
            return False

        valid_timestamps.append(now)
        self.ip_records[client_ip] = valid_timestamps
        return True


def validate_export_path(file_path: Path, allowed_base_dir: Path) -> Path:
    """Strictly sanitize and validate that export file path does not escape allowed directories."""
    resolved_path = file_path.resolve()
    resolved_base = allowed_base_dir.resolve()

    try:
        resolved_path.relative_to(resolved_base)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cybersecurity Violation: Path Traversal Attempt Blocked.",
        )

    if not resolved_path.exists() or not resolved_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export file not found.",
        )

    if resolved_path.suffix.lower() not in [".xlsx", ".csv", ".json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file extension requested.",
        )

    return resolved_path


def mask_sensitive_secrets(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively mask API keys, passwords, and SMTP secrets before returning in API payloads."""
    masked = {}
    secret_keys = {"smtp_pass", "api_key", "password", "token", "client_secret"}

    for key, value in config_data.items():
        if isinstance(value, dict):
            masked[key] = mask_sensitive_secrets(value)
        elif isinstance(key, str) and any(s in key.lower() for s in secret_keys):
            masked[key] = "••••••••" if value else ""
        else:
            masked[key] = value

    return masked

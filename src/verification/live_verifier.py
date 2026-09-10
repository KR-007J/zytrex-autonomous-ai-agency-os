"""Safe Live Verification of candidate domains & URLs."""

from __future__ import annotations
import time
import socket
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
import httpx
from src.security.ssrf import validate_and_resolve_url, SSRFValidationError
from src.config import settings


class VerificationResult:
    def __init__(
        self,
        domain: str,
        canonical_url: str,
        is_live: bool,
        http_status: Optional[int],
        response_time_ms: float,
        has_ssl: bool,
        resolved_ip: Optional[str],
        headers: Dict[str, str],
        cookies: Dict[str, str],
        html_body: str,
        verified_at: datetime,
        error_message: Optional[str] = None,
    ):
        self.domain = domain
        self.canonical_url = canonical_url
        self.is_live = is_live
        self.http_status = http_status
        self.response_time_ms = round(response_time_ms, 1)
        self.has_ssl = has_ssl
        self.resolved_ip = resolved_ip
        self.headers = headers
        self.cookies = cookies
        self.html_body = html_body
        self.verified_at = verified_at
        self.error_message = error_message

    @property
    def freshness_status(self) -> str:
        if not self.is_live:
            return "OFFLINE"
        delta = datetime.now(timezone.utc) - self.verified_at
        hours = delta.total_seconds() / 3600
        if hours < 1:
            return "LIVE"
        elif hours < 24:
            return "FRESH"
        elif hours < 168:
            return "RECENT"
        return "STALE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "canonical_url": self.canonical_url,
            "is_live": self.is_live,
            "freshness": self.freshness_status,
            "http_status": self.http_status,
            "response_time_ms": self.response_time_ms,
            "has_ssl": self.has_ssl,
            "resolved_ip": self.resolved_ip,
            "verified_at": self.verified_at.isoformat(),
            "error_message": self.error_message,
        }


class LiveVerifier:
    """Performs strict SSRF-safe live verification of candidate websites."""

    @classmethod
    async def verify(cls, target: str, timeout: float = 10.0) -> VerificationResult:
        now = datetime.now(timezone.utc)
        clean_target = target.strip().lower()
        if not clean_target.startswith("http://") and not clean_target.startswith("https://"):
            clean_target = f"https://{clean_target}"

        # 1. SSRF validate initial target
        try:
            safe_url, initial_ip, port = validate_and_resolve_url(clean_target)
        except SSRFValidationError as e:
            domain = clean_target.split("://")[-1].split("/")[0]
            return VerificationResult(
                domain=domain,
                canonical_url=clean_target,
                is_live=False,
                http_status=None,
                response_time_ms=0.0,
                has_ssl=False,
                resolved_ip=None,
                headers={},
                cookies={},
                html_body="",
                verified_at=now,
                error_message=f"SSRF Block: {e}",
            )

        domain = safe_url.split("://")[-1].split("/")[0]

        # 2. Perform safe HTTP request with redirect inspection
        start_time = time.perf_counter()
        headers = {
            "User-Agent": settings.crawler_user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        try:
            async with httpx.AsyncClient(
                verify=True,
                follow_redirects=True,
                max_redirects=4,
                timeout=httpx.Timeout(min(timeout, 3.5), connect=2.0),
            ) as client:
                resp = await client.get(safe_url, headers=headers)
                elapsed_ms = (time.perf_counter() - start_time) * 1000

                # Verify final redirect destination against SSRF
                final_url = str(resp.url)
                try:
                    validate_and_resolve_url(final_url)
                except SSRFValidationError as e:
                    return VerificationResult(
                        domain=domain,
                        canonical_url=final_url,
                        is_live=False,
                        http_status=resp.status_code,
                        response_time_ms=elapsed_ms,
                        has_ssl=False,
                        resolved_ip=initial_ip,
                        headers={},
                        cookies={},
                        html_body="",
                        verified_at=now,
                        error_message=f"Redirect destination failed SSRF check: {e}",
                    )

                is_live = 200 <= resp.status_code < 400
                resp_headers = dict(resp.headers)
                resp_cookies = dict(resp.cookies)

                return VerificationResult(
                    domain=domain,
                    canonical_url=final_url,
                    is_live=is_live,
                    http_status=resp.status_code,
                    response_time_ms=elapsed_ms,
                    has_ssl=final_url.startswith("https://"),
                    resolved_ip=initial_ip,
                    headers=resp_headers,
                    cookies=resp_cookies,
                    html_body=resp.text[:600000],  # 600KB max for fingerprinting
                    verified_at=now,
                )

        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError, Exception) as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return VerificationResult(
                domain=domain,
                canonical_url=safe_url,
                is_live=False,
                http_status=None,
                response_time_ms=elapsed_ms,
                has_ssl=safe_url.startswith("https://"),
                resolved_ip=initial_ip,
                headers={},
                cookies={},
                html_body="",
                verified_at=now,
                error_message=str(e),
            )

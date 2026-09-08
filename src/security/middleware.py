"""Enterprise Security and Rate Limiting Middlewares."""

from __future__ import annotations
import time
from collections import defaultdict
from typing import Dict, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects hardened OWASP security headers into all HTTP responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # CSP: Strict policy allowing essential CDN assets, Tailwind, Lucide, Google fonts, and inline canvas shaders
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.tailwindcss.com https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://db.onlinewebfonts.com; "
            "font-src 'self' https://fonts.gstatic.com https://db.onlinewebfonts.com data:; "
            "img-src 'self' data: https: blob:; "
            "media-src 'self' https: data: blob:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response.headers["Content-Security-Policy"] = csp
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        return response


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """In-memory sliding window rate limiter for abuse prevention."""

    def __init__(self, app, max_requests: int = 40, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        # Enforce rate limit specifically on heavy discovery actions
        if path.startswith("/api/v1/discover") and request.method == "POST":
            client_ip = request.client.host if request.client else "127.0.0.1"
            now = time.time()
            cutoff = now - self.window_seconds

            # Clean expired timestamps
            self.requests[client_ip] = [t for t in self.requests[client_ip] if t > cutoff]

            if len(self.requests[client_ip]) >= self.max_requests:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "RATE_LIMIT_EXCEEDED",
                        "detail": f"Rate limit of {self.max_requests} discovery requests per {self.window_seconds}s exceeded.",
                    },
                    headers={"Retry-After": str(self.window_seconds)},
                )

            self.requests[client_ip].append(now)

        return await call_next(request)

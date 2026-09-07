"""FastAPI Application Main Router and Assembly."""

from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from src.config import settings
from src.database.db import init_db

from src.api.routes_health import router as health_router
from src.api.routes_technologies import router as tech_router
from src.api.routes_discover import router as discover_router
from src.api.routes_leads import router as leads_router
from src.api.routes_exports import router as exports_router
from src.api.routes_keys import router as keys_router
from src.api.routes_projects import router as projects_router
from src.api.routes_webhooks import router as webhooks_router
from src.api.routes_import import router as import_router
from src.api.routes_search import router as search_router
from src.api.routes_auth import router as auth_router
from src.api.routes_organization import router as org_router
from src.api.routes_audit import router as audit_router
from src.api.routes_jobs import router as jobs_router
from src.api.routes_dashboard import router as dashboard_router

init_db()

app = FastAPI(
    title=settings.app_name,
    description="Enterprise Lead Intelligence Platform powered by open technology discovery and deterministic verification.",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 Router prefix
app.include_router(health_router, prefix="/api/v1")
app.include_router(tech_router, prefix="/api/v1")
app.include_router(discover_router, prefix="/api/v1")
app.include_router(leads_router, prefix="/api/v1")
app.include_router(exports_router, prefix="/api/v1")
app.include_router(keys_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(webhooks_router, prefix="/api/v1")
app.include_router(import_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(org_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")

# Mount web frontend static assets if directory exists
web_dir = Path(__file__).parent.parent / "web"
if web_dir.exists():
    static_dir = web_dir / "static"
    if not static_dir.exists():
        static_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
def read_root():
    index_file = web_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "name": settings.app_name,
        "tagline": settings.app_tagline,
        "version": settings.app_version,
        "docs": "/docs",
        "api_v1": "/api/v1",
    }


@app.get("/{full_path:path}")
def catch_all_spa_routes(full_path: str):
    # Ignore API and docs paths
    if full_path.startswith(("api/", "docs", "redoc", "openapi.json", "static/")):
        raise HTTPException(status_code=404, detail="Endpoint not found")

    index_file = web_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"error": "Frontend index file not found"}

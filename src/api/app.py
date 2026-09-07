"""FastAPI Application Main Router and Assembly."""

from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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

# Mount web frontend static assets if directory exists
web_dir = Path(__file__).parent.parent / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir / "static")), name="static")


@app.get("/")
def read_root():
    from fastapi.responses import FileResponse
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

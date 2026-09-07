"""LeadForge Enterprise Configuration Manager."""

from __future__ import annotations
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).parent.parent


class Settings(BaseSettings):
    app_name: str = "LeadForge"
    app_tagline: str = "Find businesses by the technology they use."
    app_version: str = "2.0.0"
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    # Database: SQLite default, PostgreSQL fully supported
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{PROJECT_ROOT}/data/leadforge.db")

    # Security & SSRF
    secret_key: str = os.getenv("SECRET_KEY", "leadforge-insecure-dev-secret-change-in-prod")
    api_key_header: str = "X-API-Key"
    blocked_ip_ranges: List[str] = [
        "127.0.0.0/8",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "169.254.0.0/16",
        "0.0.0.0/8",
        "::1/128",
        "fc00::/7",
        "fe80::/10",
    ]

    # Crawler & Rate Limits (Responsible crawling)
    crawler_timeout_seconds: float = float(os.getenv("CRAWLER_TIMEOUT", "12.0"))
    crawler_max_concurrency: int = int(os.getenv("CRAWLER_CONCURRENCY", "10"))
    crawler_user_agent: str = os.getenv(
        "CRAWLER_USER_AGENT",
        "Mozilla/5.0 (compatible; LeadForgeBot/2.0; +https://leadforge.io/bot)",
    )
    respect_robots_txt: bool = True
    max_pages_per_domain: int = 4

    # Signatures
    signatures_dir: Path = PROJECT_ROOT / "technology_signatures"

    # Feature Flags
    enable_common_crawl: bool = True
    enable_cert_transparency: bool = True
    enable_dns_discovery: bool = True
    enable_public_datasets: bool = True
    enable_ai_layer: bool = False  # Disabled in zero-cost mode

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()

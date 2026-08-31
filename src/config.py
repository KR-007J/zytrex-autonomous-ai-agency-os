"""Configuration manager for Lead Generation & Outreach Agent."""

from __future__ import annotations
import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


class RateLimitConfig(BaseModel):
    min_delay_seconds: float = 1.5
    max_delay_seconds: float = 3.5
    jitter: bool = True
    respect_robots_txt: bool = True
    max_retries: int = 3
    timeout_seconds: int = 15
    concurrency_limit: int = 3


class SearchEngineConfig(BaseModel):
    enabled: bool = True
    queries: List[str] = Field(default_factory=list)
    max_results_per_query: int = 15


class ClassifiedSiteConfig(BaseModel):
    name: str
    enabled: bool = True
    base_url: str
    listing_selector: str
    fields: Dict[str, str] = Field(default_factory=dict)


class ScrapingConfig(BaseModel):
    rate_limiting: RateLimitConfig = Field(default_factory=RateLimitConfig)
    user_agents: List[str] = Field(default_factory=list)
    search_engines: SearchEngineConfig = Field(default_factory=SearchEngineConfig)
    classified_sites: List[ClassifiedSiteConfig] = Field(default_factory=list)


class TemplateConfig(BaseModel):
    id: str
    name: str
    subject: str
    body: str


class ManualAssistConfig(BaseModel):
    auto_generate_drafts: bool = True
    default_template_id: str = "b2b_growth_pitch"
    search_ranking_weights: Dict[str, int] = Field(default_factory=dict)


class OfficialApiConfig(BaseModel):
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = "http://localhost:8000/api/linkedin/callback"
    ad_account_id: str = ""
    access_token: str = ""


class LinkedInConfig(BaseModel):
    mode: str = "manual_assist"  # 'manual_assist' or 'official_api'
    manual_assist: ManualAssistConfig = Field(default_factory=ManualAssistConfig)
    official_api: OfficialApiConfig = Field(default_factory=OfficialApiConfig)
    templates: Dict[str, TemplateConfig] = Field(default_factory=dict)


class HermesGatewayConfig(BaseModel):
    enabled: bool = True
    report_schedule: str = "0 9 * * *"
    alert_on_new_leads: bool = True


class TelegramConfig(BaseModel):
    enabled: bool = False
    bot_token: str = ""
    chat_id: str = ""


class SlackConfig(BaseModel):
    enabled: bool = False
    webhook_url: str = ""


class EmailConfig(BaseModel):
    enabled: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    recipient: str = ""


class NotificationsConfig(BaseModel):
    hermes_gateway: HermesGatewayConfig = Field(default_factory=HermesGatewayConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    slack: SlackConfig = Field(default_factory=SlackConfig)
    email: EmailConfig = Field(default_factory=EmailConfig)


class AppConfig(BaseModel):
    name: str = "LeadGen Outreach Pro"
    version: str = "1.0.0"
    database_url: str = "sqlite:///./data/leads.db"
    environment: str = "production"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000


class RootConfig(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    scraping: ScrapingConfig = Field(default_factory=ScrapingConfig)
    linkedin: LinkedInConfig = Field(default_factory=LinkedInConfig)
    notifications: NotificationsConfig = Field(default_factory=NotificationsConfig)


def load_config(config_path: Optional[str | Path] = None) -> RootConfig:
    """Load configuration from YAML file or return defaults."""
    target_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not target_path.exists():
        return RootConfig()

    with open(target_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return RootConfig(**data)


def save_config(config: RootConfig, config_path: Optional[str | Path] = None) -> None:
    """Save configuration model to YAML file."""
    target_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    data = config.model_dump()

    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

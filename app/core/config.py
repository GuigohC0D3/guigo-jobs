from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    app_name: str = "Guigo"
    debug: bool = False
    log_level: str = "INFO"

    # Request settings
    request_timeout: int = 15
    max_retries: int = 3
    retry_delay: float = 1.5
    user_agent: str = "Guigo/1.0 (+https://github.com/guigo-jobs)"

    # Cache
    cache_enabled: bool = True
    cache_ttl_minutes: int = 30

    # Storage paths
    base_dir: Path = Path(__file__).parent.parent.parent
    exports_dir: Path = base_dir / "exports"
    logs_dir: Path = base_dir / "logs"
    storage_dir: Path = base_dir / ".guigo"

    # API Keys (optional — providers work without keys but may have rate limits)
    themuse_api_key: Optional[str] = None
    greenhouse_api_key: Optional[str] = None

    # Provider toggles
    enable_remoteok: bool = True
    enable_remotive: bool = True
    enable_arbeitnow: bool = True
    enable_themuse: bool = True
    enable_gupy: bool = True
    enable_greenhouse: bool = False
    enable_linkedin: bool = True
    enable_lever: bool = False

    # Scoring weights
    score_keyword_match: float = 2.0
    score_tech_match: float = 3.0
    score_junior_title: float = 1.5
    score_recent_post: float = 1.0

    @field_validator("exports_dir", "logs_dir", "storage_dir", mode="before")
    @classmethod
    def ensure_dir(cls, v: Path) -> Path:
        Path(v).mkdir(parents=True, exist_ok=True)
        return Path(v)


settings = Settings()

"""Worker configuration."""

from __future__ import annotations

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str | None = None
    worker_id: str | None = None
    poll_interval_seconds: float = 2
    
    # AI/LLM settings
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    ai_default_provider: str = "anthropic"  # anthropic or openai


settings = Settings()

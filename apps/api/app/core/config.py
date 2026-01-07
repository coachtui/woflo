from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str | None = None
    supabase_url: str | None = None
    supabase_jwks_url: str | None = None
    supabase_service_role_key: str | None = None
    sentry_dsn: str | None = None

    environment: str = "dev"

    worker_id: str | None = None
    poll_interval_seconds: float = 2


settings = Settings()

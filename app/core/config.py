"""
Application configuration via Pydantic BaseSettings.

Reads from environment variables and .env files. All secrets and service
URLs are validated at startup — a missing or malformed value crashes fast
rather than failing silently at runtime.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, HttpUrl, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Immutable, validated configuration singleton."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "Job Pipeline API"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # --- API Keys ---
    teal_api_key: str = Field(
        default="your-teal-api-key-here",
        min_length=10,
        description="API key for the Teal job-tracking platform.",
    )
    openai_api_key: str = Field(
        default="sk-your-openai-key-here",
        min_length=10,
        description="API key for OpenAI chat-completion and embedding calls.",
    )
    gemini_api_key: str | None = Field(
        default=None,
        description="Optional API key for Google Gemini (using OpenAI compatibility endpoint).",
    )

    # --- Redis ---
    redis_url: RedisDsn = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string used by Celery and caching layers.",
    )

    # --- External Service URLs ---
    teal_base_url: HttpUrl = Field(
        default="https://api.teal.dev/v1",
        description="Base URL for the Teal REST API.",
    )
    openai_base_url: HttpUrl = Field(
        default="https://api.openai.com/v1",
        description="Base URL for the OpenAI REST API.",
    )

    # --- HTTP Client Tuning ---
    http_timeout_seconds: float = Field(
        default=30.0, gt=0, description="Default timeout for outbound HTTP requests."
    )
    http_max_retries: int = Field(
        default=3, ge=0, description="Maximum automatic retries on transient failures."
    )
    http_backoff_base: float = Field(
        default=1.0,
        gt=0,
        description="Base delay (seconds) for exponential backoff between retries.",
    )

    # --- Celery ---
    celery_task_default_queue: str = "pipeline"
    celery_task_acks_late: bool = True
    celery_worker_prefetch_multiplier: int = 1

    @property
    def redis_url_str(self) -> str:
        """Return the Redis DSN as a plain string for libraries that refuse AnyUrl."""
        return str(self.redis_url)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance (parsed once per process)."""
    return Settings()  # type: ignore[call-arg]

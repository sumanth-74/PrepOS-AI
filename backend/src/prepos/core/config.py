from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "PrepOS AI"
    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    database_url: str
    database_echo: bool = False
    database_pool_size: int = 10
    database_max_overflow: int = 20

    redis_url: str = "redis://localhost:6379/0"

    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    celery_task_always_eager: bool = False

    event_idempotency_ttl_days: int = 90
    outbox_publish_batch_size: int = 100
    outbox_stale_minutes: int = 5
    lg_optimistic_lock_max_retries: int = 3

    sentry_dsn: str | None = None
    sentry_traces_sample_rate: float = 0.1
    otel_enabled: bool = True
    otel_service_name: str = "prepos-api"
    otel_exporter_otlp_endpoint: str | None = None

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    openai_api_key: str | None = None
    embedding_model: str = "text-embedding-3-large"
    embedding_dims: int = 1536
    embedding_batch_size: int = 100
    knowledge_storage_path: str = "data/knowledge"
    knowledge_hybrid_alpha: float = 0.7
    knowledge_chunk_size_tokens: int = 600
    knowledge_chunk_overlap_tokens: int = 100
    knowledge_search_default_limit: int = 8
    knowledge_rrf_k: int = 60
    llm_model: str = "gpt-4o-mini"
    llm_max_completion_tokens: int = 800
    knowledge_ask_prompt_chunk_max: int = 8
    knowledge_relevance_min_score: float = 0.15
    knowledge_recency_half_life_days: int = 30

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            import json

            return list(json.loads(value))
        return list(value)

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()

from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "FridgeFriend"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    REDIS_URL: str = "redis://localhost:6379/0"
    IDEMPOTENCY_BACKEND: str = "memory"
    IDEMPOTENCY_TTL_SECONDS: int = 86400
    AUTH_MOCK: bool = True
    S3_ENDPOINT_URL: str = "http://localhost:4566"
    S3_BUCKET: str = "fridgefriend-uploads"
    AWS_REGION: str = "us-east-1"
    STORAGE_BACKEND: str = "local"
    FIREBASE_PROJECT_ID: str = ""
    SPOONACULAR_API_KEY: str = ""
    RECIPE_SOURCE: str = "mock"
    LLM_API_URL: str = "https://litellm.labs.jb.gg"
    LLM_MODEL: str = "gpt-4.1-mini"
    SENTRY_DSN: str = ""
    AMPLITUDE_API_KEY: str = ""

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

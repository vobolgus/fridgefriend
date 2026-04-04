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
    AUTH_MOCK: bool = False
    S3_ENDPOINT_URL: str = "http://localhost:4566"
    S3_BUCKET: str = "fridgefriend-uploads"
    AWS_REGION: str = "us-east-1"
    STORAGE_BACKEND: str = "local"
    FIREBASE_PROJECT_ID: str = ""
    SPOONACULAR_API_KEY: str = ""
    RECIPE_SOURCE: str = "mock"
    LLM_API_URL: str = "https://litellm.labs.jb.gg"
    LLM_MODEL: str = "gpt-4.1-mini"
    PHOTO_PARSER_BACKEND: str = "mock"
    BARCODE_API_SOURCE: str = "mock"
    SENTRY_DSN: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    SENTRY_ENVIRONMENT: str = "development"
    AMPLITUDE_API_KEY: str = ""
    LLM_INPUT_COST_PER_1M: float = 0.40
    LLM_OUTPUT_COST_PER_1M: float = 1.60
    SPOONACULAR_POINT_COST: float = 0.005
    FIREBASE_CREDENTIALS_PATH: str = ""
    FCM_ENABLED: bool = False

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

from __future__ import annotations

from pytest import MonkeyPatch

from app.core.config import Settings


def test_redis_url_configurable(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("REDIS_URL", raising=False)

    settings = Settings()

    assert hasattr(settings, "REDIS_URL")
    assert settings.REDIS_URL == "redis://localhost:6379/0"


def test_redis_url_can_be_overridden(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("REDIS_URL", "redis://cache.internal:6380/1")

    settings = Settings()

    assert settings.REDIS_URL == "redis://cache.internal:6380/1"


def test_sentry_config_defaults(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    monkeypatch.delenv("SENTRY_TRACES_SAMPLE_RATE", raising=False)
    monkeypatch.delenv("SENTRY_ENVIRONMENT", raising=False)

    settings = Settings()

    assert settings.SENTRY_DSN == ""
    assert settings.SENTRY_TRACES_SAMPLE_RATE == 0.1
    assert settings.SENTRY_ENVIRONMENT == "development"


def test_sentry_config_from_env(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("SENTRY_DSN", "https://key@sentry.io/123")
    monkeypatch.setenv("SENTRY_TRACES_SAMPLE_RATE", "0.25")
    monkeypatch.setenv("SENTRY_ENVIRONMENT", "production")

    settings = Settings()

    assert settings.SENTRY_DSN == "https://key@sentry.io/123"
    assert settings.SENTRY_TRACES_SAMPLE_RATE == 0.25
    assert settings.SENTRY_ENVIRONMENT == "production"


def test_amplitude_api_key_default(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("AMPLITUDE_API_KEY", raising=False)

    settings = Settings()

    assert settings.AMPLITUDE_API_KEY == ""


def test_llm_cost_config_defaults(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_INPUT_COST_PER_1M", raising=False)
    monkeypatch.delenv("LLM_OUTPUT_COST_PER_1M", raising=False)
    monkeypatch.delenv("SPOONACULAR_POINT_COST", raising=False)

    settings = Settings()

    assert settings.LLM_INPUT_COST_PER_1M == 0.40
    assert settings.LLM_OUTPUT_COST_PER_1M == 1.60
    assert settings.SPOONACULAR_POINT_COST == 0.005

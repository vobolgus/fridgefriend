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

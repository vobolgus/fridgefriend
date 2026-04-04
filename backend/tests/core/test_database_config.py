from __future__ import annotations

from pytest import MonkeyPatch

from app.core.config import Settings


def test_settings_has_database_url_field() -> None:
    settings = Settings()

    assert hasattr(settings, "DATABASE_URL")


def test_database_url_default_is_sqlite(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    settings = Settings()

    assert settings.DATABASE_URL == "sqlite+aiosqlite:///:memory:"


def test_database_url_can_be_overridden(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")

    settings = Settings()

    assert settings.DATABASE_URL == "sqlite+aiosqlite:///./app.db"

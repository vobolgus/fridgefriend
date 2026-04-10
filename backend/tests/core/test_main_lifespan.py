from __future__ import annotations

import pytest

from app.core.config import settings
from app.main import app


@pytest.mark.asyncio
async def test_lifespan_rejects_production_sqlite(monkeypatch: pytest.MonkeyPatch) -> None:
    previous_environment = settings.ENVIRONMENT
    previous_database_url = settings.DATABASE_URL
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "DATABASE_URL", "sqlite+aiosqlite:///:memory:")

    try:
        with pytest.raises(RuntimeError, match="Production must use PostgreSQL, not SQLite"):
            async with app.router.lifespan_context(app):
                pass
    finally:
        monkeypatch.setattr(settings, "ENVIRONMENT", previous_environment)
        monkeypatch.setattr(settings, "DATABASE_URL", previous_database_url)

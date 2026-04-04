from __future__ import annotations

from types import TracebackType
from typing import TypedDict, cast

import httpx
import pytest


class HealthyRedis:
    async def ping(self) -> bool:
        return True

    async def aclose(self) -> None:
        return None


class BrokenRedis:
    async def ping(self) -> bool:
        raise OSError("redis unavailable")

    async def aclose(self) -> None:
        return None


class BrokenConnectionContext:
    async def __aenter__(self) -> object:
        raise OSError("database unavailable")

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None


class ReadinessCheck(TypedDict):
    status: str
    detail: str


class ReadinessBody(TypedDict):
    status: str
    checks: dict[str, ReadinessCheck]


@pytest.mark.asyncio
async def test_readiness_healthy(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get_redis() -> HealthyRedis:
        return HealthyRedis()

    monkeypatch.setattr("app.main.get_redis", fake_get_redis)

    response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_readiness_reports_db_check(
    client: httpx.AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get_redis() -> HealthyRedis:
        return HealthyRedis()

    monkeypatch.setattr("app.main.get_redis", fake_get_redis)
    monkeypatch.setattr("app.main.get_engine", lambda: BrokenEngine())

    response = await client.get("/health/ready")

    assert response.status_code == 503
    body = cast(ReadinessBody, response.json())
    assert "database" in body["checks"]
    assert body["checks"]["database"]["status"] == "unhealthy"


class BrokenEngine:
    def connect(self) -> BrokenConnectionContext:
        return BrokenConnectionContext()

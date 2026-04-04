# pyright: reportAny=false, reportUnusedParameter=false, reportUnusedCallResult=false, reportMissingImports=false, reportUnknownVariableType=false

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.events import AnalyticsEvent
from app.models.user import User
from app.modules.inventory.dependencies import get_current_user


def _headers(test_headers: dict[str, str], key: str) -> dict[str, str]:
    return {**test_headers, "Idempotency-Key": key}


@pytest_asyncio.fixture
async def analytics_test_user(app: FastAPI, db_session: AsyncSession) -> AsyncIterator[User]:
    user = User(email="analytics-api@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    async def override_get_current_user() -> User:
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    yield user

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_collect_event(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    analytics_test_user: User,
    db_session: AsyncSession,
) -> None:
    response = await client.post(
        "/v1/analytics/events",
        headers=_headers(test_headers, "analytics-collect-1"),
        json={"event_type": "recipe_viewed", "payload": {"recipe_id": "recipe-1"}},
    )

    assert response.status_code == 202
    result = await db_session.execute(select(AnalyticsEvent).where(AnalyticsEvent.user_id == analytics_test_user.id))
    event = result.scalar_one()
    assert event.event_type == "recipe_viewed"


@pytest.mark.asyncio
async def test_analytics_event_is_immutable(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    analytics_test_user: User,
) -> None:
    _ = (test_headers, analytics_test_user)
    patch_response = await client.patch("/v1/analytics/events", headers=test_headers, json={})
    delete_response = await client.delete("/v1/analytics/events", headers=test_headers)

    assert patch_response.status_code == 405
    assert delete_response.status_code == 405


@pytest.mark.asyncio
async def test_collect_event_requires_idempotency_key(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    analytics_test_user: User,
) -> None:
    _ = analytics_test_user
    response = await client.post(
        "/v1/analytics/events",
        headers=test_headers,
        json={"event_type": "recipe_viewed", "payload": {"recipe_id": "recipe-1"}},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Idempotency-Key header is required"}

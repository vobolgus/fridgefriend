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
from app.models.notification import DeviceToken, NotificationPreference
from app.models.user import User
from app.modules.inventory.dependencies import get_current_user


@pytest_asyncio.fixture
async def notifications_test_user(app: FastAPI, db_session: AsyncSession) -> AsyncIterator[User]:
    user = User(email="notifications-api@example.com")
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
async def test_get_default_notification_preferences(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    notifications_test_user: User,
) -> None:
    response = await client.get("/v1/notifications", headers=test_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == str(notifications_test_user.id)
    assert payload["expiry_reminder_enabled"] is True
    assert payload["reminder_days_before"] == 1


@pytest.mark.asyncio
async def test_update_notification_preferences(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    notifications_test_user: User,
    db_session: AsyncSession,
) -> None:
    response = await client.patch(
        "/v1/notifications",
        headers=test_headers,
        json={
            "expiry_reminder_enabled": False,
            "reminder_days_before": 3,
            "quiet_hours_start": "22:00:00",
            "quiet_hours_end": "07:00:00",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["expiry_reminder_enabled"] is False
    assert payload["reminder_days_before"] == 3

    result = await db_session.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == notifications_test_user.id),
    )
    preference = result.scalar_one()
    assert preference.reminder_days_before == 3


@pytest.mark.asyncio
async def test_register_device_token(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    notifications_test_user: User,
    db_session: AsyncSession,
) -> None:
    response = await client.post(
        "/v1/notifications/devices",
        headers=test_headers,
        json={"token": "device-token-abc", "platform": "ios"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["user_id"] == str(notifications_test_user.id)
    assert payload["token"] == "device-token-abc"

    result = await db_session.execute(select(DeviceToken).where(DeviceToken.token == "device-token-abc"))
    token = result.scalar_one()
    assert token.platform == "ios"


@pytest.mark.asyncio
async def test_unregister_device_token(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    notifications_test_user: User,
    db_session: AsyncSession,
) -> None:
    token = DeviceToken(user_id=notifications_test_user.id, token="device-token-delete", platform="android")
    db_session.add(token)
    await db_session.commit()
    await db_session.refresh(token)

    response = await client.delete(f"/v1/notifications/devices/{token.id}", headers=test_headers)

    assert response.status_code == 204
    result = await db_session.execute(select(DeviceToken).where(DeviceToken.id == token.id))
    assert result.scalar_one_or_none() is None

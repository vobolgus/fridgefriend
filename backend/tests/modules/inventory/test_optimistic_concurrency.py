from __future__ import annotations

from collections.abc import AsyncIterator
from typing import cast

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.modules.inventory.dependencies import get_current_user


@pytest_asyncio.fixture
async def test_user(app: FastAPI, db_session: AsyncSession) -> AsyncIterator[User]:
    user = User(email="inventory-concurrency@example.com")
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
async def test_update_with_correct_version_succeeds(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    _ = test_user
    create_response = await client.post(
        "/v1/items",
        headers=test_headers,
        json={
            "display_name": "Milk",
            "quantity": 1.0,
            "unit": "liter",
            "storage_location": "fridge",
        },
    )
    create_payload = cast(dict[str, object], create_response.json())
    item_id = create_payload["itemId"]

    assert isinstance(item_id, str)

    response = await client.put(
        f"/v1/items/{item_id}",
        headers=test_headers,
        json={"quantity": 2.0, "version": 1},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_with_stale_version_returns_409(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    _ = test_user
    create_response = await client.post(
        "/v1/items",
        headers=test_headers,
        json={
            "display_name": "Yogurt",
            "quantity": 1.0,
            "unit": "cup",
            "storage_location": "fridge",
        },
    )
    create_payload = cast(dict[str, object], create_response.json())
    item_id = create_payload["itemId"]

    assert isinstance(item_id, str)

    response = await client.put(
        f"/v1/items/{item_id}",
        headers=test_headers,
        json={"quantity": 2.0, "version": 0},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Item version conflict"}


@pytest.mark.asyncio
async def test_version_increments_on_update(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    _ = test_user
    create_response = await client.post(
        "/v1/items",
        headers=test_headers,
        json={
            "display_name": "Butter",
            "quantity": 1.0,
            "unit": "pack",
            "storage_location": "fridge",
        },
    )
    create_payload = cast(dict[str, object], create_response.json())
    item_id = create_payload["itemId"]

    assert isinstance(item_id, str)

    response = await client.put(
        f"/v1/items/{item_id}",
        headers=test_headers,
        json={"quantity": 2.0, "version": 1},
    )

    assert response.status_code == 200
    assert response.json()["version"] == 2

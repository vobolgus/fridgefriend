# pyright: reportAny=false, reportUnusedParameter=false, reportUnusedCallResult=false, reportMissingImports=false, reportUnknownVariableType=false

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.idempotency import clear_cache
from app.models.user import User
from app.modules.inventory.dependencies import get_current_user


@pytest.fixture(autouse=True)
def _reset_idempotency_cache() -> None:
    clear_cache()


@pytest_asyncio.fixture
async def test_user(app: FastAPI, db_session: AsyncSession) -> AsyncIterator[User]:
    user = User(email="idempotency-test@example.com")
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
async def test_idempotency_key_deduplicates_item_creation(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    headers = {**test_headers, "Idempotency-Key": "test-key-create-123"}
    payload = {
        "display_name": "Milk",
        "quantity": 1.0,
        "unit": "L",
        "storage_location": "fridge",
    }

    r1 = await client.post("/v1/items", headers=headers, json=payload)
    r2 = await client.post("/v1/items", headers=headers, json=payload)

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] == r2.json()["id"]


@pytest.mark.asyncio
async def test_different_idempotency_keys_create_different_items(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    payload = {
        "display_name": "Eggs",
        "quantity": 12.0,
        "unit": "count",
        "storage_location": "fridge",
    }

    r1 = await client.post(
        "/v1/items",
        headers={**test_headers, "Idempotency-Key": "key-a"},
        json=payload,
    )
    r2 = await client.post(
        "/v1/items",
        headers={**test_headers, "Idempotency-Key": "key-b"},
        json=payload,
    )

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] != r2.json()["id"]


@pytest.mark.asyncio
async def test_no_idempotency_key_creates_duplicates(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    payload = {
        "display_name": "Butter",
        "quantity": 1.0,
        "unit": "pack",
        "storage_location": "fridge",
    }

    r1 = await client.post("/v1/items", headers=test_headers, json=payload)
    r2 = await client.post("/v1/items", headers=test_headers, json=payload)

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] != r2.json()["id"]


@pytest.mark.asyncio
async def test_idempotency_key_on_update_item(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    create_resp = await client.post(
        "/v1/items",
        headers=test_headers,
        json={
            "display_name": "Juice",
            "quantity": 1.0,
            "unit": "bottle",
            "storage_location": "fridge",
        },
    )
    item_id = create_resp.json()["id"]

    headers = {**test_headers, "Idempotency-Key": "update-key-1"}
    r1 = await client.patch(f"/v1/items/{item_id}", headers=headers, json={"quantity": 2.0})
    r2 = await client.patch(f"/v1/items/{item_id}", headers=headers, json={"quantity": 2.0})

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json() == r2.json()


@pytest.mark.asyncio
async def test_idempotency_key_on_status_update(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    create_resp = await client.post(
        "/v1/items",
        headers=test_headers,
        json={
            "display_name": "Bread",
            "quantity": 1.0,
            "unit": "loaf",
            "storage_location": "pantry",
        },
    )
    item_id = create_resp.json()["id"]

    headers = {**test_headers, "Idempotency-Key": "status-key-1"}
    r1 = await client.post(f"/v1/items/{item_id}/status", headers=headers, json={"status": "used"})
    r2 = await client.post(f"/v1/items/{item_id}/status", headers=headers, json={"status": "used"})

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json() == r2.json()


@pytest.mark.asyncio
async def test_idempotency_key_on_recommendations(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    headers = {**test_headers, "Idempotency-Key": "rec-key-1"}
    payload = {"servings": 2}

    r1 = await client.post("/v1/recommendations", headers=headers, json=payload)
    r2 = await client.post("/v1/recommendations", headers=headers, json=payload)

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json() == r2.json()


@pytest.mark.asyncio
async def test_idempotency_key_on_plans(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    headers = {**test_headers, "Idempotency-Key": "plan-key-1"}
    payload = {"days": 3}

    r1 = await client.post("/v1/plans", headers=headers, json=payload)
    r2 = await client.post("/v1/plans", headers=headers, json=payload)

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json() == r2.json()


@pytest.mark.asyncio
async def test_idempotency_key_isolated_across_endpoints(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    create_payload = {
        "display_name": "Apple",
        "quantity": 1.0,
        "unit": "piece",
        "storage_location": "bowl",
    }
    rec_payload = {"servings": 2}
    same_key = "shared-key-xyz"

    r_item = await client.post(
        "/v1/items",
        headers={**test_headers, "Idempotency-Key": same_key},
        json=create_payload,
    )
    r_rec = await client.post(
        "/v1/recommendations",
        headers={**test_headers, "Idempotency-Key": same_key},
        json=rec_payload,
    )

    assert r_item.status_code == 201
    assert r_rec.status_code == 200
    assert "display_name" in r_item.json()
    assert "recipes" in r_rec.json()


@pytest.mark.asyncio
async def test_idempotency_key_isolated_across_users(
    app: FastAPI,
    db_session: AsyncSession,
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    """Same idempotency key used by two different users must produce independent results."""
    same_key = "cross-user-key-abc"
    payload = {
        "display_name": "Tomato",
        "quantity": 3.0,
        "unit": "count",
        "storage_location": "fridge",
    }

    # First user (test_user) creates an item
    r_user1 = await client.post(
        "/v1/items",
        headers={**test_headers, "Idempotency-Key": same_key},
        json=payload,
    )
    assert r_user1.status_code == 201
    item_id_user1 = r_user1.json()["id"]

    # Second user with the SAME idempotency key — should get a NEW item, not the cached one
    user2 = User(email="user2-idempotency@example.com")
    db_session.add(user2)
    await db_session.commit()
    await db_session.refresh(user2)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    async def override_get_current_user_2() -> User:
        return user2

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user_2

    r_user2 = await client.post(
        "/v1/items",
        headers={**test_headers, "Idempotency-Key": same_key},
        json=payload,
    )

    app.dependency_overrides.clear()

    assert r_user2.status_code == 201
    # Different users → different item IDs even with same idempotency key
    assert r_user2.json()["id"] != item_id_user1

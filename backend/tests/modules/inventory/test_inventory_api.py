from __future__ import annotations

from datetime import date, timedelta
import uuid

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.inventory_item import InventoryStatus
from app.models.user import User
from app.modules.inventory.dependencies import get_current_user


@pytest_asyncio.fixture
async def test_user(app: FastAPI, db_session: AsyncSession) -> User:
    user = User(email="inventory-api@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    async def override_get_db() -> AsyncSession:
        yield db_session

    async def override_get_current_user() -> User:
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    yield user

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_item_success(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    response = await client.post(
        "/v1/items",
        headers=test_headers,
        json={
            "display_name": "Milk",
            "quantity": 1.5,
            "unit": "liters",
            "storage_location": "fridge",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["user_id"] == str(test_user.id)
    assert payload["display_name"] == "Milk"
    assert payload["status"] == "active"
    assert payload["source"] == "manual"
    assert payload["canonical_name"] == "Milk"
    assert payload["confidence"] == 0.5
    assert payload["estimated_expiry_date"] == str(date.today() + timedelta(days=7))


@pytest.mark.asyncio
async def test_create_item_missing_display_name(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    response = await client.post(
        "/v1/items",
        headers=test_headers,
        json={
            "quantity": 1.0,
            "unit": "liters",
            "storage_location": "fridge",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_item_invalid_quantity(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    response = await client.post(
        "/v1/items",
        headers=test_headers,
        json={
            "display_name": "Milk",
            "quantity": -1,
            "unit": "liters",
            "storage_location": "fridge",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_items_empty(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    response = await client.get("/v1/items", headers=test_headers)

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_items_returns_only_active(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    active_response = await client.post(
        "/v1/items",
        headers=test_headers,
        json={
            "display_name": "Milk",
            "quantity": 1.0,
            "unit": "liter",
            "storage_location": "fridge",
        },
    )
    used_response = await client.post(
        "/v1/items",
        headers=test_headers,
        json={
            "display_name": "Spinach",
            "quantity": 1.0,
            "unit": "bag",
            "storage_location": "fridge",
        },
    )

    used_item_id = used_response.json()["id"]
    await client.post(
        f"/v1/items/{used_item_id}/status",
        headers=test_headers,
        json={"status": "used"},
    )

    response = await client.get("/v1/items", headers=test_headers)

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == active_response.json()["id"]
    assert payload[0]["status"] == "active"


@pytest.mark.asyncio
async def test_get_item_by_id(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    create_response = await client.post(
        "/v1/items",
        headers=test_headers,
        json={
            "display_name": "Eggs",
            "quantity": 12,
            "unit": "count",
            "storage_location": "fridge",
        },
    )
    item_id = create_response.json()["id"]

    response = await client.get(f"/v1/items/{item_id}", headers=test_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == item_id
    assert payload["display_name"] == "Eggs"
    assert payload["unit"] == "count"


@pytest.mark.asyncio
async def test_get_item_not_found(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    response = await client.get(f"/v1/items/{uuid.uuid4()}", headers=test_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}


@pytest.mark.asyncio
async def test_update_item_quantity(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    create_response = await client.post(
        "/v1/items",
        headers=test_headers,
        json={
            "display_name": "Juice",
            "quantity": 1.0,
            "unit": "bottle",
            "storage_location": "fridge",
        },
    )
    item_id = create_response.json()["id"]

    response = await client.patch(
        f"/v1/items/{item_id}",
        headers=test_headers,
        json={"quantity": 2.0},
    )

    assert response.status_code == 200
    assert response.json()["quantity"] == 2.0


@pytest.mark.asyncio
async def test_update_item_partial(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    create_response = await client.post(
        "/v1/items",
        headers=test_headers,
        json={
            "display_name": "Butter",
            "quantity": 1.0,
            "unit": "pack",
            "storage_location": "fridge",
            "estimated_expiry_date": "2026-04-15",
            "confidence": 0.9,
        },
    )
    item_id = create_response.json()["id"]

    response = await client.patch(
        f"/v1/items/{item_id}",
        headers=test_headers,
        json={"storage_location": "freezer"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["storage_location"] == "freezer"
    assert payload["quantity"] == 1.0
    assert payload["unit"] == "pack"
    assert payload["estimated_expiry_date"] == "2026-04-15"


@pytest.mark.asyncio
async def test_mark_item_used(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    create_response = await client.post(
        "/v1/items",
        headers=test_headers,
        json={
            "display_name": "Tomatoes",
            "quantity": 3.0,
            "unit": "count",
            "storage_location": "counter",
        },
    )
    item_id = create_response.json()["id"]

    response = await client.post(
        f"/v1/items/{item_id}/status",
        headers=test_headers,
        json={"status": InventoryStatus.USED.value},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "used"


@pytest.mark.asyncio
async def test_mark_item_discarded(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    create_response = await client.post(
        "/v1/items",
        headers=test_headers,
        json={
            "display_name": "Lettuce",
            "quantity": 1.0,
            "unit": "head",
            "storage_location": "fridge",
        },
    )
    item_id = create_response.json()["id"]

    response = await client.post(
        f"/v1/items/{item_id}/status",
        headers=test_headers,
        json={"status": InventoryStatus.DISCARDED.value},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "discarded"


@pytest.mark.asyncio
async def test_mark_item_frozen(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    create_response = await client.post(
        "/v1/items",
        headers=test_headers,
        json={
            "display_name": "Bread",
            "quantity": 1.0,
            "unit": "loaf",
            "storage_location": "pantry",
        },
    )
    item_id = create_response.json()["id"]

    response = await client.post(
        f"/v1/items/{item_id}/status",
        headers=test_headers,
        json={"status": InventoryStatus.FROZEN.value},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "frozen"


@pytest.mark.asyncio
async def test_delete_item(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    create_response = await client.post(
        "/v1/items",
        headers=test_headers,
        json={
            "display_name": "Cheese",
            "quantity": 1.0,
            "unit": "block",
            "storage_location": "fridge",
        },
    )
    item_id = create_response.json()["id"]

    delete_response = await client.delete(f"/v1/items/{item_id}", headers=test_headers)
    get_response = await client.get(f"/v1/items/{item_id}", headers=test_headers)

    assert delete_response.status_code == 204
    assert get_response.status_code == 404
    assert get_response.json() == {"detail": "Item not found"}

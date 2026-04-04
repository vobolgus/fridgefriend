# pyright: reportAny=false, reportUnusedParameter=false, reportUnusedCallResult=false, reportMissingImports=false, reportUnknownVariableType=false

from __future__ import annotations

from collections.abc import AsyncIterator
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


def _headers(test_headers: dict[str, str], key: str) -> dict[str, str]:
    return {**test_headers, "Idempotency-Key": key}


@pytest_asyncio.fixture
async def test_user(app: FastAPI, db_session: AsyncSession) -> AsyncIterator[User]:
    user = User(email="inventory-api@example.com")
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
async def test_create_item_success(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    response = await client.post(
        "/v1/items",
        headers=_headers(test_headers, "inventory-create-success"),
        json={
            "display_name": "Milk",
            "quantity": 1.5,
            "unit": "liters",
            "storage_location": "fridge",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["itemId"]
    assert "id" not in payload
    assert payload["userId"] == str(test_user.id)
    assert payload["displayName"] == "Milk"
    assert payload["status"] == "active"
    assert payload["source"] == "manual"
    assert payload["canonicalName"] == "milk"
    assert payload["confidence"] == 0.95
    assert payload["estimatedExpiryDate"] == str(date.today() + timedelta(days=7))


@pytest.mark.asyncio
async def test_create_item_uses_shelf_life_rules_for_default_expiry(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    response = await client.post(
        "/v1/items",
        headers=_headers(test_headers, "inventory-create-expiry-rule"),
        json={
            "display_name": "Milk",
            "canonical_name": "milk",
            "quantity": 1.0,
            "unit": "liter",
            "storage_location": "fridge",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["estimatedExpiryDate"] == str(date.today() + timedelta(days=7))
    assert payload["confidence"] == 0.95


@pytest.mark.asyncio
async def test_create_item_preserves_photo_scan_confidence_without_expiry_date(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    response = await client.post(
        "/v1/items",
        headers=_headers(test_headers, "inventory-create-photo-confidence"),
        json={
            "display_name": "Mystery Greens",
            "quantity": 1.0,
            "unit": "bag",
            "storage_location": "fridge",
            "source": "photo",
            "confidence": 0.87,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["source"] == "photo"
    assert payload["confidence"] == 0.87


@pytest.mark.asyncio
async def test_create_item_missing_display_name(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    response = await client.post(
        "/v1/items",
        headers=_headers(test_headers, "inventory-create-missing-name"),
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
        headers=_headers(test_headers, "inventory-create-invalid-quantity"),
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
        headers=_headers(test_headers, "inventory-list-active-create"),
        json={
            "display_name": "Milk",
            "quantity": 1.0,
            "unit": "liter",
            "storage_location": "fridge",
        },
    )
    used_response = await client.post(
        "/v1/items",
        headers=_headers(test_headers, "inventory-list-used-create"),
        json={
            "display_name": "Spinach",
            "quantity": 1.0,
            "unit": "bag",
            "storage_location": "fridge",
        },
    )

    used_item_id = used_response.json()["itemId"]
    await client.post(
        f"/v1/items/{used_item_id}/status",
        headers=_headers(test_headers, "inventory-list-used-status"),
        json={"status": "used"},
    )

    response = await client.get("/v1/items", headers=test_headers)

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["itemId"] == active_response.json()["itemId"]
    assert payload[0]["status"] == "active"


@pytest.mark.asyncio
async def test_get_item_by_id(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    create_response = await client.post(
        "/v1/items",
        headers=_headers(test_headers, "inventory-get-create"),
        json={
            "display_name": "Eggs",
            "quantity": 12,
            "unit": "count",
            "storage_location": "fridge",
        },
    )
    item_id = create_response.json()["itemId"]

    response = await client.get(f"/v1/items/{item_id}", headers=test_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["itemId"] == item_id
    assert payload["displayName"] == "Eggs"
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
        headers=_headers(test_headers, "inventory-update-create"),
        json={
            "display_name": "Juice",
            "quantity": 1.0,
            "unit": "bottle",
            "storage_location": "fridge",
        },
    )
    item_id = create_response.json()["itemId"]

    response = await client.patch(
        f"/v1/items/{item_id}",
        headers=_headers(test_headers, "inventory-update-quantity"),
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
        headers=_headers(test_headers, "inventory-update-partial-create"),
        json={
            "display_name": "Butter",
            "quantity": 1.0,
            "unit": "pack",
            "storage_location": "fridge",
            "estimated_expiry_date": "2026-04-15",
            "confidence": 0.9,
        },
    )
    item_id = create_response.json()["itemId"]

    response = await client.patch(
        f"/v1/items/{item_id}",
        headers=_headers(test_headers, "inventory-update-partial-patch"),
        json={"storage_location": "freezer"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["storageLocation"] == "freezer"
    assert payload["quantity"] == 1.0
    assert payload["unit"] == "pack"
    # storage_location changed fridge→freezer so expiry is recalculated
    assert payload["estimatedExpiryDate"] != "2026-04-15"


@pytest.mark.asyncio
async def test_update_item_display_name_updates_canonical_name(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    create_response = await client.post(
        "/v1/items",
        headers=_headers(test_headers, "inventory-update-name-create"),
        json={
            "display_name": "Milk",
            "quantity": 1.0,
            "unit": "liter",
            "storage_location": "fridge",
        },
    )
    item_id = create_response.json()["itemId"]

    response = await client.patch(
        f"/v1/items/{item_id}",
        headers=_headers(test_headers, "inventory-update-name-patch"),
        json={"display_name": "Greek Yogurt"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["displayName"] == "Greek Yogurt"
    assert payload["canonicalName"] == "greek yogurt"


@pytest.mark.asyncio
async def test_mark_item_used(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    create_response = await client.post(
        "/v1/items",
        headers=_headers(test_headers, "inventory-status-used-create"),
        json={
            "display_name": "Tomatoes",
            "quantity": 3.0,
            "unit": "count",
            "storage_location": "counter",
        },
    )
    item_id = create_response.json()["itemId"]

    response = await client.post(
        f"/v1/items/{item_id}/status",
        headers=_headers(test_headers, "inventory-status-used"),
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
        headers=_headers(test_headers, "inventory-status-discarded-create"),
        json={
            "display_name": "Lettuce",
            "quantity": 1.0,
            "unit": "head",
            "storage_location": "fridge",
        },
    )
    item_id = create_response.json()["itemId"]

    response = await client.post(
        f"/v1/items/{item_id}/status",
        headers=_headers(test_headers, "inventory-status-discarded"),
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
        headers=_headers(test_headers, "inventory-status-frozen-create"),
        json={
            "display_name": "Bread",
            "quantity": 1.0,
            "unit": "loaf",
            "storage_location": "pantry",
        },
    )
    item_id = create_response.json()["itemId"]

    response = await client.post(
        f"/v1/items/{item_id}/status",
        headers=_headers(test_headers, "inventory-status-frozen"),
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
        headers=_headers(test_headers, "inventory-delete-create"),
        json={
            "display_name": "Cheese",
            "quantity": 1.0,
            "unit": "block",
            "storage_location": "fridge",
        },
    )
    item_id = create_response.json()["itemId"]

    delete_response = await client.delete(
        f"/v1/items/{item_id}",
        headers=_headers(test_headers, "inventory-delete"),
    )
    get_response = await client.get(f"/v1/items/{item_id}", headers=test_headers)

    assert delete_response.status_code == 204
    assert get_response.status_code == 404
    assert get_response.json() == {"detail": "Item not found"}


@pytest.mark.asyncio
async def test_undo_endpoint_restores_previous_state(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    create_response = await client.post(
        "/v1/items",
        headers=_headers(test_headers, "inventory-undo-create"),
        json={
            "display_name": "Yogurt",
            "quantity": 1.0,
            "unit": "cup",
            "storage_location": "fridge",
        },
    )
    item_id = create_response.json()["itemId"]

    update_response = await client.patch(
        f"/v1/items/{item_id}",
        headers=_headers(test_headers, "inventory-undo-update"),
        json={"quantity": 2.0, "storage_location": "freezer"},
    )
    assert update_response.status_code == 200

    undo_response = await client.post(
        f"/v1/items/{item_id}/undo",
        headers=_headers(test_headers, "inventory-undo-action"),
    )

    assert undo_response.status_code == 200
    payload = undo_response.json()
    assert payload["itemId"] == item_id
    assert payload["quantity"] == 1.0
    assert payload["storageLocation"] == "fridge"


@pytest.mark.asyncio
async def test_create_item_requires_idempotency_key(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    _ = test_user
    response = await client.post(
        "/v1/items",
        headers=test_headers,
        json={
            "display_name": "Milk",
            "quantity": 1.0,
            "unit": "liters",
            "storage_location": "fridge",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Idempotency-Key header is required"}

# pyright: reportAny=false, reportUnusedParameter=false, reportUnusedCallResult=false, reportMissingImports=false, reportUnknownVariableType=false

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import date, timedelta

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.events import InventoryEvent
from app.models.household import Household, HouseholdMember, HouseholdRole
from app.models.inventory_item import InventoryItem, InventorySource, InventoryStatus
from app.models.user import User
from app.modules.households.event_bus import household_event_bus
from app.modules.inventory.dependencies import get_current_user
from app.modules.inventory.repository import InventoryRepository
from app.modules.inventory.service import InventoryService


def _headers(test_headers: dict[str, str], key: str) -> dict[str, str]:
    return {**test_headers, "Idempotency-Key": key}


@pytest_asyncio.fixture
async def event_test_user(app: FastAPI, db_session: AsyncSession) -> AsyncIterator[tuple[User, Household]]:
    user = User(email="inventory-events@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    household = Household(name="Events Kitchen", invite_code="events-kitchen-code")
    db_session.add(household)
    await db_session.flush()
    db_session.add(HouseholdMember(household_id=household.id, user_id=user.id, role=HouseholdRole.OWNER))
    await db_session.commit()
    await db_session.refresh(household)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    async def override_get_current_user() -> User:
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    yield user, household

    app.dependency_overrides.clear()


async def _get_latest_event(db_session: AsyncSession, action: str) -> InventoryEvent:
    result = await db_session.execute(
        select(InventoryEvent)
        .where(InventoryEvent.action == action)
        .order_by(InventoryEvent.created_at.desc()),
    )
    event = result.scalars().first()
    assert event is not None
    return event


@pytest.mark.asyncio
async def test_create_item_emits_added_event(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    event_test_user: tuple[User, Household],
    db_session: AsyncSession,
) -> None:
    response = await client.post(
        "/v1/items",
        headers=_headers(test_headers, "inventory-events-create-added"),
        json={
            "display_name": "Milk",
            "quantity": 1.0,
            "unit": "liter",
            "storage_location": "fridge",
        },
    )

    assert response.status_code == 201
    event = await _get_latest_event(db_session, "added")
    assert event.action == "added"
    assert event.new_state["display_name"] == "Milk"


@pytest.mark.asyncio
async def test_update_status_emits_event_with_previous_state(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    event_test_user: tuple[User, Household],
    db_session: AsyncSession,
) -> None:
    create_response = await client.post(
        "/v1/items",
        headers=_headers(test_headers, "inventory-events-create-status"),
        json={
            "display_name": "Spinach",
            "quantity": 1.0,
            "unit": "bag",
            "storage_location": "fridge",
        },
    )
    item_id = create_response.json()["itemId"]

    response = await client.post(
        f"/v1/items/{item_id}/status",
        headers=_headers(test_headers, "inventory-events-status-update"),
        json={"status": "used"},
    )

    assert response.status_code == 200
    event = await _get_latest_event(db_session, "status_updated")
    assert event.previous_state["status"] == "active"
    assert event.new_state["status"] == "used"


@pytest.mark.asyncio
async def test_delete_item_emits_removed_event(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    event_test_user: tuple[User, Household],
    db_session: AsyncSession,
) -> None:
    create_response = await client.post(
        "/v1/items",
        headers=_headers(test_headers, "inventory-events-create-delete"),
        json={
            "display_name": "Cheese",
            "quantity": 1.0,
            "unit": "block",
            "storage_location": "fridge",
        },
    )
    item_id = create_response.json()["itemId"]

    response = await client.delete(
        f"/v1/items/{item_id}",
        headers=_headers(test_headers, "inventory-events-delete"),
    )

    assert response.status_code == 204
    event = await _get_latest_event(db_session, "removed")
    assert event.action == "removed"
    assert event.previous_state["display_name"] == "Cheese"


@pytest.mark.asyncio
async def test_delete_item_nulls_event_item_id_after_delete(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    event_test_user: tuple[User, Household],
    db_session: AsyncSession,
) -> None:
    create_response = await client.post(
        "/v1/items",
        headers=_headers(test_headers, "inventory-events-null-create"),
        json={
            "display_name": "Butter",
            "quantity": 1.0,
            "unit": "pack",
            "storage_location": "fridge",
        },
    )
    item_id = create_response.json()["itemId"]

    delete_response = await client.delete(
        f"/v1/items/{item_id}",
        headers=_headers(test_headers, "inventory-events-null-delete"),
    )

    assert delete_response.status_code == 204
    event = await _get_latest_event(db_session, "removed")
    assert event.item_id is None


@pytest.mark.asyncio
async def test_undo_last_event_restores_previous_state(
    event_test_user: tuple[User, Household],
    db_session: AsyncSession,
) -> None:
    user, household = event_test_user
    item = InventoryItem(
        user_id=user.id,
        household_id=household.id,
        display_name="Tomato",
        quantity=2.0,
        unit="count",
        storage_location="counter",
        estimated_expiry_date=date.today() + timedelta(days=4),
        confidence=0.9,
        status=InventoryStatus.ACTIVE,
        source=InventorySource.MANUAL,
        canonical_name="tomato",
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)

    service = InventoryService(InventoryRepository(db_session))
    await service.update_status(item.id, user, household.id, InventoryStatus.USED)

    restored = await service.undo_last_event(item.id, user, household.id)

    assert restored.status == InventoryStatus.ACTIVE


@pytest.mark.asyncio
async def test_undo_last_event_emits_undone_event_and_sse_payload(
    event_test_user: tuple[User, Household],
    db_session: AsyncSession,
) -> None:
    user, household = event_test_user
    item = InventoryItem(
        user_id=user.id,
        household_id=household.id,
        display_name="Yogurt",
        quantity=1.0,
        unit="cup",
        storage_location="fridge",
        estimated_expiry_date=date.today() + timedelta(days=3),
        confidence=0.88,
        status=InventoryStatus.ACTIVE,
        source=InventorySource.MANUAL,
        canonical_name="yogurt",
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)

    service = InventoryService(InventoryRepository(db_session))
    await service.update_status(item.id, user, household.id, InventoryStatus.USED)

    async with household_event_bus.subscribe(household.id) as queue:
        restored = await service.undo_last_event(item.id, user, household.id)
        event = await queue.get()

    undone_event = await _get_latest_event(db_session, "undone")

    assert restored.status == InventoryStatus.ACTIVE
    assert undone_event.item_id == item.id
    assert undone_event.previous_state["status"] == "used"
    assert undone_event.new_state["status"] == "active"
    assert event["action"] == "undone"
    assert event["item_id"] == str(item.id)
    assert event["new_state"]["status"] == "active"

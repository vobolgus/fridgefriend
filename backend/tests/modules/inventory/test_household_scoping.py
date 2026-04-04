# pyright: reportAny=false, reportUnusedParameter=false, reportUnusedCallResult=false, reportMissingImports=false, reportUnknownVariableType=false

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import date, timedelta
from uuid import UUID
import uuid

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.household import Household, HouseholdMember, HouseholdRole
from app.models.inventory_item import InventoryItem, InventorySource, InventoryStatus
from app.models.user import User
from app.modules.inventory.dependencies import get_active_household_id, get_current_user


def _headers(test_headers: dict[str, str], key: str) -> dict[str, str]:
    return {**test_headers, "Idempotency-Key": key}


@pytest_asyncio.fixture
async def scoped_users(app: FastAPI, db_session: AsyncSession) -> AsyncIterator[tuple[User, User]]:
    user_1 = User(email="inventory-scope-user-1@example.com")
    user_2 = User(email="inventory-scope-user-2@example.com")
    db_session.add_all([user_1, user_2])
    await db_session.commit()
    await db_session.refresh(user_1)
    await db_session.refresh(user_2)

    household_1 = Household(name="User 1 Kitchen", invite_code="scope-user-1-code")
    household_2 = Household(name="User 2 Kitchen", invite_code="scope-user-2-code")
    db_session.add_all([household_1, household_2])
    await db_session.flush()
    db_session.add_all(
        [
            HouseholdMember(household_id=household_1.id, user_id=user_1.id, role=HouseholdRole.OWNER),
            HouseholdMember(household_id=household_2.id, user_id=user_2.id, role=HouseholdRole.OWNER),
        ],
    )
    await db_session.commit()

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    async def override_get_current_user_1() -> User:
        return user_1

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user_1

    yield (user_1, user_2)

    app.dependency_overrides.clear()


async def _create_inventory_item(
    db_session: AsyncSession,
    user: User,
    household_id: UUID,
    name: str,
) -> InventoryItem:
    item = InventoryItem(
        user_id=user.id,
        household_id=household_id,
        display_name=name,
        quantity=1.0,
        unit="unit",
        storage_location="fridge",
        estimated_expiry_date=date.today() + timedelta(days=7),
        confidence=0.9,
        status=InventoryStatus.ACTIVE,
        source=InventorySource.MANUAL,
        canonical_name=name.lower(),
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


@pytest.mark.asyncio
async def test_items_filtered_by_household(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    scoped_users: tuple[User, User],
    db_session: AsyncSession,
) -> None:
    user_1, user_2 = scoped_users
    member_1 = (
        await db_session.execute(
            select(HouseholdMember).where(HouseholdMember.user_id == user_1.id),
        )
    ).scalar_one_or_none()
    member_2 = (
        await db_session.execute(
            select(HouseholdMember).where(HouseholdMember.user_id == user_2.id),
        )
    ).scalar_one_or_none()
    assert member_1 is not None
    assert member_2 is not None

    await _create_inventory_item(db_session, user_1, member_1.household_id, "Milk")
    await _create_inventory_item(db_session, user_2, member_2.household_id, "Banana")

    response = await client.get("/v1/items", headers=test_headers)

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["displayName"] == "Milk"


@pytest.mark.asyncio
async def test_create_item_assigns_to_active_household(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    scoped_users: tuple[User, User],
    db_session: AsyncSession,
) -> None:
    user_1, _ = scoped_users
    member_1 = (
        await db_session.execute(
            select(HouseholdMember).where(HouseholdMember.user_id == user_1.id),
        )
    ).scalar_one_or_none()
    assert member_1 is not None

    response = await client.post(
        "/v1/items",
        headers=_headers(test_headers, "household-scope-create-item"),
        json={
            "display_name": "Yogurt",
            "quantity": 1.0,
            "unit": "cup",
            "storage_location": "fridge",
        },
    )

    assert response.status_code == 201
    item_id = response.json()["itemId"]
    item = await db_session.get(InventoryItem, uuid.UUID(item_id))
    assert item is not None
    assert item.household_id == member_1.household_id


@pytest.mark.asyncio
async def test_cannot_access_other_household_items(
    client: httpx.AsyncClient,
    app: FastAPI,
    test_headers: dict[str, str],
    scoped_users: tuple[User, User],
    db_session: AsyncSession,
) -> None:
    user_1, user_2 = scoped_users
    member_2 = (
        await db_session.execute(
            select(HouseholdMember).where(HouseholdMember.user_id == user_2.id),
        )
    ).scalar_one_or_none()
    assert member_2 is not None

    other_item = await _create_inventory_item(db_session, user_2, member_2.household_id, "External Item")

    async def override_get_current_user_2(authorization: str | None = None, *, db: object | None = None) -> User:
        _ = authorization, db
        return user_1

    app.dependency_overrides[get_current_user] = override_get_current_user_2

    response = await client.get(f"/v1/items/{other_item.id}", headers=test_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}


@pytest.mark.asyncio
async def test_household_member_can_view_update_and_delete_shared_item(
    client: httpx.AsyncClient,
    app: FastAPI,
    test_headers: dict[str, str],
    scoped_users: tuple[User, User],
    db_session: AsyncSession,
) -> None:
    user_1, user_2 = scoped_users
    shared_household = Household(name="Shared Kitchen", invite_code="shared-kitchen-code")
    db_session.add(shared_household)
    await db_session.flush()
    db_session.add_all(
        [
            HouseholdMember(household_id=shared_household.id, user_id=user_1.id, role=HouseholdRole.OWNER),
            HouseholdMember(household_id=shared_household.id, user_id=user_2.id, role=HouseholdRole.MEMBER),
        ],
    )
    await db_session.commit()

    async def override_get_current_user_1() -> User:
        return user_1

    async def override_get_current_user_2() -> User:
        return user_2

    async def override_active_household_id() -> UUID:
        return shared_household.id

    app.dependency_overrides[get_current_user] = override_get_current_user_1
    app.dependency_overrides[get_active_household_id] = override_active_household_id
    create_response = await client.post(
        "/v1/items",
        headers=_headers(test_headers, "household-scope-shared-create"),
        json={
            "display_name": "Shared Milk",
            "quantity": 1.0,
            "unit": "liter",
            "storage_location": "fridge",
        },
    )

    assert create_response.status_code == 201
    item_id = create_response.json()["itemId"]

    app.dependency_overrides[get_current_user] = override_get_current_user_2

    list_response = await client.get("/v1/items", headers=test_headers)
    assert list_response.status_code == 200
    assert [item["displayName"] for item in list_response.json()] == ["Shared Milk"]

    get_response = await client.get(f"/v1/items/{item_id}", headers=test_headers)
    assert get_response.status_code == 200
    assert get_response.json()["itemId"] == item_id

    update_response = await client.patch(
        f"/v1/items/{item_id}",
        headers=_headers(test_headers, "household-scope-shared-update"),
        json={"quantity": 2.0},
    )
    assert update_response.status_code == 200
    assert update_response.json()["quantity"] == 2.0

    delete_response = await client.delete(
        f"/v1/items/{item_id}",
        headers=_headers(test_headers, "household-scope-shared-delete"),
    )
    assert delete_response.status_code == 204

    missing_response = await client.get(f"/v1/items/{item_id}", headers=test_headers)
    assert missing_response.status_code == 404

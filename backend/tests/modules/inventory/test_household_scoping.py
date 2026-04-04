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
from app.modules.inventory.dependencies import get_current_user


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
    assert payload[0]["display_name"] == "Milk"


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
        headers=test_headers,
        json={
            "display_name": "Yogurt",
            "quantity": 1.0,
            "unit": "cup",
            "storage_location": "fridge",
        },
    )

    assert response.status_code == 201
    item_id = response.json()["id"]
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

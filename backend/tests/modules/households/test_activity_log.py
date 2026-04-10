# pyright: reportAny=false, reportUnusedParameter=false, reportUnusedCallResult=false, reportMissingImports=false, reportUnknownVariableType=false

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.events import InventoryEvent
from app.models.household import Household, HouseholdMember, HouseholdRole
from app.models.inventory_item import InventoryItem, InventorySource, InventoryStatus
from app.models.user import User
from app.modules.inventory.dependencies import get_current_user


@pytest_asyncio.fixture
async def activity_test_context(app: FastAPI, db_session: AsyncSession) -> AsyncIterator[tuple[User, Household, Household]]:
    user = User(email="activity-log@example.com")
    other_user = User(email="activity-other@example.com")
    db_session.add_all([user, other_user])
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(other_user)

    household = Household(name="Activity Kitchen", invite_code="activity-kitchen")
    other_household = Household(name="Other Kitchen", invite_code="other-kitchen-activity")
    db_session.add_all([household, other_household])
    await db_session.flush()
    db_session.add_all(
        [
            HouseholdMember(household_id=household.id, user_id=user.id, role=HouseholdRole.OWNER),
            HouseholdMember(household_id=other_household.id, user_id=other_user.id, role=HouseholdRole.OWNER),
        ],
    )
    await db_session.commit()
    await db_session.refresh(household)
    await db_session.refresh(other_household)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    async def override_get_current_user() -> User:
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    yield user, household, other_household

    app.dependency_overrides.clear()


async def _add_inventory_event(
    db_session: AsyncSession,
    *,
    household: Household,
    user: User,
    action: str,
    display_name: str,
) -> None:
    item = InventoryItem(
        user_id=user.id,
        household_id=household.id,
        display_name=display_name,
        quantity=1.0,
        unit="count",
        storage_location="fridge",
        estimated_expiry_date=user.created_at.date(),
        confidence=0.9,
        status=InventoryStatus.ACTIVE,
        source=InventorySource.MANUAL,
        canonical_name=display_name.lower(),
    )
    db_session.add(item)
    await db_session.flush()
    db_session.add(
        InventoryEvent(
            household_id=household.id,
            user_id=user.id,
            item_id=item.id,
            action=action,
            previous_state={},
            new_state={"display_name": display_name},
        ),
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_get_activity_log_returns_recent_events(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    activity_test_context: tuple[User, Household, Household],
    db_session: AsyncSession,
) -> None:
    user, household, _ = activity_test_context
    await _add_inventory_event(db_session, household=household, user=user, action="added", display_name="Milk")

    response = await client.get(f"/v1/households/{household.id}/activity", headers=test_headers)

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["action"] == "added"


@pytest.mark.asyncio
async def test_activity_log_paginated(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    activity_test_context: tuple[User, Household, Household],
    db_session: AsyncSession,
) -> None:
    user, household, _ = activity_test_context
    await _add_inventory_event(db_session, household=household, user=user, action="added", display_name="Milk")
    await _add_inventory_event(db_session, household=household, user=user, action="updated", display_name="Eggs")

    response = await client.get(
        f"/v1/households/{household.id}/activity?limit=1&offset=1",
        headers=test_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1


@pytest.mark.asyncio
async def test_activity_log_filtered_by_household(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    activity_test_context: tuple[User, Household, Household],
    db_session: AsyncSession,
) -> None:
    user, household, other_household = activity_test_context
    await _add_inventory_event(db_session, household=household, user=user, action="added", display_name="Milk")
    other_user = User(email="third-activity@example.com")
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)
    await _add_inventory_event(db_session, household=other_household, user=other_user, action="removed", display_name="Bread")

    response = await client.get(f"/v1/households/{household.id}/activity", headers=test_headers)

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["new_state"]["display_name"] == "Milk"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query_string", "error_field", "invalid_value"),
    [
        ("limit=0", "limit", 0),
        ("limit=101", "limit", 101),
        ("offset=-1", "offset", -1),
    ],
)
async def test_activity_log_rejects_out_of_bounds_pagination(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    activity_test_context: tuple[User, Household, Household],
    query_string: str,
    error_field: str,
    invalid_value: int,
) -> None:
    _, household, _ = activity_test_context

    response = await client.get(
        f"/v1/households/{household.id}/activity?{query_string}",
        headers=test_headers,
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["detail"][0]["loc"][-1] == error_field
    assert payload["detail"][0]["input"] == str(invalid_value)

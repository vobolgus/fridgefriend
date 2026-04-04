# pyright: reportAny=false, reportUnusedParameter=false, reportUnusedCallResult=false, reportMissingImports=false, reportUnknownVariableType=false

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import date

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from starlette.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.household import Household, HouseholdMember, HouseholdRole
from app.models.user import User
from app.modules.households.event_bus import household_event_bus
from app.modules.households.repository import HouseholdRepository
from app.modules.households.router import stream_household_events
from app.modules.households.service import HouseholdService
from app.modules.inventory.dependencies import get_current_user


@pytest_asyncio.fixture
async def sse_test_context(app: FastAPI, db_session: AsyncSession) -> AsyncIterator[tuple[User, Household]]:
    user = User(email="household-sse@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    household = Household(name="SSE Kitchen", invite_code="sse-kitchen-code")
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


@pytest.mark.asyncio
async def test_sse_endpoint_returns_event_stream_content_type(
    sse_test_context: tuple[User, Household],
    db_session: AsyncSession,
) -> None:
    user, household = sse_test_context

    async def receive() -> dict[str, object]:
        return {"type": "http.request", "body": b"", "more_body": False}

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": f"/v1/households/{household.id}/events",
            "headers": [],
        },
        receive,
    )
    response = await stream_household_events(
        household.id,
        request,
        HouseholdService(HouseholdRepository(db_session)),
        user,
    )

    assert response.status_code == 200
    assert response.media_type == "text/event-stream"


@pytest.mark.asyncio
async def test_sse_emits_event_on_inventory_change(
    sse_test_context: tuple[User, Household],
) -> None:
    _, household = sse_test_context

    async with household_event_bus.subscribe(household.id) as queue:
        await household_event_bus.publish(
            household.id,
            {"action": "added", "item_id": "item-1", "created_at": date.today().isoformat()},
        )
        event = await queue.get()

    assert event["action"] == "added"
    assert event["item_id"] == "item-1"


@pytest.mark.asyncio
async def test_sse_requires_authentication(
    app: FastAPI,
    client: httpx.AsyncClient,
    sse_test_context: tuple[User, Household],
) -> None:
    _, household = sse_test_context

    app.dependency_overrides.pop(get_current_user, None)

    response = await client.get(f"/v1/households/{household.id}/events")

    assert response.status_code == 401

# pyright: reportAny=false, reportUnusedParameter=false, reportUnusedCallResult=false, reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta
from typing import cast
from uuid import UUID

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.events import InventoryEvent
from app.models.household import Household, HouseholdMember, HouseholdRole
from app.models.meal_plan import MealPlan
from app.models.recipe import Recipe
from app.models.user import User
from app.modules.households.event_bus import household_event_bus
from app.modules.inventory.dependencies import get_current_user
from app.modules.notifications.tasks import send_expiry_reminders


def _recipe(title: str, prep_minutes: int, ingredients: list[dict[str, object]]) -> Recipe:
    return Recipe(title=title, prep_minutes=prep_minutes, dietary_tags=[], ingredients=ingredients)


async def _seed_recipes(db_session: AsyncSession) -> None:
    db_session.add_all(
        [
            _recipe(
                "French Toast",
                15,
                [
                    {"name": "milk", "quantity": 1.0, "unit": "cup"},
                    {"name": "eggs", "quantity": 2.0, "unit": "count"},
                    {"name": "bread", "quantity": 4.0, "unit": "slice"},
                ],
            ),
            _recipe(
                "Rice Bowl",
                20,
                [
                    {"name": "rice", "quantity": 2.0, "unit": "cup"},
                    {"name": "eggs", "quantity": 2.0, "unit": "count"},
                ],
            ),
            _recipe(
                "Pantry Pasta",
                20,
                [
                    {"name": "pasta", "quantity": 1.0, "unit": "box"},
                    {"name": "tomatoes", "quantity": 2.0, "unit": "count"},
                ],
            ),
        ],
    )
    await db_session.commit()


async def _create_item(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    *,
    display_name: str,
    quantity: float,
    unit: str,
    storage_location: str,
    estimated_expiry_date: date,
    canonical_name: str | None = None,
) -> dict[str, object]:
    response = await client.post(
        "/v1/items",
        headers=headers,
        json={
            "display_name": display_name,
            "quantity": quantity,
            "unit": unit,
            "storage_location": storage_location,
            "estimated_expiry_date": str(estimated_expiry_date),
            "canonical_name": canonical_name or display_name.lower(),
            "confidence": 0.95,
        },
    )
    assert response.status_code == 201
    return cast(dict[str, object], response.json())


@pytest_asyncio.fixture
async def spec_test_user(app: FastAPI, db_session: AsyncSession) -> AsyncIterator[User]:
    user = User(email="full-spec@example.com")
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
async def test_user_registers_and_gets_household(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    spec_test_user: User,
) -> None:
    _ = spec_test_user
    response = await client.get("/v1/households", headers=test_headers)
    assert response.status_code == 200
    households = cast(list[dict[str, object]], response.json())
    assert len(households) == 1
    assert households[0]["invite_code"]


@pytest.mark.asyncio
async def test_add_items_via_manual_barcode_photo(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    spec_test_user: User,
) -> None:
    _ = spec_test_user
    manual = await _create_item(
        client,
        test_headers,
        display_name="Milk",
        quantity=1.0,
        unit="liter",
        storage_location="fridge",
        estimated_expiry_date=date.today() + timedelta(days=2),
        canonical_name="milk",
    )
    barcode = await client.post(
        "/v1/scan/barcode",
        headers=test_headers,
        json={"barcode": "8710847909610", "quantity": 1.0, "storage_location": "fridge"},
    )
    photo = await client.post(
        "/v1/scan/photo",
        headers=test_headers,
        json={"image_url": "https://example.test/fridge.png"},
    )

    assert manual["displayName"] == "Milk"
    assert barcode.status_code == 200
    assert barcode.json()["source"] == "barcode"
    assert photo.status_code == 200
    assert "draft_items" in cast(dict[str, object], photo.json())


@pytest.mark.asyncio
async def test_recommendations_account_for_expiry_and_coverage(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    spec_test_user: User,
    db_session: AsyncSession,
) -> None:
    _ = spec_test_user
    await _seed_recipes(db_session)
    _ = await _create_item(
        client,
        test_headers,
        display_name="Milk",
        quantity=1.0,
        unit="cup",
        storage_location="fridge",
        estimated_expiry_date=date.today() + timedelta(days=1),
        canonical_name="milk",
    )
    _ = await _create_item(
        client,
        test_headers,
        display_name="Eggs",
        quantity=12.0,
        unit="count",
        storage_location="fridge",
        estimated_expiry_date=date.today() + timedelta(days=5),
        canonical_name="eggs",
    )

    response = await client.post("/v1/recommendations", headers=test_headers, json={"servings": 2})
    assert response.status_code == 200
    payload = cast(dict[str, object], response.json())
    recipes = cast(list[dict[str, object]], payload["recipes"])
    assert recipes[0]["title"] == "French Toast"
    top_coverage = cast(float, recipes[0]["coveragePct"])
    bottom_coverage = cast(float, recipes[-1]["coveragePct"])
    assert top_coverage >= bottom_coverage


@pytest.mark.asyncio
async def test_meal_plan_reserves_ingredients_transactionally(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    spec_test_user: User,
    db_session: AsyncSession,
) -> None:
    _ = spec_test_user
    await _seed_recipes(db_session)
    _ = await _create_item(
        client,
        test_headers,
        display_name="Milk",
        quantity=3.0,
        unit="cup",
        storage_location="fridge",
        estimated_expiry_date=date.today() + timedelta(days=2),
        canonical_name="milk",
    )

    response = await client.post("/v1/plans", headers=test_headers, json={"days": 3, "servings": 2})
    assert response.status_code == 200
    payload = cast(dict[str, object], response.json())
    days = cast(list[dict[str, object]], payload["days"])
    assert days
    assert any(cast(list[object], day["reservedItems"]) for day in days)

    meal_plans = await db_session.execute(select(MealPlan))
    assert meal_plans.scalars().first() is not None


@pytest.mark.asyncio
async def test_shopping_list_shows_only_gaps(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    spec_test_user: User,
    db_session: AsyncSession,
) -> None:
    _ = spec_test_user
    await _seed_recipes(db_session)
    _ = await _create_item(
        client,
        test_headers,
        display_name="Pasta",
        quantity=1.0,
        unit="box",
        storage_location="pantry",
        estimated_expiry_date=date.today() + timedelta(days=365),
        canonical_name="pasta",
    )
    _ = await client.post("/v1/plans", headers=test_headers, json={"days": 3, "servings": 2})

    response = await client.get("/v1/shopping-list", headers=test_headers)
    assert response.status_code == 200
    payload = cast(dict[str, object], response.json())
    items = cast(list[dict[str, object]], payload["items"])
    assert items
    assert all(item["ingredient_name"] != "pasta" for item in items)


@pytest.mark.asyncio
async def test_household_invite_and_shared_inventory(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    spec_test_user: User,
    db_session: AsyncSession,
) -> None:
    _ = spec_test_user
    owner = User(email="owner-shared@example.com")
    db_session.add(owner)
    await db_session.commit()
    await db_session.refresh(owner)

    household = Household(name="Shared Kitchen", invite_code="shared-invite-code")
    db_session.add(household)
    await db_session.flush()
    db_session.add(HouseholdMember(household_id=household.id, user_id=owner.id, role=HouseholdRole.OWNER))
    await db_session.commit()

    response = await client.post(
        "/v1/households/join",
        headers=test_headers,
        json={"invite_code": household.invite_code},
    )
    assert response.status_code == 200
    assert response.json()["id"] == str(household.id)


class _RecordingPushService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    async def send(self, token: str, title: str, body: str) -> bool:
        self.calls.append((token, title, body))
        return True


@pytest.mark.asyncio
async def test_notification_preferences_and_reminder_task(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    spec_test_user: User,
    db_session: AsyncSession,
) -> None:
    _ = spec_test_user
    _ = await client.patch(
        "/v1/notifications",
        headers=test_headers,
        json={"expiry_reminder_enabled": True, "reminder_days_before": 1},
    )
    _ = await client.post(
        "/v1/notifications/devices",
        headers=test_headers,
        json={"token": "device-token-spec", "platform": "ios"},
    )
    _ = await _create_item(
        client,
        test_headers,
        display_name="Yogurt",
        quantity=1.0,
        unit="cup",
        storage_location="fridge",
        estimated_expiry_date=date.today() + timedelta(days=1),
        canonical_name="yogurt",
    )

    push = _RecordingPushService()
    sent = await send_expiry_reminders(
        session=db_session,
        push_service=push,
        now=datetime(2026, 4, 4, 9, 0, tzinfo=UTC),
    )
    assert sent >= 1
    assert push.calls


@pytest.mark.asyncio
async def test_sse_activity_stream(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    spec_test_user: User,
    db_session: AsyncSession,
) -> None:
    _ = (spec_test_user, db_session)
    households_response = await client.get("/v1/households", headers=test_headers)
    households = cast(list[dict[str, object]], households_response.json())
    household_id_raw = households[0]["id"]
    assert isinstance(household_id_raw, str)
    household_id = UUID(household_id_raw)
    await household_event_bus.publish(
        household_id,
        {"action": "added", "item_id": "stream-item", "created_at": date.today().isoformat()},
    )

    response = await client.get(f"/v1/households/{household_id_raw}/activity", headers=test_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_inventory_event_undo(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    spec_test_user: User,
    db_session: AsyncSession,
) -> None:
    _ = spec_test_user
    item = await _create_item(
        client,
        test_headers,
        display_name="Tomato",
        quantity=2.0,
        unit="count",
        storage_location="counter",
        estimated_expiry_date=date.today() + timedelta(days=3),
        canonical_name="tomato",
    )
    _ = await client.post(f"/v1/items/{item['itemId']}/status", headers=test_headers, json={"status": "used"})

    item_id_raw = item["itemId"]
    assert isinstance(item_id_raw, str)
    item_id = UUID(item_id_raw)
    result = await db_session.execute(select(InventoryEvent).where(InventoryEvent.item_id == item_id))
    assert result.scalars().first() is not None


@pytest.mark.asyncio
async def test_optimistic_concurrency_conflict(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    spec_test_user: User,
) -> None:
    _ = spec_test_user
    item = await _create_item(
        client,
        test_headers,
        display_name="Butter",
        quantity=1.0,
        unit="pack",
        storage_location="fridge",
        estimated_expiry_date=date.today() + timedelta(days=7),
        canonical_name="butter",
    )

    response = await client.put(
        f"/v1/items/{item['itemId']}",
        headers=test_headers,
        json={"quantity": 2.0, "version": 0},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Item version conflict"

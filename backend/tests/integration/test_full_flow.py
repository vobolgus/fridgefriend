# pyright: reportAny=false, reportUnusedParameter=false, reportUnusedCallResult=false, reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import date, timedelta

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.recipe import Recipe
from app.models.user import User
from app.modules.inventory.dependencies import get_current_user


def _recipe(
    title: str,
    prep_minutes: int,
    ingredients: list[dict[str, object]],
    dietary_tags: list[str] | None = None,
) -> Recipe:
    return Recipe(
        title=title,
        prep_minutes=prep_minutes,
        dietary_tags=dietary_tags or [],
        ingredients=ingredients,
    )


async def _seed_recipes(db_session: AsyncSession, recipes: list[Recipe]) -> None:
    db_session.add_all(recipes)
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
    return response.json()


@pytest_asyncio.fixture
async def integration_user(app: FastAPI, db_session: AsyncSession) -> AsyncIterator[User]:
    user = User(email="integration-tests@example.com")
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
async def test_full_user_journey(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    integration_user: User,
    db_session: AsyncSession,
) -> None:
    await _seed_recipes(
        db_session,
        [
            _recipe(
                "French Toast Bake",
                15,
                [
                    {"name": "milk", "quantity": 1.0, "unit": "cup"},
                    {"name": "eggs", "quantity": 2.0, "unit": "count"},
                    {"name": "bread", "quantity": 4.0, "unit": "slice"},
                ],
                ["vegetarian"],
            ),
            _recipe(
                "Creamy Pasta",
                20,
                [
                    {"name": "pasta", "quantity": 1.0, "unit": "box"},
                    {"name": "milk", "quantity": 1.0, "unit": "cup"},
                    {"name": "cheese", "quantity": 1.0, "unit": "cup"},
                ],
                ["vegetarian"],
            ),
            _recipe(
                "Egg Rice Bowl",
                18,
                [
                    {"name": "eggs", "quantity": 2.0, "unit": "count"},
                    {"name": "rice", "quantity": 2.0, "unit": "cup"},
                ],
            ),
        ],
    )

    milk = await _create_item(
        client,
        test_headers,
        display_name="Milk",
        quantity=3.0,
        unit="cup",
        storage_location="fridge",
        estimated_expiry_date=date.today() + timedelta(days=2),
        canonical_name="milk",
    )
    await _create_item(
        client,
        test_headers,
        display_name="Eggs",
        quantity=12.0,
        unit="count",
        storage_location="fridge",
        estimated_expiry_date=date.today() + timedelta(days=5),
        canonical_name="eggs",
    )
    await _create_item(
        client,
        test_headers,
        display_name="Pasta",
        quantity=1.0,
        unit="box",
        storage_location="pantry",
        estimated_expiry_date=date.today() + timedelta(days=730),
        canonical_name="pasta",
    )

    items_response = await client.get("/v1/items", headers=test_headers)

    assert items_response.status_code == 200
    items_payload = items_response.json()
    assert len(items_payload) == 3
    assert {item["displayName"] for item in items_payload} == {"Milk", "Eggs", "Pasta"}
    assert {item["status"] for item in items_payload} == {"active"}

    recommendations_response = await client.post(
        "/v1/recommendations",
        headers=test_headers,
        json={"servings": 2},
    )

    assert recommendations_response.status_code == 200
    recommendation_titles = [recipe["title"] for recipe in recommendations_response.json()["recipes"][:3]]
    assert recommendation_titles[0] == "French Toast"
    assert "Scrambled Eggs" in recommendation_titles

    plan_response = await client.post(
        "/v1/plans",
        headers=test_headers,
        json={"days": 3, "servings": 2},
    )

    assert plan_response.status_code == 200
    plan_payload = plan_response.json()["plan"]
    assert len(plan_payload["days"]) == 3
    assert all(day["recipeId"] for day in plan_payload["days"])

    shopping_response = await client.get("/v1/shopping-list", headers=test_headers)

    assert shopping_response.status_code == 200
    shopping_items = shopping_response.json()["items"]
    assert shopping_items
    shopping_ingredient_names = {item["ingredientName"] for item in shopping_items}
    assert any(name not in {"milk", "eggs", "pasta"} for name in shopping_ingredient_names)
    assert shopping_ingredient_names & {"bread", "cheese", "rice"}

    status_response = await client.post(
        f"/v1/items/{milk['itemId']}/status",
        headers=test_headers,
        json={"status": "used"},
    )

    assert status_response.status_code == 200

    remaining_items_response = await client.get("/v1/items", headers=test_headers)

    assert remaining_items_response.status_code == 200
    remaining_items = remaining_items_response.json()
    assert len(remaining_items) == 2
    assert {item["displayName"] for item in remaining_items} == {"Eggs", "Pasta"}


@pytest.mark.asyncio
async def test_barcode_scan_and_expiry(
    client: httpx.AsyncClient,
    integration_user: User,
) -> None:
    response = await client.post(
        "/v1/scan/barcode",
        headers={"Authorization": "Bearer test-token"},
        json={
            "barcode": "8710847909610",
            "quantity": 1.0,
            "storage_location": "fridge",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["canonical_name"] == "milk"
    assert payload["display_name"] == "Whole Milk 1L"
    assert payload["source"] == "barcode"


@pytest.mark.asyncio
async def test_recommendations_with_urgency(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    integration_user: User,
) -> None:
    await _create_item(
        client,
        test_headers,
        display_name="Milk",
        quantity=1.0,
        unit="liter",
        storage_location="fridge",
        estimated_expiry_date=date.today() + timedelta(days=1),
        canonical_name="milk",
    )
    await _create_item(
        client,
        test_headers,
        display_name="Eggs",
        quantity=12.0,
        unit="count",
        storage_location="fridge",
        estimated_expiry_date=date.today() + timedelta(days=30),
        canonical_name="eggs",
    )

    response = await client.post("/v1/recommendations", headers=test_headers, json={})

    assert response.status_code == 200
    recipes = response.json()["recipes"]
    french_toast = next(recipe for recipe in recipes if recipe["title"] == "French Toast")
    scrambled_eggs = next(recipe for recipe in recipes if recipe["title"] == "Scrambled Eggs")
    assert french_toast["score"] > scrambled_eggs["score"]


@pytest.mark.asyncio
async def test_meal_plan_uses_expiring_first(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    integration_user: User,
    db_session: AsyncSession,
) -> None:
    await _seed_recipes(
        db_session,
        [
            _recipe(
                "Chicken First",
                20,
                [
                    {"name": "chicken", "quantity": 1.0, "unit": "lb"},
                    {"name": "broth", "quantity": 1.0, "unit": "cup"},
                ],
            ),
            _recipe(
                "Pantry Pasta",
                20,
                [
                    {"name": "pasta", "quantity": 1.0, "unit": "box"},
                    {"name": "olive oil", "quantity": 1.0, "unit": "tbsp"},
                ],
            ),
            _recipe(
                "Rice Bowl",
                25,
                [{"name": "rice", "quantity": 1.0, "unit": "cup"}],
            ),
        ],
    )
    await _create_item(
        client,
        test_headers,
        display_name="Chicken",
        quantity=1.0,
        unit="lb",
        storage_location="fridge",
        estimated_expiry_date=date.today() + timedelta(days=1),
        canonical_name="chicken",
    )
    await _create_item(
        client,
        test_headers,
        display_name="Pasta",
        quantity=1.0,
        unit="box",
        storage_location="pantry",
        estimated_expiry_date=date.today() + timedelta(days=730),
        canonical_name="pasta",
    )

    response = await client.post("/v1/plans", headers=test_headers, json={"days": 3, "servings": 2})

    assert response.status_code == 200
    plan = response.json()["plan"]
    assert plan["days"][0]["recipeTitle"] == "Chicken First"
    assert "chicken" in plan["days"][0]["reservedItems"]


@pytest.mark.asyncio
async def test_shopping_list_after_plan(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    integration_user: User,
    db_session: AsyncSession,
) -> None:
    await _seed_recipes(
        db_session,
        [
            _recipe(
                "Tomato Pasta",
                20,
                [
                    {"name": "pasta", "quantity": 1.0, "unit": "box"},
                    {"name": "tomatoes", "quantity": 3.0, "unit": "count"},
                ],
                ["vegetarian"],
            ),
            _recipe(
                "Egg Toast",
                10,
                [
                    {"name": "eggs", "quantity": 2.0, "unit": "count"},
                    {"name": "bread", "quantity": 2.0, "unit": "slice"},
                ],
                ["vegetarian"],
            ),
            _recipe(
                "Rice Plate",
                15,
                [{"name": "rice", "quantity": 1.0, "unit": "cup"}],
            ),
        ],
    )
    await _create_item(
        client,
        test_headers,
        display_name="Pasta",
        quantity=1.0,
        unit="box",
        storage_location="pantry",
        estimated_expiry_date=date.today() + timedelta(days=90),
        canonical_name="pasta",
    )

    create_plan_response = await client.post(
        "/v1/plans",
        headers=test_headers,
        json={"days": 3, "servings": 2},
    )

    assert create_plan_response.status_code == 200

    shopping_list_response = await client.get("/v1/shopping-list", headers=test_headers)

    assert shopping_list_response.status_code == 200
    items = shopping_list_response.json()["items"]
    assert items
    assert any(item["ingredientName"] in {"tomatoes", "bread", "eggs", "rice"} for item in items)


@pytest.mark.asyncio
async def test_item_lifecycle(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    integration_user: User,
) -> None:
    item = await _create_item(
        client,
        test_headers,
        display_name="Peas",
        quantity=1.0,
        unit="bag",
        storage_location="freezer",
        estimated_expiry_date=date.today() + timedelta(days=180),
        canonical_name="peas",
    )

    update_response = await client.patch(
        f"/v1/items/{item['itemId']}",
        headers=test_headers,
        json={"quantity": 2.0},
    )

    assert update_response.status_code == 200
    assert update_response.json()["quantity"] == 2.0

    freeze_response = await client.post(
        f"/v1/items/{item['itemId']}/status",
        headers=test_headers,
        json={"status": "frozen"},
    )

    assert freeze_response.status_code == 200
    assert freeze_response.json()["status"] == "frozen"

    items_response = await client.get("/v1/items", headers=test_headers)

    assert items_response.status_code == 200
    assert items_response.json() == []

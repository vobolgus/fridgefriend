# pyright: reportAny=false, reportUnusedParameter=false, reportUnusedCallResult=false, reportMissingImports=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownParameterType=false

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import date, timedelta
import uuid

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.inventory_item import InventoryItem, InventorySource, InventoryStatus
from app.models.meal_plan import MealPlan
from app.models.recipe import Recipe
from app.models.user import User
from app.modules.inventory.dependencies import get_current_user
from app.modules.planning.planner import MealPlanner
from app.modules.planning.schemas import PlanDay, PlanRequest, PlanResult
from app.modules.planning.shopping_list import derive_shopping_list


def _recipe(
    recipe_id: str,
    title: str,
    prep_minutes: int,
    dietary_tags: list[str],
    ingredients: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "id": recipe_id,
        "title": title,
        "prep_minutes": prep_minutes,
        "dietary_tags": dietary_tags,
        "ingredients": ingredients,
    }


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _ingredient_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _int_value(value: object) -> int:
    if not isinstance(value, int | str | float):
        raise TypeError("Unsupported numeric value")
    return int(value)


def _plan_with_recipe_ingredients(recipe_id: str, title: str, ingredients: list[dict[str, object]]) -> PlanResult:
    return PlanResult(
        plan_id=str(uuid.uuid4()),
        days=[
            PlanDay(
                date=date.today(),
                recipe_id=recipe_id,
                recipe_title=title,
                servings=2,
                reserved_items=[str(ingredient["name"]) for ingredient in ingredients],
                recipe_ingredients=ingredients,
            ),
        ],
        shopping_list=[],
    )


def _inventory_item(
    name: str,
    quantity: float,
    unit: str,
    expiry_offset_days: int,
    *,
    user_id: uuid.UUID | None = None,
) -> InventoryItem:
    return InventoryItem(
        user_id=user_id or uuid.uuid4(),
        display_name=name.title(),
        quantity=quantity,
        unit=unit,
        storage_location="fridge",
        estimated_expiry_date=date.today() + timedelta(days=expiry_offset_days),
        confidence=0.9,
        status=InventoryStatus.ACTIVE,
        source=InventorySource.MANUAL,
        canonical_name=name,
    )


@pytest.fixture
def planner_recipes() -> list[dict[str, object]]:
    return [
        _recipe(
            "veggie-omelet",
            "Veggie Omelet",
            10,
            ["vegetarian", "quick"],
            [
                {"name": "eggs", "quantity": 2.0, "unit": "count"},
                {"name": "milk", "quantity": 1.0, "unit": "cup"},
                {"name": "spinach", "quantity": 1.0, "unit": "bag"},
            ],
        ),
        _recipe(
            "chicken-rice",
            "Chicken Rice Bowl",
            30,
            ["high-protein"],
            [
                {"name": "chicken", "quantity": 1.0, "unit": "lb"},
                {"name": "rice", "quantity": 2.0, "unit": "cup"},
            ],
        ),
        _recipe(
            "pasta-alfredo",
            "Pasta Alfredo",
            20,
            ["vegetarian"],
            [
                {"name": "pasta", "quantity": 1.0, "unit": "box"},
                {"name": "butter", "quantity": 1.0, "unit": "stick"},
                {"name": "milk", "quantity": 1.0, "unit": "cup"},
            ],
        ),
        _recipe(
            "slow-braised-beef",
            "Slow Braised Beef",
            90,
            ["comfort-food"],
            [
                {"name": "beef", "quantity": 1.0, "unit": "lb"},
                {"name": "onion", "quantity": 1.0, "unit": "count"},
            ],
        ),
        _recipe(
            "tomato-soup",
            "Tomato Soup",
            15,
            ["vegetarian", "quick"],
            [
                {"name": "tomato", "quantity": 3.0, "unit": "count"},
                {"name": "milk", "quantity": 1.0, "unit": "cup"},
            ],
        ),
        _recipe(
            "fruit-yogurt-bowl",
            "Fruit Yogurt Bowl",
            5,
            ["vegetarian", "quick"],
            [
                {"name": "yogurt", "quantity": 1.0, "unit": "cup"},
                {"name": "banana", "quantity": 1.0, "unit": "count"},
            ],
        ),
        _recipe(
            "fried-rice",
            "Fried Rice",
            15,
            ["quick"],
            [
                {"name": "rice", "quantity": 2.0, "unit": "cup"},
                {"name": "eggs", "quantity": 2.0, "unit": "count"},
            ],
        ),
    ]


@pytest_asyncio.fixture
async def planning_test_user(app: FastAPI, db_session: AsyncSession) -> AsyncIterator[User]:
    user = User(email="planning-api@example.com")
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


async def _seed_inventory(
    db_session: AsyncSession,
    user: User,
    items: list[InventoryItem],
) -> None:
    for item in items:
        item.user_id = user.id
    db_session.add_all(items)
    await db_session.commit()


async def _seed_recipes(db_session: AsyncSession, recipes: list[dict[str, object]]) -> None:
    db_session.add_all(
        [
            Recipe(
                title=str(recipe["title"]),
                prep_minutes=_int_value(recipe["prep_minutes"]),
                dietary_tags=_string_list(recipe["dietary_tags"]),
                ingredients=_ingredient_list(recipe["ingredients"]),
            )
            for recipe in recipes
        ],
    )
    await db_session.commit()


def test_plan_request_validates_days_bounds() -> None:
    with pytest.raises(ValueError):
        PlanRequest(days=2)

    with pytest.raises(ValueError):
        PlanRequest(days=8)


def test_plan_covers_all_days(planner_recipes: list[dict[str, object]]) -> None:
    planner = MealPlanner()
    inventory = [
        _inventory_item("eggs", 14.0, "count", 1),
        _inventory_item("milk", 7.0, "cup", 2),
        _inventory_item("spinach", 3.0, "bag", 1),
        _inventory_item("rice", 8.0, "cup", 5),
        _inventory_item("chicken", 3.0, "lb", 3),
        _inventory_item("tomato", 8.0, "count", 4),
        _inventory_item("yogurt", 3.0, "cup", 2),
        _inventory_item("banana", 4.0, "count", 5),
        _inventory_item("pasta", 2.0, "box", 10),
        _inventory_item("butter", 2.0, "stick", 6),
    ]

    result = planner.generate_plan(inventory, days=7, recipes_db=planner_recipes)

    assert len(result.days) == 7


def test_plan_prioritizes_expiring_items(planner_recipes: list[dict[str, object]]) -> None:
    planner = MealPlanner()
    inventory = [
        _inventory_item("spinach", 1.0, "bag", 1),
        _inventory_item("milk", 3.0, "cup", 30),
        _inventory_item("eggs", 6.0, "count", 30),
        _inventory_item("rice", 4.0, "cup", 30),
    ]

    result = planner.generate_plan(inventory, days=3, recipes_db=planner_recipes)

    assert "spinach" in result.days[0].reserved_items


def test_plan_respects_dietary_filter(planner_recipes: list[dict[str, object]]) -> None:
    planner = MealPlanner()
    inventory = [
        _inventory_item("eggs", 8.0, "count", 2),
        _inventory_item("milk", 5.0, "cup", 3),
        _inventory_item("spinach", 2.0, "bag", 1),
        _inventory_item("pasta", 2.0, "box", 7),
        _inventory_item("butter", 2.0, "stick", 7),
    ]

    result = planner.generate_plan(
        inventory,
        days=3,
        dietary_tags=["vegetarian"],
        recipes_db=planner_recipes,
    )

    assert all(day.recipe_id != "chicken-rice" for day in result.days)
    assert all(day.recipe_id != "slow-braised-beef" for day in result.days)


def test_plan_respects_prep_time_filter(planner_recipes: list[dict[str, object]]) -> None:
    planner = MealPlanner()
    inventory = [
        _inventory_item("beef", 2.0, "lb", 2),
        _inventory_item("onion", 2.0, "count", 4),
        _inventory_item("rice", 6.0, "cup", 20),
        _inventory_item("eggs", 8.0, "count", 3),
    ]

    result = planner.generate_plan(
        inventory,
        days=3,
        max_prep_minutes=15,
        recipes_db=planner_recipes,
    )

    assert all(day.recipe_id != "slow-braised-beef" for day in result.days)


def test_shopping_list_empty_when_all_items_on_hand() -> None:
    inventory = [
        _inventory_item("milk", 2.0, "cup", 5),
        _inventory_item("eggs", 4.0, "count", 5),
        _inventory_item("butter", 2.0, "stick", 5),
    ]
    plan = _plan_with_recipe_ingredients(
        "breakfast-scramble",
        "Breakfast Scramble",
        [
            {"name": "milk", "quantity": 1.0, "unit": "cup"},
            {"name": "eggs", "quantity": 2.0, "unit": "count"},
            {"name": "butter", "quantity": 1.0, "unit": "stick"},
        ],
    )

    shopping_list = derive_shopping_list(plan, inventory)

    assert shopping_list == []


def test_shopping_list_identifies_gaps() -> None:
    inventory = [_inventory_item("milk", 2.0, "cup", 5)]
    plan = _plan_with_recipe_ingredients(
        "breakfast-scramble",
        "Breakfast Scramble",
        [
            {"name": "milk", "quantity": 1.0, "unit": "cup"},
            {"name": "eggs", "quantity": 2.0, "unit": "count"},
            {"name": "butter", "quantity": 1.0, "unit": "stick"},
        ],
    )

    shopping_list = derive_shopping_list(plan, inventory)

    assert {item.ingredient_name for item in shopping_list} == {"eggs", "butter"}
    assert all(item.reason == "not in inventory" for item in shopping_list)


def test_shopping_list_quantity_shortfall() -> None:
    inventory = [_inventory_item("eggs", 1.0, "count", 5)]
    plan = _plan_with_recipe_ingredients(
        "omelet",
        "Omelet",
        [{"name": "eggs", "quantity": 2.0, "unit": "count"}],
    )

    shopping_list = derive_shopping_list(plan, inventory)

    assert len(shopping_list) == 1
    assert shopping_list[0].ingredient_name == "eggs"
    assert shopping_list[0].quantity == 1.0
    assert shopping_list[0].reason == "insufficient quantity"


def test_different_recipes_each_day(planner_recipes: list[dict[str, object]]) -> None:
    planner = MealPlanner()
    inventory = [
        _inventory_item("eggs", 14.0, "count", 2),
        _inventory_item("milk", 7.0, "cup", 3),
        _inventory_item("spinach", 3.0, "bag", 1),
        _inventory_item("rice", 8.0, "cup", 4),
        _inventory_item("chicken", 3.0, "lb", 5),
        _inventory_item("tomato", 8.0, "count", 4),
        _inventory_item("yogurt", 3.0, "cup", 2),
        _inventory_item("banana", 4.0, "count", 3),
    ]

    result = planner.generate_plan(inventory, days=4, recipes_db=planner_recipes)

    assert len({day.recipe_id for day in result.days}) > 1


@pytest.mark.asyncio
async def test_api_post_plans(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    planning_test_user: User,
    db_session: AsyncSession,
    planner_recipes: list[dict[str, object]],
) -> None:
    await _seed_recipes(db_session, planner_recipes)
    await _seed_inventory(
        db_session,
        planning_test_user,
        [
            _inventory_item("eggs", 12.0, "count", 2),
            _inventory_item("milk", 6.0, "cup", 3),
            _inventory_item("spinach", 2.0, "bag", 1),
            _inventory_item("rice", 4.0, "cup", 6),
        ],
    )

    response = await client.post(
        "/v1/plans",
        headers=test_headers,
        json={"days": 3, "servings": 2, "dietary_tags": ["vegetarian"]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["days"]) == 3
    assert all(day["recipe_id"] for day in payload["days"])


@pytest.mark.asyncio
async def test_api_post_plans_invalid_days(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    planning_test_user: User,
) -> None:
    response = await client.post(
        "/v1/plans",
        headers=test_headers,
        json={"days": 10, "servings": 2},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_api_get_shopping_list(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    planning_test_user: User,
    db_session: AsyncSession,
    planner_recipes: list[dict[str, object]],
) -> None:
    await _seed_recipes(db_session, planner_recipes)
    await _seed_inventory(
        db_session,
        planning_test_user,
        [
            _inventory_item("milk", 1.0, "cup", 2),
            _inventory_item("eggs", 1.0, "count", 1),
        ],
    )

    create_response = await client.post(
        "/v1/plans",
        headers=test_headers,
        json={"days": 3, "servings": 2},
    )

    assert create_response.status_code == 200

    response = await client.get("/v1/shopping-list", headers=test_headers)

    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


@pytest.mark.asyncio
async def test_plan_saved_to_db(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    planning_test_user: User,
    db_session: AsyncSession,
    planner_recipes: list[dict[str, object]],
) -> None:
    await _seed_recipes(db_session, planner_recipes)
    await _seed_inventory(
        db_session,
        planning_test_user,
        [
            _inventory_item("milk", 3.0, "cup", 2),
            _inventory_item("eggs", 6.0, "count", 2),
            _inventory_item("spinach", 1.0, "bag", 1),
        ],
    )

    response = await client.post(
        "/v1/plans",
        headers=test_headers,
        json={"days": 3, "servings": 2},
    )

    assert response.status_code == 200

    result = await db_session.execute(select(MealPlan).where(MealPlan.user_id == planning_test_user.id))
    saved_plan = result.scalar_one()

    assert saved_plan.user_id == planning_test_user.id
    assert len(saved_plan.days) == 3

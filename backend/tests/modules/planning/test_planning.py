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
from app.models.household import Household, HouseholdMember, HouseholdRole
from app.models.inventory_item import InventoryItem, InventorySource, InventoryStatus
from app.models.meal_plan import MealPlan
from app.models.recipe import Recipe
from app.models.user import User
from app.modules.inventory.dependencies import get_current_user
from app.modules.planning.planner import MealPlanner, NoMatchingRecipesError
from app.modules.planning.schemas import PlanRequest, PlanResult, RecipeIngredient
from app.modules.planning.shopping_list import derive_shopping_list


def _headers(test_headers: dict[str, str], key: str) -> dict[str, str]:
    return {**test_headers, "Idempotency-Key": key}


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
        "image_url": f"https://example.com/{recipe_id}.jpg",
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
    return PlanResult.model_validate(
        {
            "planId": str(uuid.uuid4()),
            "days": [
                {
                    "date": date.today(),
                    "recipeId": recipe_id,
                    "recipeTitle": title,
                    "servings": 2,
                    "reservedItems": [str(ingredient.get("name", "")) for ingredient in ingredients],
                    "recipeIngredients": [RecipeIngredient.model_validate(ingredient) for ingredient in ingredients],
                },
            ],
            "shoppingList": [],
        }
    )


def _shopping_list_items_payload(recipe_id: str | None) -> dict[str, object]:
    return {
        "items": [
            {
                "name": "tomato",
                "quantity": 2.0,
                "unit": "pcs",
                "recipe_id": recipe_id,
            },
            {
                "name": "basil",
                "quantity": None,
                "unit": None,
                "recipe_id": recipe_id,
            },
        ]
    }


def _assert_uuid_string(value: object) -> None:
    assert isinstance(value, str)
    uuid.UUID(value)


def _inventory_item(
    name: str,
    quantity: float,
    unit: str,
    expiry_offset_days: int,
    *,
    user_id: uuid.UUID | None = None,
    household_id: uuid.UUID | None = None,
) -> InventoryItem:
    return InventoryItem(
        user_id=user_id or uuid.uuid4(),
        household_id=household_id,
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
                image_url=str(recipe.get("image_url", "")) or None,
                dietary_tags=_string_list(recipe["dietary_tags"]),
                ingredients=_ingredient_list(recipe["ingredients"]),
            )
            for recipe in recipes
        ],
    )
    await db_session.commit()


async def _seed_household(db_session: AsyncSession, user: User, *, name: str, invite_code: str) -> Household:
    household = Household(name=name, invite_code=invite_code)
    db_session.add(household)
    await db_session.flush()
    db_session.add(HouseholdMember(household_id=household.id, user_id=user.id, role=HouseholdRole.OWNER))
    await db_session.commit()
    await db_session.refresh(household)
    return household


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


def test_plan_raises_when_constraints_match_no_recipes(planner_recipes: list[dict[str, object]]) -> None:
    planner = MealPlanner()
    inventory = [_inventory_item("eggs", 8.0, "count", 2)]

    with pytest.raises(NoMatchingRecipesError, match="No recipes match the requested constraints"):
        _ = planner.generate_plan(
            inventory,
            days=3,
            dietary_tags=["vegan"],
            max_prep_minutes=5,
            recipes_db=planner_recipes,
        )


def test_plan_raises_when_recipe_catalog_empty() -> None:
    planner = MealPlanner()
    inventory = [_inventory_item("eggs", 8.0, "count", 2)]

    with pytest.raises(NoMatchingRecipesError, match="No recipes available"):
        _ = planner.generate_plan(inventory, days=3, recipes_db=[])


@pytest.mark.asyncio
async def test_api_post_plans_returns_422_when_no_recipes_in_db(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    planning_test_user: User,
    db_session: AsyncSession,
) -> None:
    await _seed_inventory(
        db_session,
        planning_test_user,
        [_inventory_item("eggs", 8.0, "count", 2)],
    )

    response = await client.post(
        "/v1/plans",
        headers=_headers(test_headers, "planning-empty-catalog"),
        json={"days": 3, "servings": 2},
    )

    assert response.status_code == 422


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
        headers=_headers(test_headers, "planning-create-api"),
        json={"days": 3, "servings": 2, "dietary_tags": ["vegetarian"]},
    )

    assert response.status_code == 200
    payload = response.json()
    plan = payload["plan"]
    assert len(plan["days"]) == 3
    assert all(day["recipeId"] for day in plan["days"])
    recipe_metadata = {recipe["title"]: recipe for recipe in planner_recipes}
    for day in plan["days"]:
        matched_recipe = recipe_metadata[day["recipeTitle"]]
        assert day["prepMinutes"] == matched_recipe["prep_minutes"]
        assert day["imageUrl"] == matched_recipe["image_url"]


@pytest.mark.asyncio
async def test_api_post_plans_invalid_days(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    planning_test_user: User,
) -> None:
    response = await client.post(
        "/v1/plans",
        headers=_headers(test_headers, "planning-invalid-days"),
        json={"days": 10, "servings": 2},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_api_post_plans_returns_422_when_constraints_match_no_recipes(
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
        [_inventory_item("eggs", 8.0, "count", 2)],
    )

    response = await client.post(
        "/v1/plans",
        headers=_headers(test_headers, "planning-no-matches"),
        json={"days": 3, "servings": 2, "dietary_tags": ["vegan"], "max_prep_minutes": 5},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "No recipes match the requested constraints"}


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
        headers=_headers(test_headers, "planning-shopping-list-create"),
        json={"days": 3, "servings": 2},
    )

    assert create_response.status_code == 200

    response = await client.get("/v1/shopping-list", headers=test_headers)

    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


@pytest.mark.asyncio
async def test_api_get_latest_plan_includes_recipe_metadata(
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
        ],
    )

    create_response = await client.post(
        "/v1/plans",
        headers=_headers(test_headers, "planning-create-latest-metadata"),
        json={"days": 3, "servings": 2, "dietary_tags": ["vegetarian"]},
    )
    assert create_response.status_code == 200

    latest_response = await client.get("/v1/plans/latest", headers=test_headers)

    assert latest_response.status_code == 200
    recipe_metadata = {recipe["title"]: recipe for recipe in planner_recipes}
    for day in latest_response.json()["plan"]["days"]:
        matched_recipe = recipe_metadata[day["recipeTitle"]]
        assert day["prepMinutes"] == matched_recipe["prep_minutes"]
        assert day["imageUrl"] == matched_recipe["image_url"]


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
        headers=_headers(test_headers, "planning-save-plan"),
        json={"days": 3, "servings": 2},
    )

    assert response.status_code == 200

    result = await db_session.execute(select(MealPlan).where(MealPlan.user_id == planning_test_user.id))
    saved_plan = result.scalar_one()

    assert saved_plan.user_id == planning_test_user.id
    assert len(saved_plan.days) == 3


@pytest.mark.asyncio
async def test_planning_scoped_by_household(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    planning_test_user: User,
    db_session: AsyncSession,
    planner_recipes: list[dict[str, object]],
) -> None:
    user_household = await _seed_household(
        db_session,
        planning_test_user,
        name="Planning Scope User Household",
        invite_code="planning-scope-user-hh",
    )
    other_user = User(email="planning-other-user@example.com")
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)
    other_household = await _seed_household(
        db_session,
        other_user,
        name="Planning Scope Other Household",
        invite_code="planning-scope-other-hh",
    )
    await _seed_recipes(db_session, planner_recipes)
    await _seed_inventory(
        db_session,
        planning_test_user,
        [
            _inventory_item("eggs", 8.0, "count", 2, household_id=user_household.id),
            _inventory_item("milk", 4.0, "cup", 2, household_id=user_household.id),
            _inventory_item("spinach", 2.0, "bag", 1, household_id=user_household.id),
        ],
    )
    await _seed_inventory(
        db_session,
        other_user,
        [
            _inventory_item("beef", 3.0, "lb", 2, household_id=other_household.id),
            _inventory_item("onion", 2.0, "count", 4, household_id=other_household.id),
        ],
    )

    response = await client.post(
        "/v1/plans",
        headers=_headers(test_headers, "planning-household-scope"),
        json={"days": 3, "servings": 2, "max_prep_minutes": 15},
    )

    assert response.status_code == 200
    payload = response.json()
    plan = payload["plan"]
    titles = [day["recipeTitle"] for day in plan["days"]]
    assert "Slow Braised Beef" not in titles


@pytest.mark.asyncio
async def test_shopping_list_uses_latest_household_plan(
    client: httpx.AsyncClient,
    app: FastAPI,
    test_headers: dict[str, str],
    planning_test_user: User,
    db_session: AsyncSession,
    planner_recipes: list[dict[str, object]],
) -> None:
    shared_household = await _seed_household(
        db_session,
        planning_test_user,
        name="Shared Planning Household",
        invite_code="shared-planning-household",
    )
    other_user = User(email="planning-shared-member@example.com")
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)
    db_session.add(HouseholdMember(household_id=shared_household.id, user_id=other_user.id, role=HouseholdRole.MEMBER))
    await db_session.commit()

    await _seed_recipes(db_session, planner_recipes)
    await _seed_inventory(
        db_session,
        planning_test_user,
        [
            _inventory_item("eggs", 4.0, "count", 2, household_id=shared_household.id),
            _inventory_item("milk", 2.0, "cup", 2, household_id=shared_household.id),
            _inventory_item("spinach", 1.0, "bag", 1, household_id=shared_household.id),
        ],
    )

    async def override_get_current_user_shared_member() -> User:
        return other_user

    app.dependency_overrides[get_current_user] = override_get_current_user_shared_member

    create_response = await client.post(
        "/v1/plans",
        headers=_headers(test_headers, "planning-shared-household"),
        json={"days": 3, "servings": 2, "dietary_tags": ["vegetarian"]},
    )
    assert create_response.status_code == 200

    shopping_list_response = await client.get("/v1/shopping-list", headers=test_headers)

    assert shopping_list_response.status_code == 200
    assert isinstance(shopping_list_response.json()["items"], list)


@pytest.mark.asyncio
async def test_post_shopping_list_items_creates_manual_items(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    planning_test_user: User,
    db_session: AsyncSession,
    planner_recipes: list[dict[str, object]],
) -> None:
    await _seed_household(
        db_session,
        planning_test_user,
        name="Shopping List Manual Create Household",
        invite_code="shopping-list-manual-create",
    )
    await _seed_recipes(db_session, planner_recipes)
    recipe = (await db_session.execute(select(Recipe).where(Recipe.title == "Veggie Omelet"))).scalar_one()

    response = await client.post(
        "/v1/shopping-list/items",
        headers=_headers(test_headers, "shopping-list-items-create"),
        json=_shopping_list_items_payload(str(recipe.id)),
    )

    assert response.status_code == 201
    payload = response.json()
    assert list(payload.keys()) == ["items"]
    assert len(payload["items"]) == 2

    first_item, second_item = payload["items"]
    _assert_uuid_string(first_item["id"])
    assert first_item["name"] == "tomato"
    assert first_item["quantity"] == 2.0
    assert first_item["unit"] == "pcs"
    assert first_item["recipeId"] == str(recipe.id)
    assert isinstance(first_item["createdAt"], str)

    _assert_uuid_string(second_item["id"])
    assert second_item["name"] == "basil"
    assert second_item["quantity"] is None
    assert second_item["unit"] is None
    assert second_item["recipeId"] == str(recipe.id)
    assert isinstance(second_item["createdAt"], str)


@pytest.mark.asyncio
async def test_post_shopping_list_items_idempotent_replay(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    planning_test_user: User,
    db_session: AsyncSession,
    planner_recipes: list[dict[str, object]],
) -> None:
    await _seed_household(
        db_session,
        planning_test_user,
        name="Shopping List Idempotency Household",
        invite_code="shopping-list-idempotency",
    )
    await _seed_recipes(db_session, planner_recipes)
    recipe = (await db_session.execute(select(Recipe).where(Recipe.title == "Veggie Omelet"))).scalar_one()
    headers = _headers(test_headers, "shopping-list-items-idempotent")
    payload = _shopping_list_items_payload(str(recipe.id))

    first_response = await client.post(
        "/v1/shopping-list/items",
        headers=headers,
        json=payload,
    )
    second_response = await client.post(
        "/v1/shopping-list/items",
        headers=headers,
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert [item["id"] for item in second_response.json()["items"]] == [
        item["id"] for item in first_response.json()["items"]
    ]


@pytest.mark.asyncio
async def test_get_shopping_list_merges_manual_and_derived_items(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    planning_test_user: User,
    db_session: AsyncSession,
    planner_recipes: list[dict[str, object]],
) -> None:
    await _seed_household(
        db_session,
        planning_test_user,
        name="Shopping List Merge Household",
        invite_code="shopping-list-merge",
    )
    await _seed_recipes(db_session, planner_recipes)
    await _seed_inventory(
        db_session,
        planning_test_user,
        [_inventory_item("milk", 1.0, "cup", 2)],
    )
    recipe = (await db_session.execute(select(Recipe).where(Recipe.title == "Veggie Omelet"))).scalar_one()

    plan_response = await client.post(
        "/v1/plans",
        headers=_headers(test_headers, "shopping-list-merge-plan"),
        json={"days": 3, "servings": 2, "dietary_tags": ["vegetarian"]},
    )
    assert plan_response.status_code == 200

    manual_response = await client.post(
        "/v1/shopping-list/items",
        headers=_headers(test_headers, "shopping-list-merge-manual-item"),
        json={
            "items": [
                {
                    "name": "basil",
                    "quantity": None,
                    "unit": None,
                    "recipe_id": str(recipe.id),
                }
            ]
        },
    )

    assert manual_response.status_code == 201

    shopping_list_response = await client.get("/v1/shopping-list", headers=test_headers)

    assert shopping_list_response.status_code == 200
    item_names = {item["name"] for item in shopping_list_response.json()["items"]}
    assert "basil" in item_names
    assert {"eggs", "spinach"}.issubset(item_names)


@pytest.mark.asyncio
async def test_post_shopping_list_items_blocks_cross_household_recipe_id(
    client: httpx.AsyncClient,
    app: FastAPI,
    test_headers: dict[str, str],
    planning_test_user: User,
    db_session: AsyncSession,
    planner_recipes: list[dict[str, object]],
) -> None:
    await _seed_household(
        db_session,
        planning_test_user,
        name="Shopping List Household A",
        invite_code="shopping-list-household-a",
    )
    other_user = User(email="shopping-list-household-b@example.com")
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)
    await _seed_household(
        db_session,
        other_user,
        name="Shopping List Household B",
        invite_code="shopping-list-household-b",
    )
    await _seed_recipes(db_session, planner_recipes)
    recipe = (await db_session.execute(select(Recipe).where(Recipe.title == "Veggie Omelet"))).scalar_one()

    create_response = await client.post(
        "/v1/shopping-list/items",
        headers=_headers(test_headers, "shopping-list-household-a-create"),
        json={
            "items": [
                {
                    "name": "tomato",
                    "quantity": 2.0,
                    "unit": "pcs",
                    "recipe_id": str(recipe.id),
                }
            ]
        },
    )

    assert create_response.status_code == 201

    invalid_recipe_response = await client.post(
        "/v1/shopping-list/items",
        headers=_headers(test_headers, "shopping-list-invalid-recipe-id"),
        json={
            "items": [
                {
                    "name": "oregano",
                    "quantity": None,
                    "unit": None,
                    "recipe_id": str(uuid.uuid4()),
                }
            ]
        },
    )

    assert invalid_recipe_response.status_code in {404, 422}

    async def override_get_current_user_other() -> User:
        return other_user

    app.dependency_overrides[get_current_user] = override_get_current_user_other

    household_b_response = await client.get("/v1/shopping-list", headers=test_headers)

    assert household_b_response.status_code == 200
    household_b_item_names = {item["name"] for item in household_b_response.json()["items"]}
    assert "tomato" not in household_b_item_names

    async def override_get_current_user_original() -> User:
        return planning_test_user

    app.dependency_overrides[get_current_user] = override_get_current_user_original

    household_a_response = await client.get("/v1/shopping-list", headers=test_headers)

    assert household_a_response.status_code == 200
    household_a_item_names = {item["name"] for item in household_a_response.json()["items"]}
    assert "tomato" in household_a_item_names

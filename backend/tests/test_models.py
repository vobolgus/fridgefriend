# pyright: reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownLambdaType=false

from __future__ import annotations

from datetime import date, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory_item import InventoryItem, InventoryStatus, InventorySource
from app.models.meal_plan import MealPlan, MealPlanDay
from app.models.recipe import Recipe
from app.models.user import User


@pytest.mark.asyncio
async def test_user_creation(db_session: AsyncSession) -> None:
    user = User(email="cook@example.com")

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    result = await db_session.execute(select(User).where(User.email == "cook@example.com"))
    saved_user = result.scalar_one()

    assert saved_user.id == user.id
    assert saved_user.email == "cook@example.com"
    assert isinstance(saved_user.created_at, datetime)


@pytest.mark.asyncio
async def test_inventory_item_creation(db_session: AsyncSession) -> None:
    user = User(email="inventory@example.com")
    db_session.add(user)
    await db_session.flush()

    item = InventoryItem(
        user_id=user.id,
        display_name="Milk",
        quantity=2.0,
        unit="liters",
        storage_location="fridge",
        estimated_expiry_date=date(2026, 4, 10),
        confidence=0.9,
        status=InventoryStatus.ACTIVE,
        source=InventorySource.MANUAL,
        canonical_name="milk",
    )

    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)

    result = await db_session.execute(select(InventoryItem).where(InventoryItem.id == item.id))
    saved_item = result.scalar_one()

    assert saved_item.user_id == user.id
    assert saved_item.display_name == "Milk"
    assert saved_item.quantity == 2.0
    assert saved_item.unit == "liters"
    assert saved_item.storage_location == "fridge"
    assert saved_item.estimated_expiry_date == date(2026, 4, 10)
    assert saved_item.confidence == 0.9
    assert saved_item.status is InventoryStatus.ACTIVE
    assert saved_item.source is InventorySource.MANUAL
    assert saved_item.canonical_name == "milk"
    assert isinstance(saved_item.created_at, datetime)
    assert isinstance(saved_item.updated_at, datetime)


@pytest.mark.asyncio
async def test_inventory_item_status_enum(db_session: AsyncSession) -> None:
    user = User(email="status@example.com")
    db_session.add(user)
    await db_session.flush()

    item = InventoryItem(
        user_id=user.id,
        display_name="Spinach",
        quantity=1.0,
        unit="bag",
        storage_location="fridge",
        estimated_expiry_date=date(2026, 4, 8),
        confidence=0.8,
        status=InventoryStatus.ACTIVE,
        source=InventorySource.PHOTO,
        canonical_name="spinach",
    )

    db_session.add(item)
    await db_session.flush()

    assert item.status is InventoryStatus.ACTIVE

    item.status = InventoryStatus.USED
    await db_session.flush()
    assert item.status is InventoryStatus.USED

    item.status = InventoryStatus.DISCARDED
    await db_session.flush()
    assert item.status is InventoryStatus.DISCARDED

    item.status = InventoryStatus.FROZEN
    await db_session.flush()
    assert item.status is InventoryStatus.FROZEN


@pytest.mark.asyncio
async def test_inventory_item_source_enum(db_session: AsyncSession) -> None:
    user = User(email="source@example.com")
    db_session.add(user)
    await db_session.flush()

    sources = {
        InventorySource.MANUAL: "manual",
        InventorySource.BARCODE: "barcode",
        InventorySource.PHOTO: "photo",
    }

    for source, expected_value in sources.items():
        item = InventoryItem(
            user_id=user.id,
            display_name=f"Item-{expected_value}",
            quantity=1.0,
            unit="count",
            storage_location="pantry",
            estimated_expiry_date=date(2026, 4, 12),
            confidence=0.75,
            status=InventoryStatus.ACTIVE,
            source=source,
            canonical_name=f"canonical-{expected_value}",
        )

        db_session.add(item)
        await db_session.flush()

        assert item.source is source
        assert item.source.value == expected_value


@pytest.mark.asyncio
async def test_recipe_creation(db_session: AsyncSession) -> None:
    recipe = Recipe(
        title="Vegetable Stir Fry",
        prep_minutes=25,
        dietary_tags=["vegetarian", "quick"],
        ingredients=[
            {"name": "broccoli", "quantity": 1, "unit": "head"},
            {"name": "soy sauce", "quantity": 2, "unit": "tbsp"},
        ],
    )

    db_session.add(recipe)
    await db_session.commit()
    await db_session.refresh(recipe)

    result = await db_session.execute(select(Recipe).where(Recipe.id == recipe.id))
    saved_recipe = result.scalar_one()

    assert saved_recipe.title == "Vegetable Stir Fry"
    assert saved_recipe.prep_minutes == 25
    assert saved_recipe.dietary_tags == ["vegetarian", "quick"]
    assert saved_recipe.ingredients == [
        {"name": "broccoli", "quantity": 1, "unit": "head"},
        {"name": "soy sauce", "quantity": 2, "unit": "tbsp"},
    ]


@pytest.mark.asyncio
async def test_meal_plan_with_days(db_session: AsyncSession) -> None:
    recipe_one = Recipe(
        title="Pasta Primavera",
        prep_minutes=30,
        dietary_tags=["vegetarian"],
        ingredients=[{"name": "pasta", "quantity": 500, "unit": "g"}],
    )
    recipe_two = Recipe(
        title="Soup Night",
        prep_minutes=40,
        dietary_tags=["dairy-free"],
        ingredients=[{"name": "carrot", "quantity": 3, "unit": "count"}],
    )
    db_session.add_all([recipe_one, recipe_two])
    await db_session.flush()

    meal_plan = MealPlan(
        start_date=date(2026, 4, 6),
        end_date=date(2026, 4, 12),
        days=[
            MealPlanDay(date=date(2026, 4, 6), recipe_id=recipe_one.id, servings=2),
            MealPlanDay(date=date(2026, 4, 7), recipe_id=recipe_two.id, servings=4),
        ],
    )

    db_session.add(meal_plan)
    await db_session.commit()
    await db_session.refresh(meal_plan)

    result = await db_session.execute(select(MealPlan).where(MealPlan.id == meal_plan.id))
    saved_plan = result.scalar_one()

    assert saved_plan.start_date == date(2026, 4, 6)
    assert saved_plan.end_date == date(2026, 4, 12)
    assert len(saved_plan.days) == 2
    assert {day.recipe_id for day in saved_plan.days} == {recipe_one.id, recipe_two.id}
    assert [day.servings for day in sorted(saved_plan.days, key=lambda day: day.date)] == [2, 4]


@pytest.mark.asyncio
async def test_inventory_item_expiry_date(db_session: AsyncSession) -> None:
    user = User(email="expiry@example.com")
    db_session.add(user)
    await db_session.flush()

    expiry_date = date(2026, 4, 15)
    item = InventoryItem(
        user_id=user.id,
        display_name="Yogurt",
        quantity=6.0,
        unit="cups",
        storage_location="fridge",
        estimated_expiry_date=expiry_date,
        confidence=0.95,
        status=InventoryStatus.ACTIVE,
        source=InventorySource.BARCODE,
        canonical_name="yogurt",
    )

    db_session.add(item)
    await db_session.commit()

    result = await db_session.execute(select(InventoryItem).where(InventoryItem.display_name == "Yogurt"))
    saved_item = result.scalar_one()

    assert saved_item.estimated_expiry_date == expiry_date

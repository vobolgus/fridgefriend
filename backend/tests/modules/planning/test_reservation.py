from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.household import Household
from app.models.inventory_item import InventoryItem, InventorySource, InventoryStatus
from app.models.meal_plan import MealPlan
from app.models.recipe import Recipe
from app.models.reserved_ingredient import ReservedIngredient
from app.models.user import User
from app.modules.planning.reservation import InsufficientReservationQuantityError, ReservationService
from app.modules.planning.schemas import PlanDay, PlanRequest, PlanResult, RecipeIngredient
from app.modules.planning.service import PlanningService
from app.modules.planning.shopping_list import derive_shopping_list


async def _seed_user_and_household(db_session: AsyncSession, email: str) -> tuple[User, Household]:
    user = User(email=email)
    household = Household(name="Planning Household", invite_code=email.replace("@", "-"))
    db_session.add_all([user, household])
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(household)
    return user, household


async def _seed_inventory(db_session: AsyncSession, user: User, household: Household, quantity: float = 6.0) -> InventoryItem:
    item = InventoryItem(
        user_id=user.id,
        household_id=household.id,
        display_name="Eggs",
        quantity=quantity,
        unit="count",
        storage_location="fridge",
        estimated_expiry_date=date.today() + timedelta(days=2),
        confidence=0.95,
        status=InventoryStatus.ACTIVE,
        source=InventorySource.MANUAL,
        canonical_name="eggs",
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


async def _seed_recipes(db_session: AsyncSession) -> None:
    db_session.add_all(
        [
            Recipe(title="Egg Day 1", prep_minutes=10, dietary_tags=[], ingredients=[{"name": "eggs", "quantity": 2.0, "unit": "count"}]),
            Recipe(title="Egg Day 2", prep_minutes=12, dietary_tags=[], ingredients=[{"name": "eggs", "quantity": 2.0, "unit": "count"}]),
            Recipe(title="Egg Day 3", prep_minutes=14, dietary_tags=[], ingredients=[{"name": "eggs", "quantity": 2.0, "unit": "count"}]),
        ]
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_plan_creates_reserved_ingredient_records(db_session: AsyncSession) -> None:
    user, household = await _seed_user_and_household(db_session, "reservation-records@example.com")
    _ = await _seed_inventory(db_session, user, household)
    await _seed_recipes(db_session)

    result = await PlanningService(db_session).generate_plan(user, household.id, PlanRequest(days=3, servings=2))

    reservations = (await db_session.execute(select(ReservedIngredient))).scalars().all()
    assert result.plan_id
    assert len(reservations) == 3


@pytest.mark.asyncio
async def test_reservation_reduces_available_quantity(db_session: AsyncSession) -> None:
    user, household = await _seed_user_and_household(db_session, "reservation-reduce@example.com")
    inventory_item = await _seed_inventory(db_session, user, household)
    await _seed_recipes(db_session)
    service = PlanningService(db_session)

    plan = await service.generate_plan(user, household.id, PlanRequest(days=3, servings=2))
    reserved = await ReservationService(db_session).reserved_quantities_by_ingredient(household_id=household.id)

    shopping_list = derive_shopping_list(
        PlanResult(
            plan_id=plan.plan_id,
            days=[
                PlanDay(
                    date=date.today(),
                    recipe_id="future-recipe",
                    recipe_title="Future Omelet",
                    servings=2,
                    reserved_items=["eggs"],
                    recipe_ingredients=[RecipeIngredient(ingredient_name="eggs", quantity=2.0, unit="count")],
                )
            ],
            shopping_list=[],
        ),
        [inventory_item],
        reserved_quantities=reserved,
    )

    assert shopping_list[0].ingredient_name == "eggs"
    assert shopping_list[0].quantity == 2.0


@pytest.mark.asyncio
async def test_double_reservation_fails_with_insufficient_quantity(db_session: AsyncSession) -> None:
    user, household = await _seed_user_and_household(db_session, "reservation-double@example.com")
    _ = await _seed_inventory(db_session, user, household)
    await _seed_recipes(db_session)
    service = PlanningService(db_session)

    _ = await service.generate_plan(user, household.id, PlanRequest(days=3, servings=2))

    with pytest.raises(InsufficientReservationQuantityError):
        _ = await service.generate_plan(user, household.id, PlanRequest(days=3, servings=2))


@pytest.mark.asyncio
async def test_reservation_and_plan_are_atomic(db_session: AsyncSession) -> None:
    user, household = await _seed_user_and_household(db_session, "reservation-atomic@example.com")
    user_id = user.id
    household_id = household.id
    _ = await _seed_inventory(db_session, user, household)
    await _seed_recipes(db_session)
    service = PlanningService(db_session)

    _ = await service.generate_plan(user, household_id, PlanRequest(days=3, servings=2))
    with pytest.raises(InsufficientReservationQuantityError):
        _ = await service.generate_plan(user, household_id, PlanRequest(days=3, servings=2))

    plans = (await db_session.execute(select(MealPlan).where(MealPlan.user_id == user_id))).scalars().all()
    assert len(plans) == 1


@pytest.mark.asyncio
async def test_shopping_list_accounts_for_reservations(db_session: AsyncSession) -> None:
    user, household = await _seed_user_and_household(db_session, "reservation-shopping@example.com")
    _ = await _seed_inventory(db_session, user, household)
    await _seed_recipes(db_session)
    service = PlanningService(db_session)

    _ = await service.generate_plan(user, household.id, PlanRequest(days=3, servings=2))
    reserved = await ReservationService(db_session).reserved_quantities_by_ingredient(household_id=household.id)

    plan = PlanResult(
        plan_id="shopping-test",
        days=[
            PlanDay(
                date=date.today(),
                recipe_id="recipe-a",
                recipe_title="Egg Snack",
                servings=1,
                reserved_items=["eggs"],
                recipe_ingredients=[RecipeIngredient(ingredient_name="eggs", quantity=1.0, unit="count")],
            )
        ],
        shopping_list=[],
    )
    inventory = list((await db_session.execute(select(InventoryItem).where(InventoryItem.user_id == user.id))).scalars().all())

    shopping_list = derive_shopping_list(plan, inventory, reserved_quantities=reserved)

    assert shopping_list[0].reason == "insufficient quantity"
    assert shopping_list[0].ingredient_name == "eggs"


@pytest.mark.asyncio
async def test_delete_plan_releases_reservations(db_session: AsyncSession) -> None:
    user, household = await _seed_user_and_household(db_session, "reservation-delete@example.com")
    _ = await _seed_inventory(db_session, user, household)
    await _seed_recipes(db_session)
    service = PlanningService(db_session)

    plan = await service.generate_plan(user, household.id, PlanRequest(days=3, servings=2))
    await service.delete_plan(UUID(plan.plan_id), user, household.id)

    reservations = (await db_session.execute(select(ReservedIngredient))).scalars().all()
    assert reservations == []

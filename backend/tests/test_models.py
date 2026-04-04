# pyright: reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownLambdaType=false, reportMissingImports=false, reportAny=false

from __future__ import annotations

from datetime import date, datetime
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.canonical_ingredient import CanonicalIngredient, ProductBarcode, ShelfLifeRule
from app.models.events import AnalyticsEvent, InventoryEvent, RecommendationSession
from app.models.household import Household, HouseholdMember, HouseholdRole
from app.models.inventory_item import InventoryItem, InventoryStatus, InventorySource
from app.models.meal_plan import MealPlan, MealPlanDay
from app.models.notification import DeviceToken, NotificationPreference
from app.models.recipe import Recipe
from app.models.reserved_ingredient import ReservedIngredient
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
async def test_household_creation(db_session: AsyncSession) -> None:
    household = Household(name="Home Kitchen", invite_code="invite-home")

    db_session.add(household)
    await db_session.commit()
    await db_session.refresh(household)

    result = await db_session.execute(select(Household).where(Household.id == household.id))
    saved_household = result.scalar_one()

    assert saved_household.name == "Home Kitchen"
    assert saved_household.invite_code == "invite-home"


@pytest.mark.asyncio
async def test_household_member_creation(db_session: AsyncSession) -> None:
    user = User(email="member@example.com")
    household = Household(name="Shared Kitchen", invite_code="shared-home")
    db_session.add_all([user, household])
    await db_session.flush()

    membership = HouseholdMember(
        household_id=household.id,
        user_id=user.id,
        role=HouseholdRole.OWNER,
    )

    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(membership)

    result = await db_session.execute(
        select(HouseholdMember).where(HouseholdMember.id == membership.id)
    )
    saved_membership = result.scalar_one()

    assert saved_membership.household_id == household.id
    assert saved_membership.user_id == user.id
    assert saved_membership.role is HouseholdRole.OWNER


@pytest.mark.asyncio
async def test_household_has_inventory_items(db_session: AsyncSession) -> None:
    user = User(email="household-items@example.com")
    household = Household(name="Inventory Kitchen", invite_code="inventory-home")
    db_session.add_all([user, household])
    await db_session.flush()

    item = InventoryItem(
        user_id=user.id,
        household_id=household.id,
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

    result = await db_session.execute(select(Household).where(Household.id == household.id))
    saved_household = result.scalar_one()

    assert len(saved_household.inventory_items) == 1
    assert saved_household.inventory_items[0].id == item.id


@pytest.mark.asyncio
async def test_user_has_household_memberships(db_session: AsyncSession) -> None:
    user = User(email="membership@example.com")
    household = Household(name="Membership Kitchen", invite_code="membership-home")
    db_session.add_all([user, household])
    await db_session.flush()

    membership = HouseholdMember(
        household_id=household.id,
        user_id=user.id,
        role=HouseholdRole.MEMBER,
    )

    db_session.add(membership)
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.id == user.id))
    saved_user = result.scalar_one()

    assert len(saved_user.household_memberships) == 1
    assert saved_user.household_memberships[0].id == membership.id


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


@pytest.mark.asyncio
async def test_inventory_item_has_version_field(db_session: AsyncSession) -> None:
    user = User(email="version-field@example.com")
    db_session.add(user)
    await db_session.flush()

    item = InventoryItem(
        user_id=user.id,
        display_name="Kefir",
        quantity=1.0,
        unit="bottle",
        storage_location="fridge",
        estimated_expiry_date=date(2026, 4, 20),
        confidence=0.8,
        status=InventoryStatus.ACTIVE,
        source=InventorySource.MANUAL,
        canonical_name="kefir",
    )

    db_session.add(item)
    await db_session.flush()

    assert hasattr(item, "version")


@pytest.mark.asyncio
async def test_version_defaults_to_1(db_session: AsyncSession) -> None:
    user = User(email="version-default@example.com")
    db_session.add(user)
    await db_session.flush()

    item = InventoryItem(
        user_id=user.id,
        display_name="Cream",
        quantity=1.0,
        unit="carton",
        storage_location="fridge",
        estimated_expiry_date=date(2026, 4, 21),
        confidence=0.9,
        status=InventoryStatus.ACTIVE,
        source=InventorySource.MANUAL,
        canonical_name="cream",
    )

    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)

    assert item.version == 1


@pytest.mark.asyncio
async def test_meal_plan_has_version_field(db_session: AsyncSession) -> None:
    recipe = Recipe(
        title="Versioned Soup",
        prep_minutes=20,
        dietary_tags=["vegetarian"],
        ingredients=[{"name": "carrot", "quantity": 2, "unit": "count"}],
    )
    db_session.add(recipe)
    await db_session.flush()

    meal_plan = MealPlan(
        start_date=date(2026, 4, 22),
        end_date=date(2026, 4, 28),
        days=[MealPlanDay(date=date(2026, 4, 22), recipe_id=recipe.id, servings=2)],
    )

    db_session.add(meal_plan)
    await db_session.flush()

    assert hasattr(meal_plan, "version")


@pytest.mark.asyncio
async def test_canonical_ingredient_creation(db_session: AsyncSession) -> None:
    ingredient = CanonicalIngredient(name="milk", category="dairy")

    db_session.add(ingredient)
    await db_session.commit()
    await db_session.refresh(ingredient)

    result = await db_session.execute(
        select(CanonicalIngredient).where(CanonicalIngredient.id == ingredient.id)
    )
    saved_ingredient = result.scalar_one()

    assert saved_ingredient.name == "milk"
    assert saved_ingredient.category == "dairy"
    assert saved_ingredient.aliases == []


@pytest.mark.asyncio
async def test_product_barcode_links_to_ingredient(db_session: AsyncSession) -> None:
    ingredient = CanonicalIngredient(name="yogurt", category="dairy")
    db_session.add(ingredient)
    await db_session.flush()

    barcode = ProductBarcode(
        barcode="0123456789012",
        canonical_ingredient_id=ingredient.id,
        display_name="Greek Yogurt",
        brand="FridgeFriend",
    )

    db_session.add(barcode)
    await db_session.commit()
    await db_session.refresh(barcode)

    result = await db_session.execute(select(ProductBarcode).where(ProductBarcode.id == barcode.id))
    saved_barcode = result.scalar_one()

    assert saved_barcode.barcode == "0123456789012"
    assert saved_barcode.canonical_ingredient_id == ingredient.id
    assert saved_barcode.canonical_ingredient.id == ingredient.id


@pytest.mark.asyncio
async def test_shelf_life_rule_model(db_session: AsyncSession) -> None:
    ingredient = CanonicalIngredient(name="spinach", category="produce")
    db_session.add(ingredient)
    await db_session.flush()

    rule = ShelfLifeRule(
        canonical_ingredient_id=ingredient.id,
        storage_type="fridge",
        shelf_life_days=5,
    )

    db_session.add(rule)
    await db_session.commit()
    await db_session.refresh(rule)

    result = await db_session.execute(select(ShelfLifeRule).where(ShelfLifeRule.id == rule.id))
    saved_rule = result.scalar_one()

    assert saved_rule.canonical_ingredient_id == ingredient.id
    assert saved_rule.storage_type == "fridge"
    assert saved_rule.shelf_life_days == 5
    assert saved_rule.confidence == 0.8


@pytest.mark.asyncio
async def test_notification_preference_creation(db_session: AsyncSession) -> None:
    user = User(email="notify@example.com")
    db_session.add(user)
    await db_session.flush()

    preference = NotificationPreference(user_id=user.id)

    db_session.add(preference)
    await db_session.commit()
    await db_session.refresh(preference)

    result = await db_session.execute(
        select(NotificationPreference).where(NotificationPreference.id == preference.id)
    )
    saved_preference = result.scalar_one()

    assert saved_preference.user_id == user.id
    assert saved_preference.expiry_reminder_enabled is True
    assert saved_preference.reminder_days_before == 1
    assert saved_preference.quiet_hours_start is None
    assert saved_preference.quiet_hours_end is None


@pytest.mark.asyncio
async def test_device_token_creation(db_session: AsyncSession) -> None:
    user = User(email="device@example.com")
    db_session.add(user)
    await db_session.flush()

    device_token = DeviceToken(
        user_id=user.id,
        token="device-token-123",
        platform="ios",
    )

    db_session.add(device_token)
    await db_session.commit()
    await db_session.refresh(device_token)

    result = await db_session.execute(select(DeviceToken).where(DeviceToken.id == device_token.id))
    saved_token = result.scalar_one()

    assert saved_token.user_id == user.id
    assert saved_token.token == "device-token-123"
    assert saved_token.platform == "ios"


@pytest.mark.asyncio
async def test_inventory_event_creation(db_session: AsyncSession) -> None:
    user = User(email="inventory-event@example.com")
    db_session.add(user)
    await db_session.flush()

    item = InventoryItem(
        user_id=user.id,
        display_name="Cheese",
        quantity=1.0,
        unit="block",
        storage_location="fridge",
        estimated_expiry_date=date(2026, 4, 30),
        confidence=0.88,
        status=InventoryStatus.ACTIVE,
        source=InventorySource.MANUAL,
        canonical_name="cheese",
    )
    db_session.add(item)
    await db_session.flush()

    event = InventoryEvent(
        household_id=uuid.uuid4(),
        user_id=user.id,
        item_id=item.id,
        action="added",
        previous_state={},
        new_state={"display_name": "Cheese"},
    )

    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)

    result = await db_session.execute(select(InventoryEvent).where(InventoryEvent.id == event.id))
    saved_event = result.scalar_one()

    assert saved_event.user_id == user.id
    assert saved_event.item_id == item.id
    assert saved_event.action == "added"
    assert saved_event.new_state == {"display_name": "Cheese"}


@pytest.mark.asyncio
async def test_analytics_event_creation(db_session: AsyncSession) -> None:
    user = User(email="analytics@example.com")
    db_session.add(user)
    await db_session.flush()

    event = AnalyticsEvent(
        user_id=user.id,
        event_type="recipe_viewed",
        payload={"recipe_id": "recipe-123"},
    )

    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)

    result = await db_session.execute(select(AnalyticsEvent).where(AnalyticsEvent.id == event.id))
    saved_event = result.scalar_one()

    assert saved_event.user_id == user.id
    assert saved_event.event_type == "recipe_viewed"
    assert saved_event.payload == {"recipe_id": "recipe-123"}
    assert isinstance(saved_event.created_at, datetime)


@pytest.mark.asyncio
async def test_recommendation_session_creation(db_session: AsyncSession) -> None:
    session = RecommendationSession(
        household_id=uuid.uuid4(),
        request_params={"servings": 2},
    )

    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    result = await db_session.execute(
        select(RecommendationSession).where(RecommendationSession.id == session.id)
    )
    saved_session = result.scalar_one()

    assert saved_session.household_id == session.household_id
    assert saved_session.request_params == {"servings": 2}
    assert saved_session.recipes_shown == []
    assert saved_session.recipe_selected_id is None


@pytest.mark.asyncio
async def test_reserved_ingredient_creation(db_session: AsyncSession) -> None:
    user = User(email="reserved@example.com")
    recipe = Recipe(
        title="Reserved Pasta",
        prep_minutes=15,
        dietary_tags=["quick"],
        ingredients=[{"name": "pasta", "quantity": 200, "unit": "g"}],
    )
    db_session.add_all([user, recipe])
    await db_session.flush()

    item = InventoryItem(
        user_id=user.id,
        display_name="Pasta",
        quantity=500.0,
        unit="g",
        storage_location="pantry",
        estimated_expiry_date=date(2026, 5, 1),
        confidence=0.99,
        status=InventoryStatus.ACTIVE,
        source=InventorySource.MANUAL,
        canonical_name="pasta",
    )
    db_session.add(item)
    await db_session.flush()

    meal_plan = MealPlan(
        user_id=user.id,
        start_date=date(2026, 4, 6),
        end_date=date(2026, 4, 12),
    )
    db_session.add(meal_plan)
    await db_session.flush()

    meal_plan_day = MealPlanDay(
        meal_plan_id=meal_plan.id,
        recipe_id=recipe.id,
        date=date(2026, 4, 6),
        servings=2,
    )
    db_session.add(meal_plan_day)
    await db_session.flush()

    reserved_ingredient = ReservedIngredient(
        meal_plan_id=meal_plan.id,
        meal_plan_day_id=meal_plan_day.id,
        inventory_item_id=item.id,
        quantity_reserved=200.0,
        unit="g",
    )

    db_session.add(reserved_ingredient)
    await db_session.commit()
    await db_session.refresh(reserved_ingredient)

    result = await db_session.execute(
        select(ReservedIngredient).where(ReservedIngredient.id == reserved_ingredient.id)
    )
    saved_reserved_ingredient = result.scalar_one()

    assert saved_reserved_ingredient.meal_plan_id == meal_plan.id
    assert saved_reserved_ingredient.meal_plan_day_id == meal_plan_day.id
    assert saved_reserved_ingredient.inventory_item_id == item.id
    assert saved_reserved_ingredient.quantity_reserved == 200.0
    assert saved_reserved_ingredient.unit == "g"

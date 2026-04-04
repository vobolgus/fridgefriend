# pyright: reportAny=false, reportUnusedParameter=false, reportUnusedCallResult=false, reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import date, timedelta

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.household import Household, HouseholdMember, HouseholdRole
from app.models.inventory_item import InventoryItem, InventorySource, InventoryStatus
from app.models.user import User
from app.modules.inventory.dependencies import get_current_user
from app.modules.recommendations.fixture_recipes import FIXTURE_RECIPES
from app.modules.recommendations.schemas import RecommendationRequest
from app.modules.recommendations.scorer import RecipeScorer
from app.modules.recommendations.service import RecommendationService


def get_recipe(title: str) -> dict[str, object]:
    return next(recipe for recipe in FIXTURE_RECIPES if recipe["title"] == title)


async def add_inventory_item(
    db_session: AsyncSession,
    user: User,
    canonical_name: str,
    *,
    display_name: str | None = None,
    estimated_expiry_date: date | None = None,
    status: InventoryStatus = InventoryStatus.ACTIVE,
    household_id: object | None = None,
) -> InventoryItem:
    item = InventoryItem(
        user_id=user.id,
        household_id=household_id,
        display_name=display_name or canonical_name.title(),
        quantity=1.0,
        unit="unit",
        storage_location="fridge",
        estimated_expiry_date=estimated_expiry_date or (date.today() + timedelta(days=7)),
        confidence=0.9,
        status=status,
        source=InventorySource.MANUAL,
        canonical_name=canonical_name,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


async def ensure_household(db_session: AsyncSession, user: User, *, name: str, invite_code: str) -> Household:
    household = Household(name=name, invite_code=invite_code)
    db_session.add(household)
    await db_session.flush()
    db_session.add(HouseholdMember(household_id=household.id, user_id=user.id, role=HouseholdRole.OWNER))
    await db_session.commit()
    await db_session.refresh(household)
    return household


@pytest_asyncio.fixture
async def test_user(app: FastAPI, db_session: AsyncSession) -> AsyncIterator[User]:
    user = User(email="recommendations-api@example.com")
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
async def test_score_recipe_all_ingredients_present(test_user: User, db_session: AsyncSession) -> None:
    await add_inventory_item(db_session, test_user, "eggs")
    await add_inventory_item(db_session, test_user, "butter")

    scorer = RecipeScorer(today=date(2026, 4, 3))
    recipe = get_recipe("Scrambled Eggs")

    breakdown = scorer.score_breakdown(recipe, await RecommendationService(db_session).list_inventory_items(test_user.id))

    assert breakdown.coverage_pct == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_score_recipe_no_ingredients_present(test_user: User, db_session: AsyncSession) -> None:
    scorer = RecipeScorer(today=date(2026, 4, 3))
    recipe = get_recipe("Scrambled Eggs")

    breakdown = scorer.score_breakdown(recipe, await RecommendationService(db_session).list_inventory_items(test_user.id))

    assert breakdown.coverage_pct == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_score_recipe_expiry_bonus(test_user: User, db_session: AsyncSession) -> None:
    recipe = get_recipe("Banana Smoothie")
    today = date(2026, 4, 3)

    await add_inventory_item(db_session, test_user, "bananas", estimated_expiry_date=today)
    await add_inventory_item(db_session, test_user, "milk", estimated_expiry_date=today + timedelta(days=30))

    scorer = RecipeScorer(today=today)
    urgent_score = scorer.score_recipe(recipe, await RecommendationService(db_session).list_inventory_items(test_user.id))

    await db_session.rollback()

    second_user = User(email="recommendations-api-later@example.com")
    db_session.add(second_user)
    await db_session.commit()
    await db_session.refresh(second_user)
    await add_inventory_item(db_session, second_user, "bananas", estimated_expiry_date=today + timedelta(days=30))
    await add_inventory_item(db_session, second_user, "milk", estimated_expiry_date=today + timedelta(days=30))

    later_score = scorer.score_recipe(recipe, await RecommendationService(db_session).list_inventory_items(second_user.id))

    assert urgent_score > later_score


@pytest.mark.asyncio
async def test_score_recipe_prep_time_penalty(test_user: User, db_session: AsyncSession) -> None:
    scorer = RecipeScorer(today=date(2026, 4, 3))
    inventory_items = [
        await add_inventory_item(db_session, test_user, "eggs"),
        await add_inventory_item(db_session, test_user, "butter"),
    ]
    fast_score = scorer.score_recipe(
        {
            "id": "dddddddd-dddd-dddd-dddd-dddddddddddd",
            "title": "Fast Eggs",
            "prep_minutes": 10,
            "dietary_tags": [],
            "ingredients": [
                {"canonical_name": "eggs", "quantity": 2.0, "unit": "unit"},
                {"canonical_name": "butter", "quantity": 1.0, "unit": "tbsp"},
            ],
        },
        inventory_items,
    )
    slow_score = scorer.score_recipe(
        {
            "id": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
            "title": "Slow Eggs",
            "prep_minutes": 90,
            "dietary_tags": [],
            "ingredients": [
                {"canonical_name": "eggs", "quantity": 2.0, "unit": "unit"},
                {"canonical_name": "butter", "quantity": 1.0, "unit": "tbsp"},
            ],
        },
        inventory_items,
    )

    assert fast_score > slow_score


@pytest.mark.asyncio
async def test_get_recommendations_returns_sorted(test_user: User, db_session: AsyncSession) -> None:
    for name in ["eggs", "butter", "milk", "bread"]:
        await add_inventory_item(db_session, test_user, name)

    recommendations = await RecommendationService(db_session).get_recommendations(
        test_user.id,
        RecommendationRequest(),
    )

    scores = [recommendation.score for recommendation in recommendations]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_get_recommendations_dietary_filter(test_user: User, db_session: AsyncSession) -> None:
    recommendations = await RecommendationService(db_session).get_recommendations(
        test_user.id,
        RecommendationRequest(dietary_tags=["vegetarian"]),
    )

    titles = {recommendation.title for recommendation in recommendations}
    assert "Chicken Stir Fry" not in titles
    assert "Pasta Bolognese" not in titles
    assert "Beef Stew" not in titles
    assert "Vegetable Rice" in titles


@pytest.mark.asyncio
async def test_get_recommendations_dietary_filter_requires_all_tags(
    test_user: User,
    db_session: AsyncSession,
) -> None:
    recommendations = await RecommendationService(db_session).get_recommendations(
        test_user.id,
        RecommendationRequest(dietary_tags=["vegetarian", "gluten-free"]),
    )

    assert recommendations
    assert "Greek Yogurt Bowl" in [recommendation.title for recommendation in recommendations]
    assert all(
        recommendation.title in {"Greek Yogurt Bowl", "Apple Salad"}
        for recommendation in recommendations
    )


@pytest.mark.asyncio
async def test_get_recommendations_prep_time_filter(test_user: User, db_session: AsyncSession) -> None:
    recommendations = await RecommendationService(db_session).get_recommendations(
        test_user.id,
        RecommendationRequest(max_prep_minutes=15),
    )

    assert recommendations
    assert all(recommendation.prep_minutes <= 15 for recommendation in recommendations)
    assert all(recommendation.title != "Beef Stew" for recommendation in recommendations)


@pytest.mark.asyncio
async def test_get_recommendations_excluded_ingredients(test_user: User, db_session: AsyncSession) -> None:
    recommendations = await RecommendationService(db_session).get_recommendations(
        test_user.id,
        RecommendationRequest(excluded_ingredients=["beef"]),
    )

    titles = {recommendation.title for recommendation in recommendations}
    assert "Pasta Bolognese" not in titles
    assert "Beef Stew" not in titles


@pytest.mark.asyncio
async def test_missing_items_list(test_user: User, db_session: AsyncSession) -> None:
    await add_inventory_item(db_session, test_user, "milk")

    recommendations = await RecommendationService(
        db_session,
        recipes=[
            {
                "id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
                "title": "Milk and Eggs",
                "prep_minutes": 5,
                "dietary_tags": [],
                "ingredients": [
                    {"canonical_name": "milk", "quantity": 100.0, "unit": "ml"},
                    {"canonical_name": "eggs", "quantity": 2.0, "unit": "unit"},
                ],
            },
        ],
    ).get_recommendations(
        test_user.id,
        RecommendationRequest(),
    )

    assert recommendations[0].missing_items == ["eggs"]


@pytest.mark.asyncio
async def test_empty_inventory_returns_low_coverage_recipes(test_user: User, db_session: AsyncSession) -> None:
    recommendations = await RecommendationService(db_session).get_recommendations(
        test_user.id,
        RecommendationRequest(),
    )

    assert recommendations
    assert all(recommendation.coverage_pct == pytest.approx(0.0) for recommendation in recommendations)


@pytest.mark.asyncio
async def test_inactive_inventory_items_do_not_count_toward_coverage(
    test_user: User,
    db_session: AsyncSession,
) -> None:
    await add_inventory_item(db_session, test_user, "eggs")
    await add_inventory_item(db_session, test_user, "butter", status=InventoryStatus.USED)

    recommendations = await RecommendationService(db_session).get_recommendations(
        test_user.id,
        RecommendationRequest(max_prep_minutes=15),
    )

    scrambled_eggs = next(
        recommendation for recommendation in recommendations if recommendation.title == "Scrambled Eggs"
    )
    assert scrambled_eggs.coverage_pct == pytest.approx(0.5)
    assert scrambled_eggs.missing_items == ["butter"]


@pytest.mark.asyncio
async def test_service_returns_top_10_only(test_user: User, db_session: AsyncSession) -> None:
    recommendations = await RecommendationService(db_session).get_recommendations(
        test_user.id,
        RecommendationRequest(),
    )

    assert len(recommendations) == 10


@pytest.mark.asyncio
async def test_api_endpoint_recommendations(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
    db_session: AsyncSession,
) -> None:
    household = await ensure_household(
        db_session,
        test_user,
        name="API Recommendations Household",
        invite_code="api-recommend-household",
    )
    await add_inventory_item(db_session, test_user, "eggs", household_id=household.id)
    await add_inventory_item(db_session, test_user, "butter", household_id=household.id)

    response = await client.post("/v1/recommendations", headers=test_headers, json={})

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["recipes"]) >= 1
    assert payload["recipes"][0]["title"] == "Scrambled Eggs"


@pytest.mark.asyncio
async def test_api_endpoint_recommendations_empty_inventory(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
) -> None:
    response = await client.post("/v1/recommendations", headers=test_headers, json={})

    assert response.status_code == 200
    payload = response.json()
    assert "recipes" in payload
    if payload["recipes"]:
        assert all(recipe["coveragePct"] == pytest.approx(0.0) for recipe in payload["recipes"])


@pytest.mark.asyncio
async def test_recommendations_scoped_by_household(
    client: httpx.AsyncClient,
    test_headers: dict[str, str],
    test_user: User,
    db_session: AsyncSession,
) -> None:
    user_household = await ensure_household(
        db_session,
        test_user,
        name="Recommendation Scope User Household",
        invite_code="recommend-scope-user-house",
    )
    other_user = User(email="recommendations-other-user@example.com")
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)
    other_household = await ensure_household(
        db_session,
        other_user,
        name="Recommendation Scope Other Household",
        invite_code="recommend-scope-other-hh",
    )

    await add_inventory_item(db_session, test_user, "eggs", household_id=user_household.id)
    await add_inventory_item(db_session, test_user, "butter", household_id=user_household.id)
    await add_inventory_item(db_session, other_user, "beef", household_id=other_household.id)

    response = await client.post(
        "/v1/recommendations",
        headers=test_headers,
        json={"max_prep_minutes": 15},
    )

    assert response.status_code == 200
    payload = response.json()
    titles = [recipe["title"] for recipe in payload["recipes"]]
    assert "Scrambled Eggs" in titles

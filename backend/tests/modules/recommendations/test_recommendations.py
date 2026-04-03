# pyright: reportAny=false, reportUnusedParameter=false, reportUnusedCallResult=false, reportMissingImports=false, reportUnknownVariableType=false

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import date, timedelta

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
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
) -> InventoryItem:
    item = InventoryItem(
        user_id=user.id,
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
    for name in ["beef", "potatoes", "carrots", "onions", "eggs", "butter"]:
        await add_inventory_item(db_session, test_user, name)

    scorer = RecipeScorer(today=date(2026, 4, 3))
    inventory_items = await RecommendationService(db_session).list_inventory_items(test_user.id)

    fast_score = scorer.score_recipe(get_recipe("Scrambled Eggs"), inventory_items)
    slow_score = scorer.score_recipe(get_recipe("Beef Stew"), inventory_items)

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

    assert [recommendation.title for recommendation in recommendations] == ["Greek Yogurt Bowl"]


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

    recommendations = await RecommendationService(db_session).get_recommendations(
        test_user.id,
        RecommendationRequest(max_prep_minutes=10),
    )

    smoothie = next(recommendation for recommendation in recommendations if recommendation.title == "Banana Smoothie")
    assert smoothie.missing_items == ["bananas"]


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
    await add_inventory_item(db_session, test_user, "eggs")
    await add_inventory_item(db_session, test_user, "butter")

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
        assert all(recipe["coverage_pct"] == pytest.approx(0.0) for recipe in payload["recipes"])

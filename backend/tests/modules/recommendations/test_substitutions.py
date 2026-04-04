from __future__ import annotations

from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory_item import InventoryItem, InventorySource, InventoryStatus
from app.models.user import User
from app.modules.recommendations.schemas import RecommendationRequest
from app.modules.recommendations.scorer import RecipeScorer
from app.modules.recommendations.service import RecommendationService


async def _seed_inventory(db_session: AsyncSession, user: User, canonical_name: str) -> None:
    db_session.add(
        InventoryItem(
            user_id=user.id,
            household_id=None,
            display_name=canonical_name.title(),
            quantity=1.0,
            unit="unit",
            storage_location="fridge",
            estimated_expiry_date=date.today() + timedelta(days=7),
            confidence=0.9,
            status=InventoryStatus.ACTIVE,
            source=InventorySource.MANUAL,
            canonical_name=canonical_name,
        )
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_recipe_shows_substitution_options(db_session: AsyncSession) -> None:
    user = User(email="substitutions@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    await _seed_inventory(db_session, user, "eggs")
    await _seed_inventory(db_session, user, "margarine")

    recommendations = await RecommendationService(
        db_session,
        recipes=[
            {
                "id": "sub-1",
                "title": "Butter Eggs",
                "prep_minutes": 10,
                "dietary_tags": ["vegetarian"],
                "ingredients": [
                    {"canonical_name": "eggs", "quantity": 2.0, "unit": "unit"},
                    {"canonical_name": "butter", "quantity": 1.0, "unit": "tbsp"},
                ],
            }
        ],
    ).get_recommendations(user.id, RecommendationRequest())

    assert recommendations[0].substitutions == ["margarine"]


@pytest.mark.asyncio
async def test_dietary_fit_scoring_boosts_matching_preferences() -> None:
    scorer = RecipeScorer(today=date(2026, 4, 3))
    recipe: dict[str, object] = {
        "id": "diet-1",
        "title": "Veg Bowl",
        "prep_minutes": 15,
        "dietary_tags": ["vegetarian", "gluten-free"],
        "ingredients": [],
    }

    matching = scorer.score_breakdown(recipe, [], dietary_preferences=["vegetarian"])
    non_matching = scorer.score_breakdown(recipe, [], dietary_preferences=["vegan"])

    assert matching.score > non_matching.score


@pytest.mark.asyncio
async def test_missing_items_list_excludes_substitutable_items(db_session: AsyncSession) -> None:
    user = User(email="substitutions-missing@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    await _seed_inventory(db_session, user, "margarine")

    recommendations = await RecommendationService(
        db_session,
        recipes=[
            {
                "id": "sub-2",
                "title": "Toast",
                "prep_minutes": 5,
                "dietary_tags": [],
                "ingredients": [{"canonical_name": "butter", "quantity": 1.0, "unit": "tbsp"}],
            }
        ],
    ).get_recommendations(user.id, RecommendationRequest())

    assert recommendations[0].missing_items == []

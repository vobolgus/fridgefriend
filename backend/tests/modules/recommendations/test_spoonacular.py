from __future__ import annotations

from collections.abc import Mapping

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.modules.recommendations.interfaces import RecipeSourceInterface
from app.modules.recommendations.mock_recipe_source import MockRecipeSource
from app.modules.recommendations.schemas import RecommendationRequest
from app.modules.recommendations.service import RecommendationService
from app.modules.recommendations.spoonacular import QueryParamValue
from app.modules.recommendations.spoonacular import SpoonacularClient


class _BrokenRecipeSource:
    async def search_recipes(self, ingredients: list[str], count: int = 10) -> list[dict[str, object]]:
        _ = (ingredients, count)
        raise RuntimeError("boom")


class _Response:
    def __init__(self, payload: list[dict[str, object]]) -> None:
        self._payload: list[dict[str, object]] = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> list[dict[str, object]]:
        return self._payload


class _Client:
    def __init__(self, payload: list[dict[str, object]]) -> None:
        self._payload: list[dict[str, object]] = payload

    async def get(self, url: str, params: Mapping[str, QueryParamValue]) -> _Response:
        assert "recipes/findByIngredients" in url
        assert params["number"] == 2
        return _Response(self._payload)


@pytest.mark.asyncio
async def test_spoonacular_interface_protocol() -> None:
    assert getattr(RecipeSourceInterface, "_is_protocol", False) is True


@pytest.mark.asyncio
async def test_mock_recipe_source_returns_recipes() -> None:
    recipes = await MockRecipeSource().search_recipes(["milk"], count=3)

    assert len(recipes) == 3
    assert recipes[0]["title"] == "Scrambled Eggs"
    assert recipes[0]["image_url"] == "https://img.spoonacular.com/recipes/641803-556x370.jpg"
    assert recipes[0]["instructions"]
    assert recipes[0]["dietary_tags"] == ["gluten-free", "high-protein"]


@pytest.mark.asyncio
async def test_spoonacular_fallback_on_error(db_session: AsyncSession) -> None:
    user = User(email="spoonacular-fallback@example.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    recommendations = await RecommendationService(
        db_session,
        recipe_source=_BrokenRecipeSource(),
    ).get_recommendations(user.id, RecommendationRequest())

    assert recommendations
    assert {recommendation.title for recommendation in recommendations}.issuperset(
        {"Scrambled Eggs", "Banana Smoothie"}
    )


@pytest.mark.asyncio
async def test_spoonacular_maps_response_payload() -> None:
    client = SpoonacularClient(
        "test-key",
        client=_Client(
            [
                {
                    "id": 42,
                    "title": "Veggie Pasta",
                    "readyInMinutes": 18,
                    "image": "https://img.spoonacular.com/recipes/42-556x370.jpg",
                    "usedIngredients": [{"name": "pasta", "amount": 200, "unit": "g"}],
                    "missedIngredients": [{"name": "tomatoes", "amount": 2, "unit": "piece"}],
                }
            ]
        ),
    )

    recipes = await client.search_recipes(["pasta", "tomatoes"], count=2)

    assert recipes == [
        {
            "id": "42",
            "title": "Veggie Pasta",
            "prep_minutes": 18,
            "image_url": "https://img.spoonacular.com/recipes/42-556x370.jpg",
            "source_url": None,
            "summary": None,
            "instructions": [],
            "cuisines": [],
            "servings": None,
            "nutrition": None,
            "dietary_tags": [],
            "ingredients": [
                {"canonical_name": "pasta", "quantity": 200.0, "unit": "g"},
                {"canonical_name": "tomatoes", "quantity": 2.0, "unit": "piece"},
            ],
        }
    ]

from __future__ import annotations

from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.recommendations.mock_recipe_source import MockRecipeSource
from app.modules.recommendations.router import get_recommendation_service


def _recipe_source(service: object) -> object:
    return cast(dict[str, object], vars(service))["_recipe_source"]


@pytest.mark.asyncio
async def test_mock_source_default(db_session: AsyncSession) -> None:
    previous_recipe_source = settings.RECIPE_SOURCE
    previous_api_key = settings.SPOONACULAR_API_KEY
    settings.RECIPE_SOURCE = "mock"
    settings.SPOONACULAR_API_KEY = ""

    try:
        service = await get_recommendation_service(db_session)
    finally:
        settings.RECIPE_SOURCE = previous_recipe_source
        settings.SPOONACULAR_API_KEY = previous_api_key

    assert isinstance(_recipe_source(service), MockRecipeSource)


@pytest.mark.asyncio
async def test_opensearch_source(db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.recommendations import opensearch_client

    class FakeOpenSearchRecipeSource:
        async def search_recipes(self, ingredients: list[str], count: int = 50) -> list[dict[str, object]]:
            _ = (ingredients, count)
            return []

    previous_recipe_source = settings.RECIPE_SOURCE
    settings.RECIPE_SOURCE = "opensearch"
    monkeypatch.setattr(opensearch_client, "OpenSearchRecipeSource", FakeOpenSearchRecipeSource)

    try:
        service = await get_recommendation_service(db_session)
    finally:
        settings.RECIPE_SOURCE = previous_recipe_source

    assert isinstance(_recipe_source(service), FakeOpenSearchRecipeSource)


@pytest.mark.asyncio
async def test_spoonacular_source(db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.recommendations import spoonacular

    class FakeSpoonacularClient:
        def __init__(self, api_key: str) -> None:
            self.api_key: str = api_key

        async def search_recipes(self, ingredients: list[str], count: int = 10) -> list[dict[str, object]]:
            _ = (ingredients, count)
            return []

    previous_recipe_source = settings.RECIPE_SOURCE
    previous_api_key = settings.SPOONACULAR_API_KEY
    settings.RECIPE_SOURCE = "spoonacular"
    settings.SPOONACULAR_API_KEY = "spoonacular-test-key"
    monkeypatch.setattr(spoonacular, "SpoonacularClient", FakeSpoonacularClient)

    try:
        service = await get_recommendation_service(db_session)
    finally:
        settings.RECIPE_SOURCE = previous_recipe_source
        settings.SPOONACULAR_API_KEY = previous_api_key

    recipe_source = _recipe_source(service)

    assert isinstance(recipe_source, FakeSpoonacularClient)
    assert recipe_source.api_key == "spoonacular-test-key"

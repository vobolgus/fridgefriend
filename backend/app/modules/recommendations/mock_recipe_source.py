from __future__ import annotations

from .fixture_recipes import FIXTURE_RECIPES


class MockRecipeSource:
    async def search_recipes(self, ingredients: list[str], count: int = 10) -> list[dict[str, object]]:
        _ = ingredients
        return FIXTURE_RECIPES[:count]

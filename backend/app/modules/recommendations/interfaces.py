from typing import Protocol


class RecipeSourceInterface(Protocol):
    async def search_recipes(self, ingredients: list[str], count: int = 10) -> list[dict[str, object]]: ...

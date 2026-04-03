from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory_item import InventoryItem

from .fixture_recipes import FIXTURE_RECIPES
from .schemas import FixtureRecipe, RecommendationRequest, RecipeRecommendation
from .scorer import RecipeScorer


class RecommendationService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        scorer: RecipeScorer | None = None,
        recipes: list[dict[str, object]] | None = None,
    ) -> None:
        self._session: AsyncSession = session
        self._scorer: RecipeScorer = scorer or RecipeScorer()
        self._recipes: list[FixtureRecipe] = [
            FixtureRecipe.model_validate(recipe) for recipe in (recipes or FIXTURE_RECIPES)
        ]

    async def get_recommendations(
        self,
        user_id: UUID,
        request: RecommendationRequest,
    ) -> list[RecipeRecommendation]:
        inventory_items = await self.list_inventory_items(user_id)
        normalized_tags = {tag.lower() for tag in request.dietary_tags}
        excluded_ingredients = {ingredient.lower() for ingredient in request.excluded_ingredients}
        recommendations: list[RecipeRecommendation] = []

        for recipe in self._recipes:
            if normalized_tags and not normalized_tags.issubset({tag.lower() for tag in recipe.dietary_tags}):
                continue
            if request.max_prep_minutes is not None and recipe.prep_minutes > request.max_prep_minutes:
                continue
            ingredient_names = [ingredient.canonical_name.lower() for ingredient in recipe.ingredients]
            if excluded_ingredients and excluded_ingredients.intersection(ingredient_names):
                continue

            breakdown = self._scorer.score_breakdown(recipe, inventory_items)
            recommendations.append(
                RecipeRecommendation(
                    id=recipe.id,
                    title=recipe.title,
                    use_soon_score=breakdown.use_soon_score,
                    coverage_pct=breakdown.coverage_pct,
                    missing_items=breakdown.missing_items,
                    substitutions=[],
                    prep_minutes=recipe.prep_minutes,
                    score=breakdown.score,
                ),
            )

        recommendations.sort(key=lambda recommendation: recommendation.score, reverse=True)
        return recommendations[:10]

    async def list_inventory_items(self, user_id: UUID) -> list[InventoryItem]:
        statement = select(InventoryItem).where(InventoryItem.user_id == user_id)
        result = await self._session.execute(statement)
        return list(result.scalars().all())

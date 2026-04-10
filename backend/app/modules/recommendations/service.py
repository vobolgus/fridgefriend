from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.events import RecommendationSession
from app.models.inventory_item import InventoryItem, InventoryStatus

from .interfaces import RecipeSourceInterface
from .mock_recipe_source import MockRecipeSource
from .schemas import FixtureRecipe, RecommendationRequest, RecipeRecommendation
from .scorer import RecipeScorer


logger = logging.getLogger(__name__)


class RecommendationService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        scorer: RecipeScorer | None = None,
        recipes: list[dict[str, object]] | None = None,
        recipe_source: RecipeSourceInterface | None = None,
    ) -> None:
        self._session: AsyncSession = session
        self._scorer: RecipeScorer = scorer or RecipeScorer()
        self._recipe_source: RecipeSourceInterface = recipe_source or MockRecipeSource()
        self._recipe_overrides: list[FixtureRecipe] | None = (
            [FixtureRecipe.model_validate(recipe) for recipe in recipes] if recipes is not None else None
        )

    async def get_recommendations(
        self,
        user_id: UUID,
        request: RecommendationRequest,
        household_id: UUID | None = None,
    ) -> list[RecipeRecommendation]:
        recommendations, _ = await self.get_recommendations_with_source(
            user_id,
            request,
            household_id=household_id,
        )
        return recommendations

    async def get_recommendations_with_source(
        self,
        user_id: UUID,
        request: RecommendationRequest,
        household_id: UUID | None = None,
    ) -> tuple[list[RecipeRecommendation], str]:
        inventory_items = await self.list_inventory_items(user_id, household_id)
        recipes, source = await self._load_recipes(inventory_items)
        normalized_tags = {tag.lower() for tag in request.dietary_tags}
        excluded_ingredients = {ingredient.lower() for ingredient in request.excluded_ingredients}
        recommendations: list[RecipeRecommendation] = []

        for recipe in recipes:
            if normalized_tags and not normalized_tags.issubset({tag.lower() for tag in recipe.dietary_tags}):
                continue
            if request.max_prep_minutes is not None and recipe.prep_minutes > request.max_prep_minutes:
                continue
            ingredient_names = [ingredient.canonical_name.lower() for ingredient in recipe.ingredients]
            if excluded_ingredients and excluded_ingredients.intersection(ingredient_names):
                continue

            breakdown = self._scorer.score_breakdown(
                recipe,
                inventory_items,
                dietary_preferences=request.dietary_tags,
            )
            recommendations.append(
                RecipeRecommendation.model_validate(
                    {
                        "id": recipe.id,
                        "title": recipe.title,
                        "useSoonScore": breakdown.use_soon_score,
                        "coveragePct": breakdown.coverage_pct,
                        "missingItems": breakdown.missing_items,
                        "substitutions": breakdown.substitutions,
                        "prepMinutes": recipe.prep_minutes,
                        "imageUrl": recipe.image_url,
                        "sourceUrl": recipe.source_url,
                        "summary": recipe.summary,
                        "instructions": recipe.instructions,
                        "cuisines": recipe.cuisines,
                        "servings": recipe.servings,
                        "nutrition": recipe.nutrition,
                        "dietaryTags": recipe.dietary_tags,
                        "ingredients": recipe.ingredients,
                        "score": breakdown.score,
                    }
                ),
            )

        recommendations.sort(key=lambda recommendation: recommendation.score, reverse=True)
        top_recommendations = recommendations[:10]

        if household_id is not None:
            session_record = RecommendationSession(
                household_id=household_id,
                request_params=request.model_dump(mode="json"),
                recipes_shown=[recommendation.id for recommendation in top_recommendations],
            )
            try:
                self._session.add(session_record)
                await self._session.flush()
                await self._session.commit()
            except Exception:
                await self._session.rollback()

        return top_recommendations, source

    async def list_inventory_items(self, user_id: UUID, household_id: UUID | None = None) -> list[InventoryItem]:
        if household_id is not None:
            statement = select(InventoryItem).where(InventoryItem.household_id == household_id)
        else:
            statement = select(InventoryItem).where(InventoryItem.user_id == user_id)
        statement = statement.where(InventoryItem.status.notin_([InventoryStatus.USED, InventoryStatus.DISCARDED]))
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    async def _load_recipes(self, inventory_items: list[InventoryItem]) -> tuple[list[FixtureRecipe], str]:
        if self._recipe_overrides is not None:
            return self._recipe_overrides, "live"

        ingredient_names = sorted({item.canonical_name.lower() for item in inventory_items if item.canonical_name})
        try:
            raw_recipes = await self._recipe_source.search_recipes(ingredient_names, count=10)
            source = "live"
        except Exception as exc:
            logger.exception("Recipe lookup failed, falling back to mock recipes: %s", exc)
            raw_recipes = await MockRecipeSource().search_recipes(ingredient_names, count=10)
            source = "mock"
        return [FixtureRecipe.model_validate(recipe) for recipe in raw_recipes], source

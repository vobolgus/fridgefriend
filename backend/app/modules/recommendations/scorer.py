from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.models.inventory_item import InventoryItem, InventoryStatus
from app.modules.expiry.urgency import UrgencyBucket, get_urgency_bucket

from .schemas import FixtureRecipe
from .substitutions import SUBSTITUTIONS


@dataclass(slots=True)
class ScoreBreakdown:
    coverage_pct: float
    use_soon_score: float
    prep_score: float
    dietary_fit_score: float
    substitution_score: float
    score: float
    missing_items: list[str]
    substitutions: list[str]


class RecipeScorer:
    def __init__(self, today: date | None = None) -> None:
        self._today: date = today or date.today()

    def score_recipe(
        self,
        recipe: FixtureRecipe | dict[str, object],
        inventory_items: list[InventoryItem],
    ) -> float:
        return self.score_breakdown(recipe, inventory_items).score

    def score_breakdown(
        self,
        recipe: FixtureRecipe | dict[str, object],
        inventory_items: list[InventoryItem],
        dietary_preferences: list[str] | None = None,
    ) -> ScoreBreakdown:
        recipe_model = recipe if isinstance(recipe, FixtureRecipe) else FixtureRecipe.model_validate(recipe)
        recipe_ingredients = [ingredient.canonical_name.lower() for ingredient in recipe_model.ingredients]
        recipe_ingredient_set = set(recipe_ingredients)
        active_inventory = [item for item in inventory_items if self._is_active(item)]
        inventory_names = {item.canonical_name.lower() for item in active_inventory}
        covered = recipe_ingredient_set & inventory_names
        coverage_pct = len(covered) / len(recipe_ingredient_set) if recipe_ingredient_set else 0.0
        use_soon_score = self._urgency_bonus(active_inventory, covered)
        prep_score = max(0.0, 0.1 - recipe_model.prep_minutes / 1000)
        substitutions: list[str] = []
        missing_items: list[str] = []
        substitution_score = 0.0
        for ingredient in recipe_model.ingredients:
            ingredient_name = ingredient.canonical_name.lower()
            if ingredient_name in covered:
                continue
            available_substitutions = [
                substitution
                for substitution in SUBSTITUTIONS.get(ingredient_name, [])
                if substitution.lower() in inventory_names
            ]
            if available_substitutions:
                substitutions.extend(available_substitutions)
                substitution_score += 0.05 * len(available_substitutions)
                continue
            missing_items.append(ingredient.canonical_name)

        dietary_fit_score = self._dietary_fit_bonus(recipe_model, dietary_preferences or [])
        score = coverage_pct * 0.5 + use_soon_score + prep_score + dietary_fit_score + min(substitution_score, 0.15)

        return ScoreBreakdown(
            coverage_pct=coverage_pct,
            use_soon_score=use_soon_score,
            prep_score=prep_score,
            dietary_fit_score=dietary_fit_score,
            substitution_score=min(substitution_score, 0.15),
            score=score,
            missing_items=missing_items,
            substitutions=list(dict.fromkeys(substitutions)),
        )

    def _urgency_bonus(self, inventory_items: list[InventoryItem], covered: set[str]) -> float:
        urgency_bonus = 0.0
        for item in inventory_items:
            if item.canonical_name.lower() not in covered:
                continue

            urgency_bucket = get_urgency_bucket(item.estimated_expiry_date, self._today)
            if urgency_bucket in {UrgencyBucket.EXPIRED, UrgencyBucket.TODAY}:
                urgency_bonus += 0.3
            elif urgency_bucket == UrgencyBucket.THIS_WEEK:
                urgency_bonus += 0.15

        return min(urgency_bonus, 0.4)

    @staticmethod
    def _dietary_fit_bonus(recipe: FixtureRecipe, dietary_preferences: list[str]) -> float:
        normalized_preferences = {tag.lower() for tag in dietary_preferences}
        if not normalized_preferences:
            return 0.0
        recipe_tags = {tag.lower() for tag in recipe.dietary_tags}
        matched = normalized_preferences & recipe_tags
        return min(0.05 * len(matched), 0.2)

    @staticmethod
    def _is_active(item: InventoryItem) -> bool:
        return item.status not in {InventoryStatus.USED, InventoryStatus.DISCARDED}

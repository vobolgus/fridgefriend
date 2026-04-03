from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.models.inventory_item import InventoryItem, InventoryStatus
from app.modules.expiry.urgency import UrgencyBucket, get_urgency_bucket

from .schemas import FixtureRecipe


@dataclass(slots=True)
class ScoreBreakdown:
    coverage_pct: float
    use_soon_score: float
    prep_score: float
    score: float
    missing_items: list[str]


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
        missing_items = [
            ingredient.canonical_name
            for ingredient in recipe_model.ingredients
            if ingredient.canonical_name.lower() not in covered
        ]
        score = coverage_pct * 0.5 + use_soon_score + prep_score

        return ScoreBreakdown(
            coverage_pct=coverage_pct,
            use_soon_score=use_soon_score,
            prep_score=prep_score,
            score=score,
            missing_items=missing_items,
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
    def _is_active(item: InventoryItem) -> bool:
        return str(item.status) == InventoryStatus.ACTIVE.value or item.status == InventoryStatus.ACTIVE

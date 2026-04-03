# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportUnusedVariable=false, reportArgumentType=false, reportOperatorIssue=false, reportConstantRedefinition=false

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
import uuid

from app.models.inventory_item import InventoryItem, InventoryStatus
from app.modules.expiry.urgency import UrgencyBucket, get_urgency_bucket
from app.modules.planning.schemas import PlanDay, PlanResult, RecipeIngredient
from app.modules.planning.shopping_list import derive_shopping_list

try:
    from app.modules.recommendations.fixture_recipes import FIXTURE_RECIPES as PLANNING_RECIPES
except ImportError:
    PLANNING_RECIPES: list[dict[str, object]] = [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "title": "Scrambled Eggs",
            "prep_minutes": 10,
            "dietary_tags": ["vegetarian"],
            "ingredients": [
                {"canonical_name": "eggs", "quantity": 2.0, "unit": "unit"},
                {"canonical_name": "butter", "quantity": 1.0, "unit": "tbsp"},
            ],
        },
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "title": "Chicken Stir Fry",
            "prep_minutes": 20,
            "dietary_tags": [],
            "ingredients": [
                {"canonical_name": "chicken", "quantity": 500.0, "unit": "g"},
                {"canonical_name": "spinach", "quantity": 100.0, "unit": "g"},
            ],
        },
        {
            "id": "33333333-3333-3333-3333-333333333333",
            "title": "Vegetable Rice",
            "prep_minutes": 30,
            "dietary_tags": ["vegetarian"],
            "ingredients": [
                {"canonical_name": "rice", "quantity": 200.0, "unit": "g"},
                {"canonical_name": "carrots", "quantity": 1.0, "unit": "piece"},
            ],
        },
    ]


@dataclass(slots=True)
class _NormalizedIngredient:
    name: str
    quantity: float
    unit: str


@dataclass(slots=True)
class _NormalizedRecipe:
    id: str
    title: str
    prep_minutes: int
    dietary_tags: set[str]
    ingredients: list[_NormalizedIngredient]


@dataclass(slots=True)
class _InventorySnapshot:
    quantity: float
    unit: str
    expiry_date: date


class MealPlanner:
    def generate_plan(
        self,
        user_inventory: list[InventoryItem],
        days: int,
        dietary_tags: list[str] | None = None,
        max_prep_minutes: int | None = None,
        recipes_db: Sequence[Mapping[str, object]] | None = None,
    ) -> PlanResult:
        inventory = [item for item in user_inventory if item.status == InventoryStatus.ACTIVE]
        remaining_inventory = self._build_remaining_inventory(inventory)
        recipes = self._normalize_recipes(recipes_db or PLANNING_RECIPES)
        filtered_recipes = self._filter_recipes(recipes, dietary_tags or [], max_prep_minutes)
        candidate_recipes = filtered_recipes or recipes
        today = date.today()
        used_recipe_ids: set[str] = set()
        plan_days: list[PlanDay] = []

        for offset in range(days):
            recipe = self._pick_best_recipe(candidate_recipes, remaining_inventory, used_recipe_ids, today)
            reserved_items = self._reserve_ingredients(recipe, remaining_inventory)
            plan_days.append(
                PlanDay(
                    date=today + timedelta(days=offset),
                    recipe_id=recipe.id,
                    recipe_title=recipe.title,
                    servings=2,
                    reserved_items=reserved_items,
                    recipe_ingredients=[
                        RecipeIngredient(
                            ingredient_name=ingredient.name,
                            quantity=ingredient.quantity,
                            unit=ingredient.unit,
                        )
                        for ingredient in recipe.ingredients
                    ],
                ),
            )
            used_recipe_ids.add(recipe.id)

        plan = PlanResult(plan_id=str(uuid.uuid4()), days=plan_days, shopping_list=[])
        plan.shopping_list = derive_shopping_list(plan, user_inventory)
        return plan

    def _filter_recipes(
        self,
        recipes: list[_NormalizedRecipe],
        dietary_tags: list[str],
        max_prep_minutes: int | None,
    ) -> list[_NormalizedRecipe]:
        normalized_tags = {tag.lower() for tag in dietary_tags}
        filtered: list[_NormalizedRecipe] = []
        for recipe in recipes:
            if normalized_tags and not normalized_tags.issubset(recipe.dietary_tags):
                continue
            if max_prep_minutes is not None and recipe.prep_minutes > max_prep_minutes:
                continue
            filtered.append(recipe)
        return filtered

    def _pick_best_recipe(
        self,
        recipes: list[_NormalizedRecipe],
        remaining_inventory: dict[str, _InventorySnapshot],
        used_recipe_ids: set[str],
        today: date,
    ) -> _NormalizedRecipe:
        scored = sorted(
            recipes,
            key=lambda recipe: self._score_recipe(recipe, remaining_inventory, used_recipe_ids, today),
            reverse=True,
        )
        return scored[0]

    def _score_recipe(
        self,
        recipe: _NormalizedRecipe,
        remaining_inventory: dict[str, _InventorySnapshot],
        used_recipe_ids: set[str],
        today: date,
    ) -> tuple[float, int, int, int, int]:
        urgent_score = 0.0
        coverage = 0
        complete_matches = 0

        for ingredient in recipe.ingredients:
            inventory_item = remaining_inventory.get(ingredient.name)
            if inventory_item is None:
                continue

            available_quantity = inventory_item.quantity
            if available_quantity <= 0:
                continue

            coverage += 1
            expiry_date = inventory_item.expiry_date
            bucket = get_urgency_bucket(expiry_date, today)
            urgent_score += {
                UrgencyBucket.EXPIRED: 5.0,
                UrgencyBucket.TODAY: 4.0,
                UrgencyBucket.THIS_WEEK: 2.0,
                UrgencyBucket.SAFE_LATER: 1.0,
            }[bucket]
            urgent_score += max(0.0, 30.0 - float((expiry_date - today).days)) / 100.0

            if available_quantity >= ingredient.quantity:
                complete_matches += 1

        repeat_bonus = 1 if recipe.id not in used_recipe_ids else 0
        return (urgent_score, complete_matches, coverage, repeat_bonus, -recipe.prep_minutes)

    def _reserve_ingredients(
        self,
        recipe: _NormalizedRecipe,
        remaining_inventory: dict[str, _InventorySnapshot],
    ) -> list[str]:
        reserved_items: list[str] = []
        for ingredient in recipe.ingredients:
            inventory_item = remaining_inventory.get(ingredient.name)
            if inventory_item is None:
                continue

            available_quantity = inventory_item.quantity
            if available_quantity <= 0:
                continue

            inventory_item.quantity = max(0.0, available_quantity - ingredient.quantity)
            reserved_items.append(ingredient.name)

        return reserved_items

    def _build_remaining_inventory(
        self,
        inventory: list[InventoryItem],
    ) -> dict[str, _InventorySnapshot]:
        remaining: dict[str, _InventorySnapshot] = {}
        for item in sorted(inventory, key=lambda current: current.estimated_expiry_date):
            key = item.canonical_name.strip().lower()
            if key not in remaining:
                remaining[key] = _InventorySnapshot(quantity=0.0, unit=item.unit, expiry_date=item.estimated_expiry_date)
            remaining[key].quantity += item.quantity
            if item.estimated_expiry_date < remaining[key].expiry_date:
                remaining[key].expiry_date = item.estimated_expiry_date
        return remaining

    def _normalize_recipes(self, recipes_db: Sequence[Mapping[str, object]]) -> list[_NormalizedRecipe]:
        normalized: list[_NormalizedRecipe] = []
        for recipe in recipes_db:
            ingredients: list[_NormalizedIngredient] = []
            recipe_ingredients = recipe.get("ingredients", [])
            if not isinstance(recipe_ingredients, list):
                recipe_ingredients = []
            for ingredient_payload in recipe_ingredients:
                if not isinstance(ingredient_payload, dict):
                    continue
                ingredient_name = str(
                    ingredient_payload.get("canonical_name")
                    or ingredient_payload.get("name")
                    or ingredient_payload.get("ingredient_name"),
                ).strip().lower()
                if not ingredient_name:
                    continue
                ingredients.append(
                    _NormalizedIngredient(
                        name=ingredient_name,
                        quantity=float(ingredient_payload.get("quantity", 0.0)),
                        unit=str(ingredient_payload.get("unit", "unit")),
                    ),
                )

            normalized.append(
                _NormalizedRecipe(
                    id=str(recipe.get("id")),
                    title=str(recipe.get("title")),
                    prep_minutes=int(recipe.get("prep_minutes", 0)),
                    dietary_tags={str(tag).lower() for tag in list(recipe.get("dietary_tags", []))},
                    ingredients=ingredients,
                ),
            )
        return normalized

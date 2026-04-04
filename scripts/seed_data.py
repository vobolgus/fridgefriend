# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select

from backend.app.core.database import AsyncSessionLocal
from backend.app.models.canonical_ingredient import CanonicalIngredient, ShelfLifeRule
from backend.app.models.recipe import Recipe
from backend.app.modules.expiry.rules import SHELF_LIFE_DAYS
from backend.app.modules.recommendations.fixture_recipes import FIXTURE_RECIPES


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        # Seed canonical ingredients and shelf-life rules
        ingredients_by_name: dict[str, CanonicalIngredient] = {}

        for (name, storage_type), (shelf_life_days, confidence) in SHELF_LIFE_DAYS.items():
            ingredient = ingredients_by_name.get(name)
            if ingredient is None:
                existing = await session.execute(
                    select(CanonicalIngredient).where(CanonicalIngredient.name == name),
                )
                ingredient = existing.scalar_one_or_none()
                if ingredient is None:
                    ingredient = CanonicalIngredient(name=name, category="general", aliases=[])
                    session.add(ingredient)
                    await session.flush()
                ingredients_by_name[name] = ingredient

            rule_result = await session.execute(
                select(ShelfLifeRule).where(
                    ShelfLifeRule.canonical_ingredient_id == ingredient.id,
                    ShelfLifeRule.storage_type == storage_type,
                ),
            )
            rule = rule_result.scalar_one_or_none()
            if rule is None:
                session.add(
                    ShelfLifeRule(
                        canonical_ingredient_id=ingredient.id,
                        storage_type=storage_type,
                        shelf_life_days=shelf_life_days,
                        confidence=confidence,
                    ),
                )

        # Seed fixture recipes
        for recipe_data in FIXTURE_RECIPES:
            recipe_id = uuid.UUID(str(recipe_data["id"]))
            existing_recipe = await session.execute(
                select(Recipe).where(Recipe.id == recipe_id),
            )
            if existing_recipe.scalar_one_or_none() is None:
                recipe = Recipe(
                    id=recipe_id,
                    title=str(recipe_data["title"]),
                    prep_minutes=int(recipe_data.get("prep_minutes", 0)),
                    dietary_tags=list(recipe_data.get("dietary_tags", [])),
                    ingredients=list(recipe_data.get("ingredients", [])),
                )
                session.add(recipe)

        await session.commit()
        print("Seed complete: ingredients, shelf-life rules, and recipes.")


if __name__ == "__main__":
    asyncio.run(seed())

from __future__ import annotations

from collections.abc import Mapping
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.canonical_ingredient import CanonicalIngredient, ShelfLifeRule

SHELF_LIFE_DAYS: dict[tuple[str, str], tuple[int, float]] = {
    ("milk", "fridge"): (7, 0.95),
    ("milk", "freezer"): (90, 0.90),
    ("eggs", "fridge"): (21, 0.90),
    ("butter", "fridge"): (30, 0.85),
    ("cheese", "fridge"): (14, 0.80),
    ("chicken", "fridge"): (2, 0.95),
    ("chicken", "freezer"): (270, 0.90),
    ("beef", "fridge"): (3, 0.95),
    ("beef", "freezer"): (365, 0.90),
    ("bread", "pantry"): (5, 0.85),
    ("bread", "freezer"): (90, 0.85),
    ("apples", "fridge"): (21, 0.80),
    ("apples", "pantry"): (7, 0.75),
    ("bananas", "pantry"): (5, 0.80),
    ("spinach", "fridge"): (5, 0.85),
    ("carrots", "fridge"): (21, 0.85),
    ("tomatoes", "pantry"): (5, 0.80),
    ("tomatoes", "fridge"): (10, 0.80),
    ("pasta", "pantry"): (730, 0.95),
    ("rice", "pantry"): (730, 0.95),
    ("yogurt", "fridge"): (14, 0.90),
    ("lettuce", "fridge"): (7, 0.85),
    ("onions", "pantry"): (60, 0.85),
    ("potatoes", "pantry"): (30, 0.80),
}
DEFAULT_SHELF_LIFE: tuple[int, float] = (7, 0.40)


class ShelfLifeRules:
    def __init__(
        self,
        shelf_life_days: Mapping[tuple[str, str], tuple[int, float]] | None = None,
        default_shelf_life: tuple[int, float] = DEFAULT_SHELF_LIFE,
    ) -> None:
        self._shelf_life_days: dict[tuple[str, str], tuple[int, float]] = dict(
            shelf_life_days or SHELF_LIFE_DAYS,
        )
        self._default_shelf_life: tuple[int, float] = default_shelf_life

    def get_shelf_life_days(self, ingredient_name: str, storage_location: str) -> tuple[int, float]:
        normalized_name = ingredient_name.strip().lower()
        normalized_location = storage_location.strip().lower()

        exact_match = self._shelf_life_days.get((normalized_name, normalized_location))
        if exact_match is not None:
            return exact_match

        for (name, _location), shelf_life in self._shelf_life_days.items():
            if name == normalized_name:
                return shelf_life

        return self._default_shelf_life


async def load_db_shelf_life_rules(
    session: AsyncSession,
) -> dict[tuple[str, str], tuple[int, float]]:
    statement = (
        select(
            CanonicalIngredient.name,
            ShelfLifeRule.storage_type,
            ShelfLifeRule.shelf_life_days,
            ShelfLifeRule.confidence,
        )
        .join(ShelfLifeRule, ShelfLifeRule.canonical_ingredient_id == CanonicalIngredient.id)
        .order_by(CanonicalIngredient.name.asc(), ShelfLifeRule.storage_type.asc())
    )
    result = await session.execute(statement)
    rows = cast(list[tuple[str, str, int, float]], result.all())

    return {
        (name.strip().lower(), storage_type.strip().lower()): (shelf_life_days, confidence)
        for name, storage_type, shelf_life_days, confidence in rows
    }


class DatabaseShelfLifeRules(ShelfLifeRules):
    def __init__(
        self,
        db_rules: dict[tuple[str, str], tuple[int, float]] | None = None,
        *,
        shelf_life_days: Mapping[tuple[str, str], tuple[int, float]] | None = None,
        default_shelf_life: tuple[int, float] = DEFAULT_SHELF_LIFE,
    ) -> None:
        merged = dict(SHELF_LIFE_DAYS)
        if shelf_life_days:
            merged.update(shelf_life_days)
        if db_rules:
            merged.update(db_rules)
        super().__init__(shelf_life_days=merged, default_shelf_life=default_shelf_life)

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.canonical_ingredient import CanonicalIngredient, ShelfLifeRule
from app.modules.expiry.rules import DatabaseShelfLifeRules, load_db_shelf_life_rules


async def _create_rule(
    db_session: AsyncSession,
    *,
    name: str,
    storage_type: str,
    shelf_life_days: int,
    confidence: float,
) -> None:
    ingredient = CanonicalIngredient(name=name, category="test", aliases=[])
    db_session.add(ingredient)
    await db_session.flush()
    db_session.add(
        ShelfLifeRule(
            canonical_ingredient_id=ingredient.id,
            storage_type=storage_type,
            shelf_life_days=shelf_life_days,
            confidence=confidence,
        )
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_lookup_from_db_rules(db_session: AsyncSession) -> None:
    await _create_rule(
        db_session,
        name="spinach",
        storage_type="fridge",
        shelf_life_days=9,
        confidence=0.93,
    )

    service = DatabaseShelfLifeRules(await load_db_shelf_life_rules(db_session))

    assert service.get_shelf_life_days("spinach", "fridge") == (9, 0.93)


@pytest.mark.asyncio
async def test_fallback_to_default_when_no_db_rule(db_session: AsyncSession) -> None:
    service = DatabaseShelfLifeRules(await load_db_shelf_life_rules(db_session))

    assert service.get_shelf_life_days("dragon fruit", "fridge") == (7, 0.40)


@pytest.mark.asyncio
async def test_db_rules_override_defaults(db_session: AsyncSession) -> None:
    await _create_rule(
        db_session,
        name="milk",
        storage_type="fridge",
        shelf_life_days=12,
        confidence=0.99,
    )

    service = DatabaseShelfLifeRules(await load_db_shelf_life_rules(db_session))

    assert service.get_shelf_life_days("milk", "fridge") == (12, 0.99)


@pytest.mark.asyncio
async def test_load_db_rules_normalizes_keys(db_session: AsyncSession) -> None:
    await _create_rule(
        db_session,
        name="Yogurt",
        storage_type="Fridge",
        shelf_life_days=11,
        confidence=0.88,
    )

    loaded = await load_db_shelf_life_rules(db_session)

    assert loaded[("yogurt", "fridge")] == (11, 0.88)

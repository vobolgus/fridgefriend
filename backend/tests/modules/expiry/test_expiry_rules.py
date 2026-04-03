from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.modules.expiry.rules import DEFAULT_SHELF_LIFE, ShelfLifeRules
from app.modules.expiry.service import ExpiryService
from app.modules.expiry.urgency import UrgencyBucket, get_urgency_bucket


@pytest.fixture
def shelf_life_rules() -> ShelfLifeRules:
    return ShelfLifeRules()


@pytest.fixture
def expiry_service(shelf_life_rules: ShelfLifeRules) -> ExpiryService:
    return ExpiryService(shelf_life_rules)


def test_milk_fridge_shelf_life(shelf_life_rules: ShelfLifeRules) -> None:
    assert shelf_life_rules.get_shelf_life_days("milk", "fridge") == (7, 0.95)


def test_milk_freezer_shelf_life(shelf_life_rules: ShelfLifeRules) -> None:
    assert shelf_life_rules.get_shelf_life_days("milk", "freezer") == (90, 0.90)


def test_case_insensitive_lookup(shelf_life_rules: ShelfLifeRules) -> None:
    assert shelf_life_rules.get_shelf_life_days("MILK", "FRIDGE") == (7, 0.95)


def test_lookup_trims_input_whitespace(shelf_life_rules: ShelfLifeRules) -> None:
    assert shelf_life_rules.get_shelf_life_days("  milk  ", "  fridge  ") == (7, 0.95)


def test_unknown_ingredient_returns_default(shelf_life_rules: ShelfLifeRules) -> None:
    assert shelf_life_rules.get_shelf_life_days("quinoa", "pantry") == DEFAULT_SHELF_LIFE


def test_unknown_storage_for_known_ingredient_falls_back_to_name_match(
    shelf_life_rules: ShelfLifeRules,
) -> None:
    assert shelf_life_rules.get_shelf_life_days("milk", "cellar") == (7, 0.95)


def test_chicken_fridge_2_days(shelf_life_rules: ShelfLifeRules) -> None:
    assert shelf_life_rules.get_shelf_life_days("chicken", "fridge") == (2, 0.95)


def test_bread_freezer_lookup(shelf_life_rules: ShelfLifeRules) -> None:
    assert shelf_life_rules.get_shelf_life_days("bread", "freezer") == (90, 0.85)


def test_apples_pantry_lookup(shelf_life_rules: ShelfLifeRules) -> None:
    assert shelf_life_rules.get_shelf_life_days("apples", "pantry") == (7, 0.75)


def test_calculate_expiry_milk(expiry_service: ExpiryService) -> None:
    assert expiry_service.calculate_expiry("milk", "fridge", date(2026, 4, 3)) == (
        date(2026, 4, 10),
        0.95,
    )


def test_calculate_expiry_unknown_default(expiry_service: ExpiryService) -> None:
    expiry_date, confidence = expiry_service.calculate_expiry("quinoa", "pantry", date(2026, 4, 3))

    assert expiry_date == date(2026, 4, 10)
    assert confidence == 0.40


def test_calculate_expiry_pasta_long(expiry_service: ExpiryService) -> None:
    expiry_date, confidence = expiry_service.calculate_expiry("pasta", "pantry", date(2026, 4, 3))

    assert expiry_date == date(2028, 4, 2)
    assert confidence == 0.95


def test_calculate_expiry_uses_name_only_fallback(expiry_service: ExpiryService) -> None:
    expiry_date, confidence = expiry_service.calculate_expiry("beef", "garage", date(2026, 4, 3))

    assert expiry_date == date(2026, 4, 6)
    assert confidence == 0.95


def test_calculate_expiry_preserves_date_type(expiry_service: ExpiryService) -> None:
    expiry_date, _ = expiry_service.calculate_expiry("eggs", "fridge", date(2026, 4, 3))

    assert isinstance(expiry_date, date)


def test_expired_item() -> None:
    today = date(2026, 4, 3)

    assert get_urgency_bucket(today - timedelta(days=1), today) is UrgencyBucket.EXPIRED


def test_today_item() -> None:
    today = date(2026, 4, 3)

    assert get_urgency_bucket(today, today) is UrgencyBucket.TODAY


def test_tomorrow_item() -> None:
    today = date(2026, 4, 3)

    assert get_urgency_bucket(today + timedelta(days=1), today) is UrgencyBucket.TODAY


def test_this_week_item() -> None:
    today = date(2026, 4, 3)

    assert get_urgency_bucket(today + timedelta(days=5), today) is UrgencyBucket.THIS_WEEK


def test_boundary_day_7() -> None:
    today = date(2026, 4, 3)

    assert get_urgency_bucket(today + timedelta(days=7), today) is UrgencyBucket.THIS_WEEK


def test_boundary_day_8() -> None:
    today = date(2026, 4, 3)

    assert get_urgency_bucket(today + timedelta(days=8), today) is UrgencyBucket.SAFE_LATER


def test_safe_later_item() -> None:
    today = date(2026, 4, 3)

    assert get_urgency_bucket(today + timedelta(days=30), today) is UrgencyBucket.SAFE_LATER


def test_urgency_bucket_values_are_api_friendly_strings() -> None:
    assert UrgencyBucket.TODAY.value == "today"
    assert UrgencyBucket.THIS_WEEK.value == "this_week"
    assert UrgencyBucket.SAFE_LATER.value == "safe_later"
    assert UrgencyBucket.EXPIRED.value == "expired"

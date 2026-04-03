from __future__ import annotations

from datetime import date, timedelta

from app.modules.expiry.rules import ShelfLifeRules


class ExpiryService:
    def __init__(self, shelf_life_rules: ShelfLifeRules | None = None) -> None:
        self._shelf_life_rules: ShelfLifeRules = shelf_life_rules or ShelfLifeRules()

    def calculate_expiry(self, name: str, storage: str, date_added: date) -> tuple[date, float]:
        shelf_life_days, confidence = self._shelf_life_rules.get_shelf_life_days(name, storage)
        expiry_date = date_added + timedelta(days=shelf_life_days)
        return expiry_date, confidence

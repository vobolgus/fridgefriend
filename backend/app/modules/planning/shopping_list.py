from __future__ import annotations

from typing import TypedDict

from app.core.units import convert_to_base
from app.models.inventory_item import InventoryItem, InventoryStatus

from .schemas import PlanResult, ShoppingItem


class _IngredientRequirement(TypedDict):
    base_quantity: float
    base_unit: str
    display_unit: str


def derive_shopping_list(
    plan: PlanResult,
    inventory: list[InventoryItem],
    reserved_quantities: dict[str, float] | None = None,
) -> list[ShoppingItem]:
    available_base: dict[str, tuple[float, str]] = {}
    total_base: dict[str, tuple[float, str]] = {}
    for item in inventory:
        if item.status in {InventoryStatus.USED, InventoryStatus.DISCARDED}:
            continue
        key = item.canonical_name.strip().lower()
        item_base_qty, item_base_unit = convert_to_base(item.quantity, item.unit)
        prev_avail, _ = available_base.get(key, (0.0, item_base_unit))
        available_base[key] = (prev_avail + item_base_qty, item_base_unit)
        prev_total, _ = total_base.get(key, (0.0, item_base_unit))
        total_base[key] = (prev_total + item_base_qty, item_base_unit)

    for ingredient_name, reserved_quantity in (reserved_quantities or {}).items():
        key = ingredient_name.strip().lower()
        if key not in available_base:
            continue
        avail_qty, avail_unit = available_base[key]
        reserved_base, _ = convert_to_base(reserved_quantity, avail_unit)
        available_base[key] = (max(0.0, avail_qty - reserved_base), avail_unit)

    required_by_ingredient: dict[str, _IngredientRequirement] = {}
    for day in plan.days:
        for ingredient in day.recipe_ingredients:
            key = ingredient.ingredient_name.strip().lower()
            req_base_qty, req_base_unit = convert_to_base(ingredient.quantity, ingredient.unit)
            if key not in required_by_ingredient:
                required_by_ingredient[key] = {
                    "base_quantity": 0.0,
                    "base_unit": req_base_unit,
                    "display_unit": ingredient.unit,
                }
            required_by_ingredient[key]["base_quantity"] += req_base_qty

    items: list[ShoppingItem] = []
    for ingredient_name, requirement in sorted(required_by_ingredient.items()):
        required_base_qty = requirement["base_quantity"]
        avail_qty, _ = available_base.get(ingredient_name, (0.0, ""))
        if avail_qty >= required_base_qty:
            continue

        gap_base = required_base_qty - avail_qty
        display_unit = requirement["display_unit"]
        one_unit_in_base, _ = convert_to_base(1.0, display_unit)
        gap_display = gap_base / one_unit_in_base if one_unit_in_base > 0 else gap_base

        items.append(
            ShoppingItem.model_validate(
                {
                    "ingredientName": ingredient_name,
                    "quantity": round(gap_display, 3),
                    "unit": display_unit,
                    "reason": (
                        "not in inventory"
                        if total_base.get(ingredient_name, (0.0, ""))[0] == 0
                        else "insufficient quantity"
                    ),
                },
            ),
        )

    return items

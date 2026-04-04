from __future__ import annotations

from app.models.inventory_item import InventoryItem, InventoryStatus

from .schemas import PlanResult, ShoppingItem


def derive_shopping_list(
    plan: PlanResult,
    inventory: list[InventoryItem],
    reserved_quantities: dict[str, float] | None = None,
) -> list[ShoppingItem]:
    available_inventory: dict[str, float] = {}
    total_inventory: dict[str, float] = {}
    for item in inventory:
        if item.status != InventoryStatus.ACTIVE:
            continue
        key = item.canonical_name.strip().lower()
        available_inventory[key] = available_inventory.get(key, 0.0) + item.quantity
        total_inventory[key] = total_inventory.get(key, 0.0) + item.quantity

    for ingredient_name, reserved_quantity in (reserved_quantities or {}).items():
        key = ingredient_name.strip().lower()
        if key not in available_inventory:
            continue
        available_inventory[key] = max(0.0, available_inventory[key] - reserved_quantity)

    required_by_ingredient: dict[str, dict[str, float | str]] = {}
    for day in plan.days:
        for ingredient in day.recipe_ingredients:
            key = ingredient.ingredient_name.strip().lower()
            if key not in required_by_ingredient:
                required_by_ingredient[key] = {"quantity": 0.0, "unit": ingredient.unit}
            required_by_ingredient[key]["quantity"] = float(required_by_ingredient[key]["quantity"]) + ingredient.quantity

    items: list[ShoppingItem] = []
    for ingredient_name, requirement in sorted(required_by_ingredient.items()):
        required_quantity = float(requirement["quantity"])
        available_quantity = available_inventory.get(ingredient_name, 0.0)
        if available_quantity >= required_quantity:
            continue

        items.append(
            ShoppingItem(
                ingredient_name=ingredient_name,
                quantity=required_quantity - available_quantity,
                unit=str(requirement["unit"]),
                reason=(
                    "not in inventory"
                    if total_inventory.get(ingredient_name, 0.0) == 0
                    else "insufficient quantity"
                ),
            ),
        )

    return items

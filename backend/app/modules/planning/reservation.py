from __future__ import annotations

import uuid
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.units import convert_to_base
from app.models.inventory_item import InventoryItem, InventoryStatus
from app.models.meal_plan import MealPlan
from app.models.reserved_ingredient import ReservedIngredient

from .schemas import PlanResult


class InsufficientReservationQuantityError(Exception):
    pass


class ReservationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    async def reserve_plan(
        self,
        meal_plan: MealPlan,
        plan_result: PlanResult,
        inventory_items: list[InventoryItem],
    ) -> None:
        externally_reserved_by_item = await self._reserved_quantities_by_item(exclude_plan_id=meal_plan.id)
        reserved_by_item = dict(externally_reserved_by_item)
        inventory_by_name: dict[str, list[InventoryItem]] = {}
        for item in sorted(inventory_items, key=lambda current: current.estimated_expiry_date):
            if item.status != InventoryStatus.ACTIVE:
                continue
            inventory_by_name.setdefault(item.canonical_name.strip().lower(), []).append(item)

        day_by_key = {(day.date, str(day.recipe_id)): day for day in meal_plan.days}

        for planned_day in plan_result.days:
            meal_plan_day = day_by_key[(planned_day.date, planned_day.recipe_id)]
            for ingredient in planned_day.recipe_ingredients:
                ingredient_name = ingredient.ingredient_name.strip().lower()
                candidates = inventory_by_name.get(ingredient_name, [])
                if not candidates:
                    continue

                allocations = self._allocate_quantity(
                    candidates, ingredient.quantity, ingredient.unit, reserved_by_item,
                )
                allocated_quantity = sum(quantity for _, quantity in allocations)
                required_base_quantity, required_base_unit = convert_to_base(ingredient.quantity, ingredient.unit)
                has_existing_reservations = any(
                    externally_reserved_by_item.get(item.id, 0.0) > 0 for item in candidates
                )
                if has_existing_reservations and allocated_quantity + 1e-9 < required_base_quantity:
                    raise InsufficientReservationQuantityError(
                        f"Insufficient free quantity for {ingredient_name}",
                    )

                for inventory_item, quantity in allocations:
                    self._session.add(
                        ReservedIngredient(
                            meal_plan_id=meal_plan.id,
                            meal_plan_day_id=meal_plan_day.id,
                            inventory_item_id=inventory_item.id,
                            quantity_reserved=quantity,
                            unit=required_base_unit,
                        )
                    )
                    reserved_by_item[inventory_item.id] = reserved_by_item.get(inventory_item.id, 0.0) + quantity

        await self._session.flush()

    async def reserved_quantities_by_ingredient(
        self,
        *,
        household_id: uuid.UUID,
        exclude_plan_id: uuid.UUID | None = None,
    ) -> dict[str, float]:
        statement = select(ReservedIngredient, InventoryItem).join(
            InventoryItem,
            InventoryItem.id == ReservedIngredient.inventory_item_id,
        )
        if exclude_plan_id is not None:
            statement = statement.where(ReservedIngredient.meal_plan_id != exclude_plan_id)
        statement = statement.where(InventoryItem.household_id == household_id)
        rows = (await self._session.execute(statement)).all()
        reserved: dict[str, float] = {}
        for reserved_ingredient, inventory_item in cast(list[tuple[ReservedIngredient, InventoryItem]], rows):
            key = inventory_item.canonical_name.strip().lower()
            reserved[key] = reserved.get(key, 0.0) + reserved_ingredient.quantity_reserved
        return reserved

    async def _reserved_quantities_by_item(
        self,
        *,
        exclude_plan_id: uuid.UUID | None = None,
    ) -> dict[uuid.UUID, float]:
        statement = select(ReservedIngredient)
        if exclude_plan_id is not None:
            statement = statement.where(ReservedIngredient.meal_plan_id != exclude_plan_id)
        rows = (await self._session.execute(statement)).scalars().all()
        reserved: dict[uuid.UUID, float] = {}
        for row in rows:
            reserved[row.inventory_item_id] = reserved.get(row.inventory_item_id, 0.0) + row.quantity_reserved
        return reserved

    @staticmethod
    def _allocate_quantity(
        candidates: list[InventoryItem],
        required_quantity: float,
        required_unit: str,
        reserved_by_item: dict[uuid.UUID, float],
    ) -> list[tuple[InventoryItem, float]]:
        required_base, required_base_unit = convert_to_base(required_quantity, required_unit)
        remaining_required = required_base
        allocations: list[tuple[InventoryItem, float]] = []
        for item in candidates:
            item_base, item_base_unit = convert_to_base(item.quantity, item.unit)
            if item_base_unit != required_base_unit:
                continue
            already_reserved_base = reserved_by_item.get(item.id, 0.0)
            free_base = max(0.0, item_base - already_reserved_base)
            if free_base <= 0:
                continue
            allocation_base = min(free_base, remaining_required)
            if allocation_base <= 0:
                continue
            allocations.append((item, allocation_base))
            remaining_required -= allocation_base
            if remaining_required <= 1e-9:
                break
        return allocations

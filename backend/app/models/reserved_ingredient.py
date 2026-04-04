# pyright: reportUnannotatedClassAttribute=false, reportExplicitAny=false

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Float, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class ReservedIngredient(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "reserved_ingredients"

    meal_plan_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("meal_plans.id"), index=True)
    meal_plan_day_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("meal_plan_days.id"),
        index=True,
    )
    inventory_item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("inventory_items.id"),
        index=True,
    )
    quantity_reserved: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(50))

    meal_plan: Mapped[Any] = relationship("MealPlan", back_populates="reserved_ingredients")
    meal_plan_day: Mapped[Any] = relationship("MealPlanDay")
    inventory_item: Mapped[Any] = relationship("InventoryItem")

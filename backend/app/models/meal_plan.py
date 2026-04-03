# pyright: reportUnannotatedClassAttribute=false, reportExplicitAny=false

from __future__ import annotations

from datetime import date
import uuid
from typing import Any

from sqlalchemy import Date, ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MealPlan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "meal_plans"

    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)

    days: Mapped[list["MealPlanDay"]] = relationship(
        back_populates="meal_plan",
        cascade="all, delete-orphan",
        order_by="MealPlanDay.date",
        lazy="selectin",
    )


class MealPlanDay(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "meal_plan_days"

    meal_plan_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("meal_plans.id"), index=True)
    recipe_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("recipes.id"), index=True)
    date: Mapped[date] = mapped_column(Date)
    servings: Mapped[int] = mapped_column(Integer)

    meal_plan: Mapped[MealPlan] = relationship(back_populates="days")
    recipe: Mapped[Any] = relationship("Recipe", back_populates="meal_plan_days")

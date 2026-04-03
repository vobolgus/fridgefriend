# pyright: reportUnannotatedClassAttribute=false, reportExplicitAny=false

from __future__ import annotations

from typing import Any

from sqlalchemy import Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Recipe(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recipes"

    title: Mapped[str] = mapped_column(String(255))
    prep_minutes: Mapped[int] = mapped_column(Integer)
    dietary_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    ingredients: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)

    meal_plan_days: Mapped[list[Any]] = relationship(
        "MealPlanDay",
        back_populates="recipe",
    )

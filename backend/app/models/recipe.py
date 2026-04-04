# pyright: reportUnannotatedClassAttribute=false, reportExplicitAny=false

from __future__ import annotations

from typing import Any

from sqlalchemy import Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Recipe(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recipes"

    title: Mapped[str] = mapped_column(String(255))
    prep_minutes: Mapped[int] = mapped_column(Integer)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    instructions: Mapped[list[dict[str, object]] | None] = mapped_column(JSON, nullable=True)
    cuisines: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    servings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    nutrition: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    dietary_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    ingredients: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)

    meal_plan_days: Mapped[list[Any]] = relationship(
        "MealPlanDay",
        back_populates="recipe",
    )
    recipe_ingredients: Mapped[list[Any]] = relationship(
        "RecipeIngredient",
        back_populates="recipe",
        cascade="all, delete-orphan",
    )

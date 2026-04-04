# pyright: reportUnannotatedClassAttribute=false, reportExplicitAny=false

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Float, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RecipeIngredient(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recipe_ingredients"

    recipe_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("recipes.id"), index=True)
    canonical_ingredient_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("canonical_ingredients.id"),
        index=True,
        nullable=True,
    )
    ingredient_name: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(50))

    recipe: Mapped[Any] = relationship("Recipe", back_populates="recipe_ingredients")
    canonical_ingredient: Mapped[Any] = relationship("CanonicalIngredient")

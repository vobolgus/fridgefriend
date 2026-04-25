# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnannotatedClassAttribute=false, reportAny=false

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.household import Household
    from app.models.recipe import Recipe
    from app.models.user import User


class ShoppingListItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "shopping_list_items"

    household_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    recipe_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("recipes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_purchased: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)

    household: Mapped[Household] = relationship("Household")
    recipe: Mapped[Recipe | None] = relationship("Recipe")
    created_by_user: Mapped[User | None] = relationship("User")

    __table_args__ = (
        UniqueConstraint(
            "household_id",
            "idempotency_key",
            name="uq_shopping_list_items_household_idempotency",
        ),
    )

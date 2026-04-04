# pyright: reportUnannotatedClassAttribute=false, reportExplicitAny=false

from __future__ import annotations

from datetime import date
from enum import StrEnum
import uuid
from typing import Any

from sqlalchemy import Date, Enum, Float, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class InventoryStatus(StrEnum):
    ACTIVE = "active"
    USED = "used"
    DISCARDED = "discarded"
    FROZEN = "frozen"


class InventorySource(StrEnum):
    MANUAL = "manual"
    BARCODE = "barcode"
    PHOTO = "photo"


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [item.value for item in enum_cls]


class InventoryItem(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "inventory_items"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    household_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("households.id"),
        index=True,
        nullable=True,
    )
    canonical_ingredient_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("canonical_ingredients.id"),
        nullable=True,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(50))
    storage_location: Mapped[str] = mapped_column(String(100))
    estimated_expiry_date: Mapped[date] = mapped_column(Date)
    confidence: Mapped[float] = mapped_column(Float)
    status: Mapped[InventoryStatus] = mapped_column(
        Enum(InventoryStatus, values_callable=enum_values),
        default=InventoryStatus.ACTIVE,
    )
    source: Mapped[InventorySource] = mapped_column(
        Enum(InventorySource, values_callable=enum_values),
    )
    canonical_name: Mapped[str] = mapped_column(String(255))

    user: Mapped[Any] = relationship("User", back_populates="inventory_items")
    household: Mapped[Any] = relationship("Household", back_populates="inventory_items")

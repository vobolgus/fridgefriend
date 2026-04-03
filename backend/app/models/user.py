# pyright: reportUnannotatedClassAttribute=false, reportExplicitAny=false

from __future__ import annotations

from typing import Any

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)

    inventory_items: Mapped[list[Any]] = relationship(
        "InventoryItem",
        back_populates="user",
    )

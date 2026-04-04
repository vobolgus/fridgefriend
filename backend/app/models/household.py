# pyright: reportUnannotatedClassAttribute=false, reportExplicitAny=false

from __future__ import annotations

from enum import StrEnum
import uuid
from typing import Any

from sqlalchemy import Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [item.value for item in enum_cls]


class HouseholdRole(StrEnum):
    OWNER = "owner"
    MEMBER = "member"


class Household(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "households"

    name: Mapped[str] = mapped_column(String(255))
    invite_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)

    members: Mapped[list["HouseholdMember"]] = relationship(
        back_populates="household",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    inventory_items: Mapped[list[Any]] = relationship(
        "InventoryItem",
        back_populates="household",
        lazy="selectin",
    )


class HouseholdMember(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "household_members"

    household_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("households.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    role: Mapped[HouseholdRole] = mapped_column(
        Enum(HouseholdRole, values_callable=enum_values),
        default=HouseholdRole.MEMBER,
    )

    household: Mapped[Household] = relationship(back_populates="members")
    user: Mapped[Any] = relationship("User", back_populates="household_memberships")

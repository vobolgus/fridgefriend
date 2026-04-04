# pyright: reportUnannotatedClassAttribute=false, reportExplicitAny=false

from __future__ import annotations

from datetime import UTC, datetime
import uuid
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class InventoryEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "inventory_events"

    household_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("households.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    item_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("inventory_items.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(50))
    previous_state: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    new_state: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class AnalyticsEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "analytics_events"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(100))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )


class RecommendationSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recommendation_sessions"

    household_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("households.id"), index=True)
    request_params: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    recipes_shown: Mapped[list[Any]] = mapped_column(JSON, default=list)
    recipe_selected_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

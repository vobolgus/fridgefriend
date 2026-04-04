from __future__ import annotations

from datetime import UTC, datetime
import uuid

from sqlalchemy import DateTime, Float, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class AiInferenceLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ai_inference_log"

    provider: Mapped[str] = mapped_column(String(50), index=True)
    # 'litellm', 'spoonacular', 'firebase_auth'
    operation: Mapped[str] = mapped_column(String(100))
    # 'photo_parse', 'recipe_search', 'token_verify'
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 'gpt-4.1-mini' for LLM calls
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True, index=True
    )
    household_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True
    )

    # Performance
    duration_ms: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20))
    # 'success', 'error', 'timeout'

    # Cost (LLM-specific)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Cost (API-specific)
    api_points_used: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    # Context
    request_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True
    )
    error_detail: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    # Result quality
    items_returned: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    avg_confidence: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )

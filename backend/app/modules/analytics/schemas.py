from __future__ import annotations

from datetime import datetime
import uuid
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field


class AnalyticsEventCreate(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(str_strip_whitespace=True)

    event_type: str = Field(min_length=1, max_length=100)
    payload: dict[str, Any] = Field(default_factory=dict)


class AnalyticsEventAccepted(BaseModel):
    accepted: bool = True
    event_id: uuid.UUID
    created_at: datetime

from __future__ import annotations

from datetime import datetime, time
import uuid
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field


class NotificationPreferenceUpdate(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(str_strip_whitespace=True)

    expiry_reminder_enabled: bool | None = None
    reminder_days_before: int | None = Field(default=None, ge=0, le=30)
    quiet_hours_start: time | None = None
    quiet_hours_end: time | None = None


class NotificationPreferenceResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    expiry_reminder_enabled: bool
    reminder_days_before: int
    quiet_hours_start: time | None
    quiet_hours_end: time | None
    created_at: datetime
    updated_at: datetime


class DeviceTokenCreate(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(str_strip_whitespace=True)

    token: str = Field(min_length=1, max_length=500)
    platform: str = Field(min_length=1, max_length=20)


class DeviceTokenResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    token: str
    platform: str
    created_at: datetime
    updated_at: datetime


class ExpiryReminderCandidate(BaseModel):
    user_id: uuid.UUID
    device_tokens: list[str] = Field(default_factory=list)
    item_names: list[str] = Field(default_factory=list)
    reminder_days_before: int


class PushReceipt(BaseModel):
    token: str
    success: bool


class PushSummary(BaseModel):
    user_id: uuid.UUID
    receipts: list[PushReceipt] = Field(default_factory=list)


class ReminderRunResult(BaseModel):
    notifications_sent: int
    users_notified: int


class NotificationAcceptedResponse(BaseModel):
    accepted: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

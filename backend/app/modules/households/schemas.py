from __future__ import annotations

from datetime import datetime
import uuid
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field

from app.models.household import HouseholdRole


class HouseholdCreate(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)


class HouseholdUpdate(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=255)


class JoinRequest(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(str_strip_whitespace=True)

    invite_code: str = Field(min_length=1, max_length=20)


class HouseholdMemberResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    role: HouseholdRole


class HouseholdResponse(BaseModel):
    id: uuid.UUID
    name: str
    invite_code: str
    members: list[HouseholdMemberResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

from __future__ import annotations

from datetime import date, datetime
import uuid
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.inventory_item import InventorySource, InventoryStatus


class ItemCreate(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(str_strip_whitespace=True)

    display_name: str = Field(min_length=1)
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1)
    storage_location: str = Field(min_length=1)
    source: InventorySource = InventorySource.MANUAL
    canonical_name: str | None = None
    estimated_expiry_date: date | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @field_validator("canonical_name")
    @classmethod
    def normalize_optional_canonical_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value or None


class ItemUpdate(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(str_strip_whitespace=True)

    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, min_length=1)
    storage_location: str | None = Field(default=None, min_length=1)
    estimated_expiry_date: date | None = None


class ItemStatusUpdate(BaseModel):
    status: InventoryStatus


class ItemResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    display_name: str
    quantity: float
    unit: str
    storage_location: str
    estimated_expiry_date: date
    confidence: float
    status: InventoryStatus
    source: InventorySource
    canonical_name: str
    created_at: datetime
    updated_at: datetime

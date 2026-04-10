from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field


class BarcodeResult(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    barcode: str
    display_name: str = Field(alias="displayName")
    canonical_name: str = Field(alias="canonicalName")
    brand: str
    unit: str = "unit"


class BarcodeScanRequest(BaseModel):
    barcode: str
    quantity: float
    unit: str = "unit"
    storage_location: str
    household_id: str | None = None


class BarcodeScanResponse(BarcodeResult):
    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    canonical_ingredient_id: str | None = Field(default=None, alias="canonicalIngredientId")
    quantity: float
    storage_location: str = Field(alias="storageLocation")
    confidence: float = 0.0
    source: str = "barcode"


class DraftItem(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    display_name: str = Field(alias="displayName")
    quantity: float
    unit: str
    confidence: float
    canonical_name: str | None = Field(default=None, alias="canonicalName")


class PhotoScanRequest(BaseModel):
    image_url: str
    household_id: str | None = None


class PhotoScanResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    draft_items: list[DraftItem] = Field(alias="draftItems")
    source: str = "photo"

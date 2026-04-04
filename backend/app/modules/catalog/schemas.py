from pydantic import BaseModel


class BarcodeResult(BaseModel):
    barcode: str
    display_name: str
    canonical_name: str
    brand: str
    unit: str = "unit"


class BarcodeScanRequest(BaseModel):
    barcode: str
    quantity: float
    unit: str = "unit"
    storage_location: str
    household_id: str | None = None


class BarcodeScanResponse(BarcodeResult):
    canonical_ingredient_id: str | None = None
    quantity: float
    storage_location: str
    source: str = "barcode"


class DraftItem(BaseModel):
    display_name: str
    quantity: float
    unit: str
    confidence: float
    canonical_name: str | None = None


class PhotoScanRequest(BaseModel):
    image_url: str
    household_id: str | None = None


class PhotoScanResponse(BaseModel):
    draft_items: list[DraftItem]
    source: str = "photo"

from pydantic import BaseModel


class BarcodeResult(BaseModel):
    barcode: str
    display_name: str
    canonical_name: str
    brand: str


class BarcodeScanRequest(BaseModel):
    barcode: str
    quantity: float
    storage_location: str
    household_id: str | None = None


class BarcodeScanResponse(BarcodeResult):
    quantity: float
    storage_location: str
    source: str = "barcode"

from .interfaces import BarcodeAPIInterface
from .mock_barcode_api import MockBarcodeAPI
from .normalizer import normalize_ingredient_name
from .schemas import BarcodeResult


class CatalogService:
    def __init__(self, barcode_api: BarcodeAPIInterface | None = None) -> None:
        self.barcode_api: BarcodeAPIInterface = barcode_api or MockBarcodeAPI()

    def lookup_barcode(self, barcode: str) -> BarcodeResult | None:
        return self.barcode_api.lookup(barcode)

    def normalize(self, name: str) -> str:
        return normalize_ingredient_name(name)

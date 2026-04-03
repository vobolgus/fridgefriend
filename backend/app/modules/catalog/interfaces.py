from typing import Protocol

from .schemas import BarcodeResult


class BarcodeAPIInterface(Protocol):
    def lookup(self, barcode: str) -> BarcodeResult | None:
        ...

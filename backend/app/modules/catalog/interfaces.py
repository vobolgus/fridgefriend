from typing import Protocol

from .schemas import BarcodeResult


class BarcodeAPIInterface(Protocol):
    async def lookup(self, barcode: str) -> BarcodeResult | None:
        ...

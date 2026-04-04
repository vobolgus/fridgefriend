from .schemas import BarcodeResult


MOCK_BARCODES = {
    "5000112637939": BarcodeResult(
        barcode="5000112637939",
        display_name="Heinz Tomato Ketchup 500g",
        canonical_name="ketchup",
        brand="Heinz",
    ),
    "0070038640047": BarcodeResult(
        barcode="0070038640047",
        display_name="Cheerios Cereal 450g",
        canonical_name="cereal",
        brand="General Mills",
    ),
    "049000028911": BarcodeResult(
        barcode="049000028911",
        display_name="Coca-Cola 330ml",
        canonical_name="soft drink",
        brand="Coca-Cola",
    ),
    "5449000000996": BarcodeResult(
        barcode="5449000000996",
        display_name="Coca-Cola 1.5L",
        canonical_name="soft drink",
        brand="Coca-Cola",
    ),
    "4006381333931": BarcodeResult(
        barcode="4006381333931",
        display_name="Milka Chocolate 100g",
        canonical_name="chocolate",
        brand="Milka",
    ),
    "8710847909610": BarcodeResult(
        barcode="8710847909610",
        display_name="Whole Milk 1L",
        canonical_name="milk",
        brand="Generic",
        unit="l",
    ),
    "5010029013018": BarcodeResult(
        barcode="5010029013018",
        display_name="Free Range Eggs 6pk",
        canonical_name="eggs",
        brand="Generic",
    ),
    "5000168201975": BarcodeResult(
        barcode="5000168201975",
        display_name="White Bread 800g",
        canonical_name="bread",
        brand="Warburtons",
    ),
    "0011110859624": BarcodeResult(
        barcode="0011110859624",
        display_name="Chicken Breast 500g",
        canonical_name="chicken",
        brand="Generic",
    ),
}


class MockBarcodeAPI:
    async def lookup(self, barcode: str) -> BarcodeResult | None:
        return MOCK_BARCODES.get(barcode)

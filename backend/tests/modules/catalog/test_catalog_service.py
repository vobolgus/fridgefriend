import httpx
import pytest

from app.modules.catalog.interfaces import BarcodeAPIInterface
from app.modules.catalog.schemas import BarcodeResult
from app.modules.catalog.service import CatalogService
from app.modules.catalog.normalizer import normalize_ingredient_name


class CustomBarcodeAPI(BarcodeAPIInterface):
    def lookup(self, barcode: str) -> BarcodeResult | None:
        if barcode == "custom-1":
            return BarcodeResult(
                barcode=barcode,
                display_name="Tesco Ketchup 500g",
                canonical_name="ketchup",
                brand="Tesco",
            )
        return None


def test_lookup_known_barcode() -> None:
    service = CatalogService()

    result = service.lookup_barcode("8710847909610")

    assert result is not None
    assert result.canonical_name == "milk"
    assert result.brand == "Generic"


def test_lookup_unknown_barcode() -> None:
    service = CatalogService()

    result = service.lookup_barcode("9999999999999")

    assert result is None


def test_lookup_known_barcode_returns_expected_payload() -> None:
    service = CatalogService()

    result = service.lookup_barcode("5000112637939")

    assert result == BarcodeResult(
        barcode="5000112637939",
        display_name="Heinz Tomato Ketchup 500g",
        canonical_name="ketchup",
        brand="Heinz",
    )


@pytest.mark.asyncio
async def test_barcode_api_endpoint_found(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/v1/scan/barcode",
        json={
            "barcode": "8710847909610",
            "quantity": 1,
            "storage_location": "fridge",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "barcode": "8710847909610",
        "display_name": "Whole Milk 1L",
        "canonical_name": "milk",
        "brand": "Generic",
        "quantity": 1.0,
        "storage_location": "fridge",
        "source": "barcode",
    }


@pytest.mark.asyncio
async def test_barcode_api_endpoint_not_found(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/v1/scan/barcode",
        json={
            "barcode": "9999999999999",
            "quantity": 1,
            "storage_location": "pantry",
        },
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_barcode_api_endpoint_missing_field(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/v1/scan/barcode",
        json={"quantity": 1, "storage_location": "fridge"},
    )

    assert response.status_code == 422


def test_normalize_basic() -> None:
    assert normalize_ingredient_name("Milk") == "milk"


def test_normalize_strip_whitespace() -> None:
    assert normalize_ingredient_name("  eggs  ") == "eggs"


def test_normalize_strip_quantity_parens() -> None:
    assert normalize_ingredient_name("Milk (1L)") == "milk"


def test_normalize_strip_common_suffixes() -> None:
    assert normalize_ingredient_name("White Bread 800g") == "white bread"
    assert normalize_ingredient_name("Whole Milk 1L") == "whole milk"
    assert normalize_ingredient_name("Free Range Eggs 6pk") == "free range eggs"


def test_normalize_different_brands_same_canonical() -> None:
    assert normalize_ingredient_name("Heinz Ketchup 500g") == "ketchup"
    assert normalize_ingredient_name("Tesco Ketchup 500g") == "ketchup"


def test_normalize_maps_common_variants() -> None:
    assert normalize_ingredient_name("tomato") == "tomatoes"
    assert normalize_ingredient_name("Tomatoes") == "tomatoes"


def test_catalog_service_uses_interface() -> None:
    service = CatalogService(barcode_api=CustomBarcodeAPI())

    result = service.lookup_barcode("custom-1")

    assert result is not None
    assert result.brand == "Tesco"
    assert service.normalize(result.display_name) == "ketchup"

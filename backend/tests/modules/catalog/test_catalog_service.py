from collections.abc import Callable
from importlib import import_module
from types import ModuleType
from typing import Protocol, cast

import httpx
import pytest


def _headers(key: str) -> dict[str, str]:
    return {"Authorization": "Bearer test-token", "Idempotency-Key": key}


class BarcodeResultLike(Protocol):
    barcode: str
    display_name: str
    canonical_name: str
    brand: str


class BarcodeResultFactory(Protocol):
    def __call__(
        self,
        *,
        barcode: str,
        display_name: str,
        canonical_name: str,
        brand: str,
    ) -> BarcodeResultLike: ...


class CatalogServiceLike(Protocol):
    def lookup_barcode(self, barcode: str) -> BarcodeResultLike | None: ...

    def normalize(self, name: str) -> str: ...


class CatalogServiceFactory(Protocol):
    def __call__(self, barcode_api: object | None = None) -> CatalogServiceLike: ...


def _load_symbol(module_name: str, symbol_name: str) -> object:
    module: ModuleType = import_module(module_name)
    return cast(object, getattr(module, symbol_name))


normalize_ingredient_name = cast(
    Callable[[str], str],
    _load_symbol("app.modules.catalog.normalizer", "normalize_ingredient_name"),
)
BarcodeResult = cast(
    BarcodeResultFactory,
    _load_symbol("app.modules.catalog.schemas", "BarcodeResult"),
)
CatalogService = cast(
    CatalogServiceFactory,
    _load_symbol("app.modules.catalog.service", "CatalogService"),
)


class CustomBarcodeAPI:
    def lookup(self, barcode: str) -> BarcodeResultLike | None:
        if barcode == "custom-1":
            return BarcodeResult(
                barcode=barcode,
                display_name="Tesco Ketchup 500g",
                canonical_name="ketchup",
                brand="Tesco",
            )
        return None


@pytest.fixture
def service() -> CatalogServiceLike:
    return CatalogService()


def test_lookup_known_barcode(service: CatalogServiceLike) -> None:
    result = service.lookup_barcode("8710847909610")

    assert result is not None
    assert result.canonical_name == "milk"
    assert result.brand == "Generic"


def test_lookup_unknown_barcode(service: CatalogServiceLike) -> None:
    result = service.lookup_barcode("9999999999999")

    assert result is None


def test_lookup_known_barcode_returns_expected_payload(service: CatalogServiceLike) -> None:
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
        headers=_headers("barcode-found-1"),
        json={
            "barcode": "8710847909610",
            "quantity": 1,
            "storage_location": "fridge",
        },
    )

    assert response.status_code == 200
    payload = cast(dict[str, object], response.json())
    assert payload["barcode"] == "8710847909610"
    assert payload["display_name"] == "Whole Milk 1L"
    assert payload["canonical_name"] == "milk"
    assert payload["brand"] == "Generic"
    assert payload["quantity"] == 1.0
    assert payload["storage_location"] == "fridge"
    assert payload["confidence"] == 1.0
    assert payload["source"] == "barcode"
    assert payload["canonical_ingredient_id"] is not None


@pytest.mark.asyncio
async def test_barcode_api_endpoint_requires_auth(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/v1/scan/barcode",
        json={
            "barcode": "8710847909610",
            "quantity": 1,
            "storage_location": "fridge",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_barcode_api_endpoint_not_found_returns_editable_draft(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/v1/scan/barcode",
        headers=_headers("barcode-not-found-1"),
        json={
            "barcode": "9999999999999",
            "quantity": 1,
            "storage_location": "pantry",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "barcode": "9999999999999",
        "display_name": "",
        "canonical_name": "",
        "brand": "",
        "canonical_ingredient_id": None,
        "quantity": 1.0,
        "storage_location": "pantry",
        "confidence": 0.0,
        "source": "barcode",
    }


@pytest.mark.asyncio
async def test_barcode_api_endpoint_missing_field(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/v1/scan/barcode",
        headers=_headers("barcode-missing-field-1"),
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

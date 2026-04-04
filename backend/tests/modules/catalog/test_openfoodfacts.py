from __future__ import annotations

from collections.abc import Mapping
import httpx
import pytest

from app.modules.catalog.openfoodfacts import OpenFoodFactsAPI
from app.modules.catalog.schemas import BarcodeResult


class _Response:
    def __init__(self, payload: dict[str, object], *, status_code: int = 200) -> None:
        self._payload: dict[str, object] = payload
        self.status_code: int = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "https://world.openfoodfacts.org/api/v2/product/test.json")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("openfoodfacts error", request=request, response=response)

    def json(self) -> dict[str, object]:
        return self._payload


class _Client:
    def __init__(self, response: _Response) -> None:
        self._response: _Response = response
        self.last_headers: Mapping[str, str] | None = None

    async def get(
        self,
        url: str,
        *,
        params: Mapping[str, str],
        headers: Mapping[str, str],
    ) -> _Response:
        assert url.endswith("/3017620422003.json")
        assert params == {"fields": OpenFoodFactsAPI.FIELDS}
        self.last_headers = headers
        return self._response


def _build_client(payload: dict[str, object], *, status_code: int = 200) -> OpenFoodFactsAPI:
    client = _Client(_Response(payload, status_code=status_code))
    return OpenFoodFactsAPI(client=client)


@pytest.mark.asyncio
async def test_lookup_found_maps_correctly() -> None:
    api = _build_client(
        {
            "status": 1,
            "product": {
                "product_name": "Nutella",
                "brands": "Ferrero",
                "quantity": "750g",
                "categories_tags": [],
                "nutriments": {},
            },
        }
    )

    result = await api.lookup("3017620422003")

    assert result == BarcodeResult(
        barcode="3017620422003",
        display_name="Nutella 750g",
        canonical_name="nutella",
        brand="Ferrero",
        unit="g",
    )


@pytest.mark.asyncio
async def test_lookup_not_found_status_0() -> None:
    api = _build_client({"status": 0})

    result = await api.lookup("3017620422003")

    assert result is None


@pytest.mark.asyncio
async def test_lookup_not_found_404() -> None:
    api = _build_client({}, status_code=404)

    result = await api.lookup("3017620422003")

    assert result is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("quantity", "unit"),
    [("500g", "g"), ("1.5L", "l"), ("12 oz", "oz")],
)
async def test_lookup_maps_quantity_to_unit(quantity: str, unit: str) -> None:
    api = _build_client(
        {
            "status": 1,
            "product": {
                "product_name": "Test Product",
                "brands": "Test Brand",
                "quantity": quantity,
                "categories_tags": [],
                "nutriments": {},
            },
        }
    )

    result = await api.lookup("3017620422003")

    assert result is not None
    assert result.unit == unit


@pytest.mark.asyncio
async def test_missing_brand_defaults_to_unknown() -> None:
    api = _build_client(
        {
            "status": 1,
            "product": {
                "product_name": "Test Product",
                "brands": "",
                "quantity": "500g",
                "categories_tags": [],
                "nutriments": {},
            },
        }
    )

    result = await api.lookup("3017620422003")

    assert result is not None
    assert result.brand == "Unknown"


@pytest.mark.asyncio
async def test_user_agent_header_sent() -> None:
    client = _Client(
        _Response(
            {
                "status": 1,
                "product": {
                    "product_name": "Nutella",
                    "brands": "Ferrero",
                    "quantity": "750g",
                    "categories_tags": [],
                    "nutriments": {},
                },
            }
        )
    )
    api = OpenFoodFactsAPI(client=client)

    _ = await api.lookup("3017620422003")

    assert client.last_headers == {"User-Agent": OpenFoodFactsAPI.USER_AGENT}

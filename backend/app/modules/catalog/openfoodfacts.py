from __future__ import annotations

import logging
import re
import time
from collections.abc import Mapping
from typing import Protocol, cast

import httpx

from app.core.database import AsyncSessionLocal
from app.models.ai_inference_log import AiInferenceLog

from .normalizer import normalize_ingredient_name
from .schemas import BarcodeResult


logger = logging.getLogger(__name__)


type QueryParams = Mapping[str, str]
type JSONDict = dict[str, object]


_UNIT_PATTERN = re.compile(r"(\d[\d.,]*)\s*(g|kg|ml|l|cl|oz|lb|fl\s*oz)\b", re.IGNORECASE)


def _extract_unit(quantity_str: str) -> str | None:
    match = _UNIT_PATTERN.search(quantity_str)
    return match.group(2).lower().strip() if match else None


class BarcodeHTTPResponse(Protocol):
    status_code: int

    def raise_for_status(self) -> object: ...

    def json(self) -> object: ...


class BarcodeHTTPClient(Protocol):
    async def get(
        self,
        url: str,
        *,
        params: QueryParams,
        headers: QueryParams,
    ) -> BarcodeHTTPResponse: ...


class OpenFoodFactsAPI:
    USER_AGENT: str = "FridgeFriend/1.0 (contact@fridgefriend.app)"
    BASE_URL: str = "https://world.openfoodfacts.org/api/v2/product"
    FIELDS: str = "product_name,brands,quantity,categories_tags,nutriments"

    def __init__(self, *, client: BarcodeHTTPClient | None = None) -> None:
        self._client: BarcodeHTTPClient | None = client

    async def lookup(self, barcode: str) -> BarcodeResult | None:
        start = time.perf_counter()
        status = "success"
        error_detail: str | None = None
        try:
            url = f"{self.BASE_URL}/{barcode}.json"
            params = {"fields": self.FIELDS}
            headers = {"User-Agent": self.USER_AGENT}
            if self._client is not None:
                response = await self._client.get(url, params=params, headers=headers)
            else:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url, params=params, headers=headers)

            if response.status_code == 404:
                return None
            _ = response.raise_for_status()

            payload = response.json()
            if not isinstance(payload, dict):
                return None
            payload_dict = cast(JSONDict, payload)
            if payload_dict.get("status") != 1 or "product" not in payload_dict:
                return None

            product = payload_dict["product"]
            if not isinstance(product, dict):
                return None
            return self._map_product(barcode, cast(JSONDict, product))
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            status = "error"
            error_detail = str(exc)[:500]
            raise
        except Exception as exc:
            status = "error"
            error_detail = str(exc)[:500]
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            await self._log_inference(duration_ms, status, error_detail)

    @staticmethod
    def _map_product(barcode: str, product: dict[str, object]) -> BarcodeResult:
        product_name = str(product.get("product_name") or "").strip()
        brand = str(product.get("brands") or "").strip()
        quantity_str = str(product.get("quantity") or "").strip()
        unit = _extract_unit(quantity_str) or "unit"
        canonical_name = normalize_ingredient_name(product_name)
        display_name = f"{product_name} {quantity_str}".strip() if quantity_str else product_name
        return BarcodeResult.model_validate(
            {
                "barcode": barcode,
                "displayName": display_name,
                "canonicalName": canonical_name,
                "brand": brand or "Unknown",
                "unit": unit,
            }
        )

    async def _log_inference(self, duration_ms: float, status: str, error_detail: str | None) -> None:
        try:
            async with AsyncSessionLocal() as session:
                session.add(
                    AiInferenceLog(
                        provider="openfoodfacts",
                        operation="barcode_lookup",
                        duration_ms=duration_ms,
                        status=status,
                        api_points_used=1,
                        items_returned=1 if status == "success" else 0,
                        error_detail=error_detail,
                    )
                )
                await session.commit()
        except Exception as exc:
            logger.warning("Open Food Facts inference logging failed: %s", exc)

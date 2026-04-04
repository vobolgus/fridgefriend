from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Protocol, cast

import httpx

from app.core.database import AsyncSessionLocal
from app.models.ai_inference_log import AiInferenceLog


type QueryParamValue = str | int | float | bool
type QueryParams = Mapping[str, QueryParamValue]
type JSONDict = dict[str, object]


class RecipeHTTPClient(Protocol):
    async def get(self, url: str, params: QueryParams) -> httpx.Response | object: ...


class SpoonacularClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.spoonacular.com",
        client: RecipeHTTPClient | None = None,
    ) -> None:
        self._api_key: str = api_key
        self._base_url: str = base_url.rstrip("/")
        self._client: RecipeHTTPClient | None = client

    async def search_recipes(self, ingredients: list[str], count: int = 10) -> list[dict[str, object]]:
        params: dict[str, QueryParamValue] = {
            "apiKey": self._api_key,
            "ingredients": ",".join(sorted(set(ingredients))),
            "number": count,
            "ranking": 2,
            "ignorePantry": False,
        }
        start = time.perf_counter()
        status = "success"
        error_detail = None
        result: list[dict[str, object]] = []

        try:
            if self._client is not None:
                response = await self._client.get(f"{self._base_url}/recipes/findByIngredients", params=params)
            else:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.get(f"{self._base_url}/recipes/findByIngredients", params=params)
            raise_for_status = getattr(response, "raise_for_status", None)
            if callable(raise_for_status):
                _ = raise_for_status()

            json_loader = getattr(response, "json", None)
            payload: object = json_loader() if callable(json_loader) else []
            if not isinstance(payload, list):
                result = []
            else:
                normalized_payload: list[JSONDict] = []
                for raw_item in cast(list[object], payload):
                    if isinstance(raw_item, dict):
                        normalized_payload.append(cast(JSONDict, raw_item))
                result = [self._map_recipe(item) for item in normalized_payload]
        except Exception as exc:
            status = "error"
            error_detail = str(exc)[:500]
            result = []
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            await self._log_inference(duration_ms, len(result), status, error_detail)

        return result

    async def _log_inference(
        self,
        duration_ms: float,
        items_returned: int,
        status: str,
        error_detail: str | None,
    ) -> None:
        try:
            async with AsyncSessionLocal() as session:
                session.add(
                    AiInferenceLog(
                        provider="spoonacular",
                        operation="recipe_search",
                        duration_ms=duration_ms,
                        status=status,
                        api_points_used=1,
                        items_returned=items_returned,
                        error_detail=error_detail,
                    )
                )
                await session.commit()
        except Exception:
            pass

    @staticmethod
    def _map_recipe(payload: Mapping[str, object]) -> dict[str, object]:
        payload_dict = cast(JSONDict, payload)
        used_ingredients = payload_dict.get("usedIngredients", [])
        missed_ingredients = payload_dict.get("missedIngredients", [])
        ingredients: list[dict[str, object]] = []
        combined_ingredients: list[object] = []
        if isinstance(used_ingredients, list):
            combined_ingredients.extend(cast(list[object], used_ingredients))
        if isinstance(missed_ingredients, list):
            combined_ingredients.extend(cast(list[object], missed_ingredients))
        for ingredient in combined_ingredients:
            if not isinstance(ingredient, Mapping):
                continue
            ingredient_dict = cast(JSONDict, ingredient)
            name = str(ingredient_dict.get("name") or ingredient_dict.get("originalName") or "").strip().lower()
            if not name:
                continue
            ingredients.append(
                {
                    "canonical_name": name,
                    "quantity": _to_float(ingredient_dict.get("amount"), default=0.0),
                    "unit": str(ingredient_dict.get("unit") or "unit"),
                }
            )

        return {
            "id": str(payload_dict.get("id", "")),
            "title": str(payload_dict.get("title", "")),
            "prep_minutes": int(_to_float(payload_dict.get("readyInMinutes"), default=0.0)),
            "image_url": str(payload_dict.get("image")) if payload_dict.get("image") else None,
            "source_url": None,
            "summary": None,
            "instructions": [],
            "cuisines": [],
            "servings": None,
            "nutrition": None,
            "dietary_tags": [],
            "ingredients": ingredients,
        }


def _to_float(value: object, *, default: float) -> float:
    if isinstance(value, bool):
        return default
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any, cast

from opensearchpy import AsyncOpenSearch

from app.core.config import settings

logger = logging.getLogger(__name__)

type JSONDict = dict[str, object]


class OpenSearchRecipeSource:
    def __init__(
        self,
        client: AsyncOpenSearch | Any | None = None,
        *,
        url: str | None = None,
        index_name: str | None = None,
    ) -> None:
        self._client: AsyncOpenSearch | Any = client or AsyncOpenSearch(hosts=[url or settings.OPENSEARCH_URL])
        self._index_name: str = index_name or settings.OPENSEARCH_INDEX

    async def search_recipes(
        self,
        ingredients: list[str],
        count: int = 50,
        dietary_tags: list[str] | None = None,
        max_prep_minutes: int | None = None,
    ) -> list[dict[str, object]]:
        query = build_recipe_search_query(
            ingredients,
            dietary_tags=dietary_tags,
            max_prep_minutes=max_prep_minutes,
            count=count,
        )
        try:
            response = await self._client.search(index=self._index_name, body=query)
        except Exception as exc:
            logger.warning("OpenSearch recipe lookup failed: %s", exc)
            return []

        hits = response.get("hits", {}).get("hits", []) if isinstance(response, dict) else []
        if not isinstance(hits, list):
            return []

        recipes: list[dict[str, object]] = []
        for hit in hits:
            if isinstance(hit, Mapping):
                recipes.append(_map_hit_to_recipe(hit))
        return recipes


def build_recipe_search_query(
    ingredients: list[str],
    *,
    dietary_tags: list[str] | None = None,
    max_prep_minutes: int | None = None,
    count: int = 50,
) -> dict[str, object]:
    normalized_ingredients = sorted({ingredient.strip().lower() for ingredient in ingredients if ingredient.strip()})
    should_clauses: list[dict[str, object]] = [
        {"term": {"ingredients": ingredient}} for ingredient in normalized_ingredients
    ]

    filters: list[dict[str, object]] = []
    normalized_tags = sorted({tag.strip().lower() for tag in dietary_tags or [] if tag.strip()})
    if normalized_tags:
        filters.append({"terms": {"dietary_tags": normalized_tags}})
    if max_prep_minutes is not None:
        filters.append({"range": {"prep_minutes": {"lte": max_prep_minutes}}})

    bool_query: dict[str, object] = {
        "should": should_clauses,
        "minimum_should_match": 1 if should_clauses else 0,
    }
    if filters:
        bool_query["filter"] = filters

    return {
        "size": count,
        "sort": [{"_score": {"order": "desc"}}],
        "query": {"bool": bool_query},
    }


def _map_hit_to_recipe(hit: Mapping[str, object]) -> dict[str, object]:
    source_raw = hit.get("_source", {})
    source = cast(JSONDict, source_raw if isinstance(source_raw, dict) else {})

    ingredient_names_raw = source.get("ingredients", [])
    ingredients: list[dict[str, object]] = []
    if isinstance(ingredient_names_raw, list):
        for ingredient_name in ingredient_names_raw:
            if isinstance(ingredient_name, str) and ingredient_name.strip():
                ingredients.append(
                    {
                        "canonical_name": ingredient_name.strip().lower(),
                        "quantity": 0.0,
                        "unit": "unit",
                    }
                )

    instructions = _map_instructions(source.get("instructions"))
    recipe_id = source.get("recipe_id") or hit.get("_id") or ""

    return {
        "id": str(recipe_id),
        "title": str(source.get("title", "")),
        "prep_minutes": _to_int(source.get("prep_minutes"), default=0),
        "image_url": _to_optional_str(source.get("image_url")),
        "source_url": None,
        "summary": None,
        "instructions": instructions,
        "cuisines": _to_str_list(source.get("cuisines")),
        "servings": _to_optional_int(source.get("servings")),
        "nutrition": None,
        "dietary_tags": _to_str_list(source.get("dietary_tags")),
        "ingredients": ingredients,
    }


def _map_instructions(value: object) -> list[dict[str, object]]:
    if isinstance(value, str):
        steps = [segment.strip() for segment in value.split("\n") if segment.strip()]
        return [{"number": index, "step": step} for index, step in enumerate(steps, start=1)]
    if isinstance(value, list):
        mapped_steps: list[dict[str, object]] = []
        for index, step in enumerate(value, start=1):
            if isinstance(step, str) and step.strip():
                mapped_steps.append({"number": index, "step": step.strip()})
        return mapped_steps
    return []


def _to_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


def _to_optional_str(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None


def _to_int(value: object, *, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def _to_optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None

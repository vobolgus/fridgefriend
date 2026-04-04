from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from opensearchpy.helpers import async_bulk

INDEX_MAPPING: dict[str, object] = {
    "mappings": {
        "properties": {
            "recipe_id": {"type": "keyword"},
            "title": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword"}},
            },
            "ingredients": {"type": "keyword"},
            "cuisines": {"type": "keyword"},
            "dietary_tags": {"type": "keyword"},
            "prep_minutes": {"type": "integer"},
            "image_url": {"type": "keyword"},
            "servings": {"type": "integer"},
            "instructions": {"type": "text"},
        }
    }
}


def recipe_to_document(recipe: dict[str, object]) -> dict[str, object]:
    ingredients_raw = recipe.get("ingredients", [])
    ingredient_names: list[str] = []
    if isinstance(ingredients_raw, list):
        for ingredient in ingredients_raw:
            if not isinstance(ingredient, dict):
                continue
            candidate = ingredient.get("canonical_name") or ingredient.get("name")
            if isinstance(candidate, str) and candidate.strip():
                ingredient_names.append(candidate.strip().lower())

    instructions_raw = recipe.get("instructions", [])
    instruction_steps: list[str] = []
    if isinstance(instructions_raw, list):
        for instruction in instructions_raw:
            if not isinstance(instruction, dict):
                continue
            step = instruction.get("step")
            if isinstance(step, str) and step.strip():
                instruction_steps.append(step.strip())

    return {
        "recipe_id": recipe.get("id"),
        "title": recipe.get("title", ""),
        "ingredients": ingredient_names,
        "cuisines": _normalize_string_list(recipe.get("cuisines")),
        "dietary_tags": _normalize_string_list(recipe.get("dietary_tags")),
        "prep_minutes": _coerce_int(recipe.get("prep_minutes")),
        "image_url": recipe.get("image_url"),
        "servings": _coerce_int(recipe.get("servings")),
        "instructions": "\n".join(instruction_steps),
    }


async def create_index(client: Any, index_name: str) -> None:
    exists = await client.indices.exists(index=index_name)
    if exists:
        return
    await client.indices.create(index=index_name, body=INDEX_MAPPING)


async def index_recipes(client: Any, index_name: str, recipes: Sequence[dict[str, object]]) -> None:
    actions = [
        {
            "_index": index_name,
            "_id": str(recipe.get("id", "")),
            "_source": recipe_to_document(recipe),
        }
        for recipe in recipes
    ]
    if not actions:
        return
    await async_bulk(client, actions, refresh=True)


def _normalize_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            normalized.append(item.strip())
    return normalized


def _coerce_int(value: object) -> int | None:
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

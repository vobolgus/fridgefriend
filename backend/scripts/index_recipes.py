from __future__ import annotations

import argparse
import asyncio
import logging
import re
from collections.abc import Mapping, Sequence
from typing import cast

import httpx
from opensearchpy import AsyncOpenSearch
from opensearchpy.helpers import async_bulk

from app.modules.recommendations.opensearch_index import INDEX_MAPPING

logger = logging.getLogger(__name__)

SPOONACULAR_BASE_URL = "https://api.spoonacular.com"
MAX_PAGE_SIZE = 100
HTML_TAG_RE = re.compile(r"<[^>]+>")

type JSONDict = dict[str, object]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch Spoonacular recipes and index them into OpenSearch.")
    _ = parser.add_argument("--api-key", required=True, help="Spoonacular API key")
    _ = parser.add_argument("--opensearch-url", required=True, help="OpenSearch base URL")
    _ = parser.add_argument("--index", default="recipes", help="OpenSearch index name")
    _ = parser.add_argument("--count", type=int, default=100, help="Number of recipes to fetch and index")
    return parser.parse_args()


async def fetch_recipes(api_key: str, *, count: int, client: httpx.AsyncClient | None = None) -> list[JSONDict]:
    if count <= 0:
        return []

    owns_client = client is None
    http_client = client or httpx.AsyncClient(base_url=SPOONACULAR_BASE_URL, timeout=30.0)
    recipes: list[JSONDict] = []
    offset = 0

    try:
        while len(recipes) < count:
            batch_size = min(MAX_PAGE_SIZE, count - len(recipes))
            params = {
                "apiKey": api_key,
                "addRecipeInformation": True,
                "fillIngredients": True,
                "number": batch_size,
                "offset": offset,
            }
            logger.info("Fetching Spoonacular recipes offset=%s batch=%s", offset, batch_size)
            response = await http_client.get("/recipes/complexSearch", params=params)
            _ = response.raise_for_status()
            payload_raw = _load_json(response)
            if not isinstance(payload_raw, dict):
                logger.warning("Unexpected Spoonacular response type: %s", type(payload_raw).__name__)
                break
            payload = cast(JSONDict, payload_raw)

            results_raw = payload.get("results", [])
            if not isinstance(results_raw, list) or not results_raw:
                break

            normalized_results = [cast(JSONDict, item) for item in cast(list[object], results_raw) if isinstance(item, dict)]
            recipes.extend(normalized_results)

            if len(normalized_results) < batch_size:
                break
            offset += len(normalized_results)
    finally:
        if owns_client:
            await http_client.aclose()

    return recipes[:count]


def map_spoonacular_recipe(recipe: Mapping[str, object]) -> JSONDict:
    recipe_dict = cast(JSONDict, recipe)
    recipe_id = recipe_dict.get("id", "")

    instructions = _extract_instructions(recipe_dict)
    return {
        "recipe_id": str(recipe_id),
        "title": _to_str(recipe_dict.get("title")),
        "prep_minutes": _to_int(recipe_dict.get("readyInMinutes")),
        "image_url": _to_optional_str(recipe_dict.get("image")),
        "instructions": instructions,
        "cuisines": _to_string_list(recipe_dict.get("cuisines")),
        "servings": _to_optional_int(recipe_dict.get("servings")),
        "dietary_tags": _extract_dietary_tags(recipe_dict),
        "ingredients": _extract_ingredients(recipe_dict),
    }


async def ensure_index(client: AsyncOpenSearch, index_name: str) -> None:
    if await client.indices.exists(index=index_name):
        return
    logger.info("Creating OpenSearch index %s", index_name)
    await client.indices.create(index=index_name, body=INDEX_MAPPING)


async def bulk_index_recipes(
    client: AsyncOpenSearch,
    *,
    index_name: str,
    recipes: Sequence[Mapping[str, object]],
) -> None:
    actions = [
        {
            "_op_type": "index",
            "_index": index_name,
            "_id": str(recipe.get("recipe_id", "")),
            "_source": dict(recipe),
        }
        for recipe in recipes
    ]
    if not actions:
        logger.info("No recipes to index")
        return

    logger.info("Indexing %s recipes into %s", len(actions), index_name)
    success_count, errors_raw = await async_bulk(client, actions, refresh=True, raise_on_error=False)
    errors = cast(list[object], errors_raw)
    if errors:
        logger.warning("Indexed %s recipes with %s bulk errors", success_count, len(errors))
    else:
        logger.info("Indexed %s recipes successfully", success_count)


async def run(api_key: str, opensearch_url: str, *, index_name: str, count: int) -> None:
    spoonacular_recipes = await fetch_recipes(api_key, count=count)
    logger.info("Fetched %s Spoonacular recipes", len(spoonacular_recipes))
    documents = [map_spoonacular_recipe(recipe) for recipe in spoonacular_recipes]

    client = AsyncOpenSearch(hosts=[opensearch_url])
    try:
        await ensure_index(client, index_name)
        await bulk_index_recipes(client, index_name=index_name, recipes=documents)
    finally:
        await client.close()


def _extract_instructions(recipe: Mapping[str, object]) -> str:
    analyzed_instructions = recipe.get("analyzedInstructions", [])
    steps: list[str] = []
    if isinstance(analyzed_instructions, list):
        for instruction in cast(list[object], analyzed_instructions):
            if not isinstance(instruction, Mapping):
                continue
            instruction_dict = cast(Mapping[str, object], instruction)
            instruction_steps = instruction_dict.get("steps", [])
            if not isinstance(instruction_steps, list):
                continue
            for step in cast(list[object], instruction_steps):
                if not isinstance(step, Mapping):
                    continue
                step_dict = cast(Mapping[str, object], step)
                text = _strip_html(_to_str(step_dict.get("step"))).strip()
                if text:
                    steps.append(text)

    if steps:
        return "\n".join(steps)

    raw_instructions = _strip_html(_to_str(recipe.get("instructions"))).strip()
    return raw_instructions


def _extract_dietary_tags(recipe: Mapping[str, object]) -> list[str]:
    tags: list[str] = []
    flag_to_tag = {
        "vegetarian": "vegetarian",
        "vegan": "vegan",
        "glutenFree": "gluten-free",
        "dairyFree": "dairy-free",
        "veryHealthy": "very-healthy",
        "sustainable": "sustainable",
        "lowFodmap": "low-fodmap",
        "whole30": "whole30",
    }
    for field_name, tag in flag_to_tag.items():
        if recipe.get(field_name) is True:
            tags.append(tag)
    return tags


def _extract_ingredients(recipe: Mapping[str, object]) -> list[str]:
    ingredients_raw = recipe.get("extendedIngredients", [])
    ingredients: list[str] = []
    if not isinstance(ingredients_raw, list):
        return ingredients

    for ingredient in cast(list[object], ingredients_raw):
        if not isinstance(ingredient, Mapping):
            continue
        ingredient_dict = cast(Mapping[str, object], ingredient)
        candidate = (
            ingredient_dict.get("nameClean")
            or ingredient_dict.get("name")
            or ingredient_dict.get("originalName")
            or ingredient_dict.get("original")
        )
        if isinstance(candidate, str):
            normalized = candidate.strip().lower()
            if normalized:
                ingredients.append(normalized)
    return sorted(set(ingredients))


def _to_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in cast(list[object], value):
        if isinstance(item, str):
            normalized = item.strip()
            if normalized:
                result.append(normalized)
    return result


def _to_str(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _to_optional_str(value: object) -> str | None:
    normalized = _to_str(value)
    return normalized or None


def _to_int(value: object) -> int:
    return _to_optional_int(value) or 0


def _to_optional_int(value: object) -> int | None:
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


def _strip_html(value: str) -> str:
    return HTML_TAG_RE.sub("", value)


def _load_json(response: httpx.Response) -> object:
    return cast(object, response.json())


async def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parsed_args = cast(dict[str, object], vars(args))
    api_key = str(parsed_args["api_key"])
    opensearch_url = str(parsed_args["opensearch_url"])
    index_name = str(parsed_args["index"])
    count_value = parsed_args["count"]
    if isinstance(count_value, bool):
        count = int(count_value)
    elif isinstance(count_value, int | float | str):
        count = int(count_value)
    else:
        raise ValueError("count must be an int")
    await run(api_key, opensearch_url, index_name=index_name, count=count)


if __name__ == "__main__":
    asyncio.run(main())

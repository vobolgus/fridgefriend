from __future__ import annotations

import pytest

from app.modules.recommendations.opensearch_client import OpenSearchRecipeSource
from app.modules.recommendations.opensearch_client import build_recipe_search_query


class _StubOpenSearchClient:
    def __init__(self, response: dict[str, object] | None = None, error: Exception | None = None) -> None:
        self.response = response or {"hits": {"hits": []}}
        self.error = error
        self.calls: list[dict[str, object]] = []

    async def search(self, *, index: str, body: dict[str, object]) -> dict[str, object]:
        self.calls.append({"index": index, "body": body})
        if self.error is not None:
            raise self.error
        return self.response


@pytest.mark.asyncio
async def test_search_builds_correct_query() -> None:
    client = _StubOpenSearchClient()
    recipe_source = OpenSearchRecipeSource(client=client, index_name="recipes-test")

    await recipe_source.search_recipes(["milk", "eggs", "milk"], count=25)

    assert len(client.calls) == 1
    assert client.calls[0]["index"] == "recipes-test"
    assert client.calls[0]["body"] == {
        "size": 25,
        "sort": [{"_score": {"order": "desc"}}],
        "query": {
            "bool": {
                "should": [{"term": {"ingredients": "eggs"}}, {"term": {"ingredients": "milk"}}],
                "minimum_should_match": 1,
            }
        },
    }


@pytest.mark.asyncio
async def test_search_maps_hits_to_recipes() -> None:
    client = _StubOpenSearchClient(
        response={
            "hits": {
                "hits": [
                    {
                        "_id": "recipe-1",
                        "_source": {
                            "recipe_id": "recipe-1",
                            "title": "Egg Fried Rice",
                            "ingredients": ["eggs", "rice", "onions"],
                            "cuisines": ["Asian"],
                            "dietary_tags": ["vegetarian"],
                            "prep_minutes": 15,
                            "image_url": "https://example.com/rice.jpg",
                            "servings": 2,
                            "instructions": "Beat eggs\nCook rice",
                        },
                    }
                ]
            }
        }
    )
    recipe_source = OpenSearchRecipeSource(client=client)

    recipes = await recipe_source.search_recipes(["eggs", "rice"])

    assert recipes == [
        {
            "id": "recipe-1",
            "title": "Egg Fried Rice",
            "prep_minutes": 15,
            "image_url": "https://example.com/rice.jpg",
            "source_url": None,
            "summary": None,
            "instructions": [
                {"number": 1, "step": "Beat eggs"},
                {"number": 2, "step": "Cook rice"},
            ],
            "cuisines": ["Asian"],
            "servings": 2,
            "nutrition": None,
            "dietary_tags": ["vegetarian"],
            "ingredients": [
                {"canonical_name": "eggs", "quantity": 0.0, "unit": "unit"},
                {"canonical_name": "rice", "quantity": 0.0, "unit": "unit"},
                {"canonical_name": "onions", "quantity": 0.0, "unit": "unit"},
            ],
        }
    ]


def test_search_with_dietary_filter() -> None:
    query = build_recipe_search_query(["spinach"], dietary_tags=["vegetarian", "vegetarian", "gluten-free"])

    assert query["query"] == {
        "bool": {
            "should": [{"term": {"ingredients": "spinach"}}],
            "minimum_should_match": 1,
            "filter": [{"terms": {"dietary_tags": ["gluten-free", "vegetarian"]}}],
        }
    }


def test_search_with_prep_time_filter() -> None:
    query = build_recipe_search_query(["tomatoes"], max_prep_minutes=20)

    assert query["query"] == {
        "bool": {
            "should": [{"term": {"ingredients": "tomatoes"}}],
            "minimum_should_match": 1,
            "filter": [{"range": {"prep_minutes": {"lte": 20}}}],
        }
    }


@pytest.mark.asyncio
async def test_search_graceful_fallback(caplog: pytest.LogCaptureFixture) -> None:
    client = _StubOpenSearchClient(error=RuntimeError("opensearch unavailable"))
    recipe_source = OpenSearchRecipeSource(client=client)

    with caplog.at_level("WARNING"):
        recipes = await recipe_source.search_recipes(["eggs"])

    assert recipes == []
    assert "OpenSearch recipe lookup failed" in caplog.text

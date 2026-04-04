from __future__ import annotations

import asyncio

from opensearchpy import AsyncOpenSearch

from app.core.config import settings
from app.modules.recommendations.fixture_recipes import FIXTURE_RECIPES
from app.modules.recommendations.opensearch_index import create_index, index_recipes


async def main() -> None:
    client = AsyncOpenSearch(hosts=[settings.OPENSEARCH_URL])
    try:
        await create_index(client, settings.OPENSEARCH_INDEX)
        await index_recipes(client, settings.OPENSEARCH_INDEX, FIXTURE_RECIPES)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())

# pyright: reportUnknownMemberType=false

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.config import settings

try:
    import redis.asyncio as redis_asyncio
except ImportError:
    redis_asyncio = None

if TYPE_CHECKING:
    from redis.asyncio import Redis


def get_redis_client() -> Redis | None:
    if redis_asyncio is None:
        return None
    if settings.DATABASE_URL.startswith("sqlite+aiosqlite:///:memory:"):
        return None
    return redis_asyncio.Redis.from_url(settings.REDIS_URL)


async def get_redis() -> Redis | None:
    return get_redis_client()

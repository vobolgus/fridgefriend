# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false

from __future__ import annotations

try:
    from redis.asyncio import Redis
except ImportError:
    Redis = None  # type: ignore[assignment,misc]

from app.core.config import settings


async def get_redis() -> object | None:
    if Redis is None:
        return None
    return Redis.from_url(settings.REDIS_URL)

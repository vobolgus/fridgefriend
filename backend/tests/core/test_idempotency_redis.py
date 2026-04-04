from __future__ import annotations

import time

from app.core.idempotency import MemoryIdempotencyCache, RedisIdempotencyCache


class FakeRedis:
    def __init__(self) -> None:
        self.data: dict[str, tuple[float | None, str]] = {}

    def get(self, key: str) -> str | None:
        payload = self.data.get(key)
        if payload is None:
            return None
        expires_at, value = payload
        if expires_at is not None and expires_at < time.time():
            self.data.pop(key, None)
            return None
        return value

    def set(self, key: str, value: str, ex: int) -> None:
        self.data[key] = (time.time() + ex, value)

    def delete(self, *keys: str) -> None:
        for key in keys:
            self.data.pop(key, None)


class BrokenRedis:
    def get(self, key: str) -> str | None:
        raise OSError("redis unavailable")

    def set(self, key: str, value: str, ex: int) -> None:
        raise OSError("redis unavailable")

    def delete(self, *keys: str) -> None:
        raise OSError("redis unavailable")


def test_redis_idempotency_caches_response() -> None:
    cache = RedisIdempotencyCache(redis_client=FakeRedis(), fallback=MemoryIdempotencyCache(ttl_seconds=10), ttl_seconds=10)

    cache.set("user:/v1/items:key", {"ok": True})

    assert cache.get("user:/v1/items:key") == {"ok": True}


def test_redis_idempotency_expires_after_ttl() -> None:
    cache = RedisIdempotencyCache(redis_client=FakeRedis(), fallback=MemoryIdempotencyCache(ttl_seconds=1), ttl_seconds=1)

    cache.set("user:/v1/items:key", {"ok": True})
    time.sleep(1.1)

    assert cache.get("user:/v1/items:key") is None


def test_fallback_to_memory_when_redis_unavailable() -> None:
    fallback = MemoryIdempotencyCache(ttl_seconds=10)
    cache = RedisIdempotencyCache(redis_client=BrokenRedis(), fallback=fallback, ttl_seconds=10)

    cache.set("user:/v1/items:key", {"ok": True})

    assert fallback.get("user:/v1/items:key") == {"ok": True}
    assert cache.get("user:/v1/items:key") == {"ok": True}

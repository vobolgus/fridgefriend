# pyright: reportAny=false, reportExplicitAny=false, reportUnknownVariableType=false

from __future__ import annotations

import importlib
import json
import time
from typing import Annotated
from typing import Any

from fastapi import Header, HTTPException, status

from app.core.config import settings


class RedisError(Exception):
    pass


def _load_redis_class() -> type[Any] | None:
    try:
        redis_module = importlib.import_module("redis")
    except ImportError:
        return None

    redis_class = getattr(redis_module, "Redis", None)
    return redis_class if isinstance(redis_class, type) else None


RedisClient = _load_redis_class()


class MemoryIdempotencyCache:
    def __init__(self, ttl_seconds: int | None = None) -> None:
        self._ttl_seconds: int = ttl_seconds or settings.IDEMPOTENCY_TTL_SECONDS
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}

    def get(self, key: str) -> dict[str, Any] | None:
        payload = self._cache.get(key)
        if payload is None:
            return None

        expires_at, response_data = payload
        if expires_at < time.time():
            _ = self._cache.pop(key, None)
            return None

        return response_data

    def set(self, key: str, response_data: dict[str, Any]) -> None:
        self._cache[key] = (time.time() + self._ttl_seconds, response_data)

    def clear(self) -> None:
        self._cache.clear()


class RedisIdempotencyCache:
    def __init__(
        self,
        redis_client: Any | None = None,
        *,
        fallback: MemoryIdempotencyCache | None = None,
        ttl_seconds: int | None = None,
    ) -> None:
        self._ttl_seconds: int = ttl_seconds or settings.IDEMPOTENCY_TTL_SECONDS
        self._fallback: MemoryIdempotencyCache = fallback or MemoryIdempotencyCache(self._ttl_seconds)
        self._redis_client: Any | None = redis_client if redis_client is not None else self._build_client()
        self._tracked_keys: set[str] = set()

    def _build_client(self) -> Any | None:
        if RedisClient is None:
            return None
        return RedisClient.from_url(settings.REDIS_URL, decode_responses=True)

    def get(self, key: str) -> dict[str, Any] | None:
        if self._redis_client is None:
            return self._fallback.get(key)

        try:
            payload = self._redis_client.get(key)
        except (RedisError, OSError, ValueError, AttributeError):
            return self._fallback.get(key)

        if payload is None:
            return self._fallback.get(key)

        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        if not isinstance(payload, str):
            return self._fallback.get(key)

        data = json.loads(payload)
        return data if isinstance(data, dict) else None

    def set(self, key: str, response_data: dict[str, Any]) -> None:
        self._tracked_keys.add(key)
        if self._redis_client is None:
            self._fallback.set(key, response_data)
            return

        try:
            self._redis_client.set(key, json.dumps(response_data), ex=self._ttl_seconds)
        except (RedisError, OSError, ValueError, AttributeError):
            self._fallback.set(key, response_data)

    def clear(self) -> None:
        self._fallback.clear()
        if self._redis_client is None or not self._tracked_keys:
            return

        try:
            self._redis_client.delete(*self._tracked_keys)
        except (RedisError, OSError, ValueError, AttributeError):
            return
        finally:
            self._tracked_keys.clear()


_memory_cache = MemoryIdempotencyCache()
_redis_cache = RedisIdempotencyCache(fallback=_memory_cache)


def _scoped_key(user_id: str, path: str, raw_key: str) -> str:
    return f"{user_id}:{path}:{raw_key}"


def _get_backend() -> MemoryIdempotencyCache | RedisIdempotencyCache:
    if settings.IDEMPOTENCY_BACKEND == "redis":
        return _redis_cache
    return _memory_cache


def get_cached(user_id: str, path: str, raw_key: str) -> dict[str, Any] | None:
    return _get_backend().get(_scoped_key(user_id, path, raw_key))


def store_cached(user_id: str, path: str, raw_key: str, response_data: dict[str, Any]) -> None:
    _get_backend().set(_scoped_key(user_id, path, raw_key), response_data)


def clear_cache() -> None:
    _memory_cache.clear()
    _redis_cache.clear()


def require_idempotency_key(idempotency_key: Annotated[str | None, Header()] = None) -> str:
    if idempotency_key is None or not idempotency_key.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required",
        )
    return idempotency_key

# pyright: reportExplicitAny=false

from __future__ import annotations

from typing import Any

_cache: dict[str, dict[str, Any]] = {}


def _scoped_key(user_id: str, path: str, raw_key: str) -> str:
    return f"{user_id}:{path}:{raw_key}"


def get_cached(user_id: str, path: str, raw_key: str) -> dict[str, Any] | None:
    return _cache.get(_scoped_key(user_id, path, raw_key))


def store_cached(user_id: str, path: str, raw_key: str, response_data: dict[str, Any]) -> None:
    _cache[_scoped_key(user_id, path, raw_key)] = response_data


def clear_cache() -> None:
    _cache.clear()

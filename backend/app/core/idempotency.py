# pyright: reportExplicitAny=false

from __future__ import annotations

from typing import Any

_cache: dict[str, dict[str, Any]] = {}


def get_cached(key: str) -> dict[str, Any] | None:
    return _cache.get(key)


def store_cached(key: str, response_data: dict[str, Any]) -> None:
    _cache[key] = response_data


def clear_cache() -> None:
    _cache.clear()

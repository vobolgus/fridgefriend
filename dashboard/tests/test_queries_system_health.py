# pyright: reportImplicitRelativeImport=false, reportMissingTypeStubs=false, reportUnannotatedClassAttribute=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportAny=false, reportUnknownLambdaType=false, reportMissingTypeArgument=false

from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace

import pandas as pd
import pytest

from queries import system_health


class _FakeElapsed:
    def __init__(self, seconds: float):
        self._seconds = seconds

    def total_seconds(self) -> float:
        return self._seconds


class _FakeResponse:
    def __init__(self, payload: dict, seconds: float = 0.123):
        self._payload = payload
        self.elapsed = _FakeElapsed(seconds)

    def json(self) -> dict:
        return self._payload


class _FakeHttpxClient:
    def __init__(self, response: _FakeResponse):
        self._response = response

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, _url: str) -> _FakeResponse:
        return self._response


def test_check_backend_health_returns_ok_status(monkeypatch):
    response = _FakeResponse({"version": "1.2.3"}, seconds=0.25)
    fake_httpx = SimpleNamespace(Client=lambda timeout=5.0: _FakeHttpxClient(response))
    monkeypatch.setitem(__import__("sys").modules, "httpx", fake_httpx)

    result = system_health.check_backend_health()

    assert result["status"] == "ok"
    assert result["version"] == "1.2.3"
    assert result["latency_ms"] == pytest.approx(250.0)


def test_check_postgres_returns_ok_status(monkeypatch):
    monkeypatch.setattr(system_health, "run_query", lambda sql: pd.DataFrame({"ok": [1]}))

    result = system_health.check_postgres()

    assert result == {"status": "ok"}


def test_check_postgres_returns_error_status(monkeypatch):
    def _raise(_sql: str):
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(system_health, "run_query", _raise)

    result = system_health.check_postgres()

    assert result["status"] == "error"
    assert "db unavailable" in result["error"]


def test_check_redis_returns_ok_status(monkeypatch):
    class _RedisClient:
        def ping(self):
            return True

    fake_redis = SimpleNamespace(from_url=lambda *args, **kwargs: _RedisClient())
    monkeypatch.setitem(__import__("sys").modules, "redis", fake_redis)

    result = system_health.check_redis()

    assert result == {"status": "ok"}


def test_check_redis_returns_error_status(monkeypatch):
    def _from_url(*args, **kwargs):
        raise RuntimeError("redis unavailable")

    fake_redis = SimpleNamespace(from_url=_from_url)
    monkeypatch.setitem(__import__("sys").modules, "redis", fake_redis)

    result = system_health.check_redis()

    assert result["status"] == "error"
    assert "redis unavailable" in result["error"]


def test_get_celery_queue_depth_returns_queue_depth(monkeypatch):
    class _RedisClient:
        def llen(self, _key: str) -> int:
            return 7

    fake_redis = SimpleNamespace(from_url=lambda *args, **kwargs: _RedisClient())
    monkeypatch.setitem(__import__("sys").modules, "redis", fake_redis)

    result = system_health.get_celery_queue_depth()

    assert result == 7


def test_get_celery_queue_depth_returns_none_on_error(monkeypatch):
    def _from_url(*args, **kwargs):
        raise RuntimeError("redis unavailable")

    fake_redis = SimpleNamespace(from_url=_from_url)
    monkeypatch.setitem(__import__("sys").modules, "redis", fake_redis)

    result = system_health.get_celery_queue_depth()

    assert result is None


@pytest.mark.parametrize(
    ("func_name", "args"),
    [
        ("get_api_latency", (date.today() - timedelta(days=7), date.today())),
        ("get_error_rate", (date.today() - timedelta(days=7), date.today())),
        ("get_throughput", (date.today() - timedelta(days=7), date.today())),
        ("get_latency_timeseries", (date.today() - timedelta(days=7), date.today())),
    ],
)
def test_runtime_query_functions_return_empty_dataframe_without_api_request_log(
    monkeypatch, func_name: str, args: tuple[date, date]
):
    monkeypatch.setattr(system_health, "check_table_exists", lambda table_name: False)

    def _should_not_run(*_args, **_kwargs):
        raise AssertionError("run_query should not be called when table is missing")

    monkeypatch.setattr(system_health, "run_query", _should_not_run)

    func = getattr(system_health, func_name)
    raw_func = getattr(func, "__wrapped__", func)
    result = raw_func(*args)

    assert isinstance(result, pd.DataFrame)
    assert result.empty

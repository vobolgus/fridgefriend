# pyright: reportImplicitRelativeImport=false, reportMissingTypeStubs=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportAny=false, reportUnknownLambdaType=false, reportMissingTypeArgument=false

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest

from queries import unit_economics


@pytest.mark.parametrize(
    ("func_name", "args"),
    [
        ("get_llm_cost", (date.today() - timedelta(days=30), date.today() + timedelta(days=1))),
        ("get_spoonacular_cost", (date.today() - timedelta(days=30), date.today() + timedelta(days=1))),
        ("get_total_cost_trend", (date.today() - timedelta(days=30), date.today() + timedelta(days=1))),
        ("get_cost_per_active_user", (date.today() + timedelta(days=1),)),
    ],
)
def test_unit_economics_queries_return_empty_dataframe_when_table_missing(
    monkeypatch, func_name: str, args: tuple[date, ...]
):
    monkeypatch.setattr(unit_economics, "check_table_exists", lambda table_name: False)

    def _should_not_run(*_args, **_kwargs):
        raise AssertionError("run_query should not be called when table is missing")

    monkeypatch.setattr(unit_economics, "run_query", _should_not_run)

    func = getattr(unit_economics, func_name)
    raw_func = getattr(func, "__wrapped__", func)
    result = raw_func(*args)

    assert isinstance(result, pd.DataFrame)
    assert result.empty


@pytest.mark.parametrize(
    ("func_name", "args", "expected_sql", "expected_params", "expected_df"),
    [
        (
            "get_llm_cost",
            (date(2026, 1, 1), date(2026, 1, 31)),
            unit_economics.Q_LLM_COST,
            {"start_date": date(2026, 1, 1), "end_date": date(2026, 1, 31)},
            pd.DataFrame({"day": [date(2026, 1, 1)], "total_cost_usd": [1.25]}),
        ),
        (
            "get_spoonacular_cost",
            (date(2026, 1, 1), date(2026, 1, 31)),
            unit_economics.Q_SPOONACULAR_COST,
            {"start_date": date(2026, 1, 1), "end_date": date(2026, 1, 31)},
            pd.DataFrame({"day": [date(2026, 1, 1)], "api_calls": [2]}),
        ),
        (
            "get_total_cost_trend",
            (date(2026, 1, 1), date(2026, 1, 31)),
            unit_economics.Q_TOTAL_COST_TREND,
            {"start_date": date(2026, 1, 1), "end_date": date(2026, 1, 31)},
            pd.DataFrame({"week_start": [date(2026, 1, 5)], "provider": ["litellm"]}),
        ),
        (
            "get_cost_per_active_user",
            (date(2026, 1, 31),),
            unit_economics.Q_COST_PER_ACTIVE_USER,
            {"end_date": date(2026, 1, 31)},
            pd.DataFrame({"cost_per_active_user": [0.42]}),
        ),
    ],
)
def test_unit_economics_queries_call_run_query_when_table_exists(
    monkeypatch,
    func_name: str,
    args: tuple[date, ...],
    expected_sql: str,
    expected_params: dict,
    expected_df: pd.DataFrame,
):
    monkeypatch.setattr(unit_economics, "check_table_exists", lambda table_name: True)

    calls: list[tuple[str, dict]] = []

    def _fake_run_query(sql: str, params: dict):
        calls.append((sql, params))
        return expected_df

    monkeypatch.setattr(unit_economics, "run_query", _fake_run_query)

    func = getattr(unit_economics, func_name)
    raw_func = getattr(func, "__wrapped__", func)
    result = raw_func(*args)

    assert calls == [(expected_sql, expected_params)]
    pd.testing.assert_frame_equal(result, expected_df)

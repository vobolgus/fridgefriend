# pyright: reportImplicitRelativeImport=false, reportMissingTypeStubs=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnusedParameter=false, reportMissingTypeArgument=false

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from queries.ai_quality import (
    Q_AVG_CONFIDENCE,
    Q_AVG_CONFIDENCE_TREND,
    Q_BARCODE_ITEM_COUNT,
    Q_BARCODE_ITEM_TREND,
    Q_CONFIDENCE_DISTRIBUTION,
    Q_PHOTO_FALLBACK_RATE,
    Q_PHOTO_FALLBACK_TREND,
    Q_PHOTO_ITEM_COUNT,
    Q_RECOMMENDATION_SESSION_COUNT,
    Q_RECOMMENDATION_STATS,
)

DATABASE_URL = "postgresql://fridgefriend:fridgefriend@localhost:5432/fridgefriend_test"


def _has_postgres() -> bool:
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            _ = conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


HAS_POSTGRES = _has_postgres()

pytestmark = pytest.mark.skipif(not HAS_POSTGRES, reason="PostgreSQL not available")


def _date_range() -> tuple[date, date]:
    return date.today() - timedelta(days=90), date.today() + timedelta(days=1)


def _query_df(db_conn, sql: str, params: dict | None = None) -> pd.DataFrame:
    return pd.read_sql_query(text(sql), db_conn, params=params or {})


def test_avg_confidence_returns_expected_values(
    db_conn, sample_users, sample_household, sample_items
):
    start_date, end_date = _date_range()

    df = _query_df(
        db_conn,
        Q_AVG_CONFIDENCE,
        {"start_date": start_date, "end_date": end_date},
    )

    row = df.iloc[0]
    assert list(df.columns) == ["avg_confidence", "photo_item_count"]
    assert float(row["avg_confidence"]) == pytest.approx(0.8)
    assert row["photo_item_count"] == 10


def test_confidence_distribution_returns_expected_buckets(
    db_conn, sample_users, sample_household, sample_items
):
    start_date, end_date = _date_range()

    df = _query_df(
        db_conn,
        Q_CONFIDENCE_DISTRIBUTION,
        {"start_date": start_date, "end_date": end_date},
    )

    row = df.iloc[0]
    assert list(df.columns) == [
        "week_start",
        "high_confidence",
        "medium_confidence",
        "low_confidence",
        "very_low_confidence",
    ]
    assert len(df) == 1
    assert row["high_confidence"] == 0
    assert row["medium_confidence"] == 10
    assert row["low_confidence"] == 0
    assert row["very_low_confidence"] == 0


def test_barcode_item_trend_returns_expected_weekly_counts(
    db_conn, sample_users, sample_household, sample_items
):
    start_date, end_date = _date_range()

    df = _query_df(
        db_conn,
        Q_BARCODE_ITEM_TREND,
        {"start_date": start_date, "end_date": end_date},
    )

    assert list(df.columns) == ["week_start", "barcode_items"]
    assert len(df) == 1
    assert df.iloc[0]["barcode_items"] == 10


def test_photo_fallback_rate_returns_expected_values(
    db_conn, sample_users, sample_household, sample_items
):
    start_date, end_date = _date_range()

    df = _query_df(
        db_conn,
        Q_PHOTO_FALLBACK_RATE,
        {"start_date": start_date, "end_date": end_date},
    )

    row = df.iloc[0]
    assert list(df.columns) == [
        "total_photo_items",
        "fallback_items",
        "fallback_rate_pct",
    ]
    assert row["total_photo_items"] == 10
    assert row["fallback_items"] == 0
    assert float(row["fallback_rate_pct"]) == pytest.approx(0.0)


def test_photo_fallback_trend_returns_expected_values(
    db_conn, sample_users, sample_household, sample_items
):
    start_date, end_date = _date_range()

    df = _query_df(
        db_conn,
        Q_PHOTO_FALLBACK_TREND,
        {"start_date": start_date, "end_date": end_date},
    )

    row = df.iloc[0]
    assert list(df.columns) == [
        "week_start",
        "total_photo_items",
        "fallback_items",
        "fallback_rate_pct",
    ]
    assert len(df) == 1
    assert row["total_photo_items"] == 10
    assert row["fallback_items"] == 0
    assert float(row["fallback_rate_pct"]) == pytest.approx(0.0)


def test_recommendation_stats_returns_expected_values(
    db_conn, sample_users, sample_household, sample_recommendation_sessions
):
    start_date, end_date = _date_range()

    df = _query_df(
        db_conn,
        Q_RECOMMENDATION_STATS,
        {"start_date": start_date, "end_date": end_date},
    )

    row = df.iloc[0]
    assert list(df.columns) == [
        "week_start",
        "session_count",
        "avg_recipes_shown",
    ]
    assert len(df) == 1
    assert row["session_count"] == 5
    assert float(row["avg_recipes_shown"]) == pytest.approx(5.0)


def test_photo_item_count_returns_expected_count(
    db_conn, sample_users, sample_household, sample_items
):
    start_date, end_date = _date_range()

    df = _query_df(
        db_conn,
        Q_PHOTO_ITEM_COUNT,
        {"start_date": start_date, "end_date": end_date},
    )

    assert list(df.columns) == ["photo_items"]
    assert df.iloc[0]["photo_items"] == 10


def test_barcode_item_count_returns_expected_count(
    db_conn, sample_users, sample_household, sample_items
):
    start_date, end_date = _date_range()

    df = _query_df(
        db_conn,
        Q_BARCODE_ITEM_COUNT,
        {"start_date": start_date, "end_date": end_date},
    )

    assert list(df.columns) == ["barcode_items"]
    assert df.iloc[0]["barcode_items"] == 10


def test_recommendation_session_count_returns_expected_count(
    db_conn, sample_users, sample_household, sample_recommendation_sessions
):
    start_date, end_date = _date_range()

    df = _query_df(
        db_conn,
        Q_RECOMMENDATION_SESSION_COUNT,
        {"start_date": start_date, "end_date": end_date},
    )

    assert list(df.columns) == ["session_count"]
    assert df.iloc[0]["session_count"] == 5


def test_avg_confidence_trend_returns_expected_values(
    db_conn, sample_users, sample_household, sample_items
):
    start_date, end_date = _date_range()

    df = _query_df(
        db_conn,
        Q_AVG_CONFIDENCE_TREND,
        {"start_date": start_date, "end_date": end_date},
    )

    row = df.iloc[0]
    assert list(df.columns) == ["week_start", "avg_confidence", "photo_item_count"]
    assert len(df) == 1
    assert float(row["avg_confidence"]) == pytest.approx(0.8)
    assert row["photo_item_count"] == 10

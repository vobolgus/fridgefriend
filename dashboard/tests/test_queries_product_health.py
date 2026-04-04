# pyright: reportImplicitRelativeImport=false, reportMissingTypeStubs=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnusedParameter=false, reportMissingTypeArgument=false

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from queries.product_health import (
    Q_ACTIVATION_RATE,
    Q_DEVICE_PLATFORMS,
    Q_HOUSEHOLD_SIZE_DISTRIBUTION,
    Q_ITEM_SOURCE_DISTRIBUTION,
    Q_KEY_ACTIONS,
    Q_MAU,
    Q_NOTIFICATION_ADOPTION,
    Q_ONBOARDING_FUNNEL,
    Q_RETENTION_COHORTS,
    Q_SIGNUP_TREND,
    Q_TOTAL_USERS,
    Q_WASTE_RATIO,
    Q_WAU,
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


def test_total_users_returns_expected_count(db_conn, sample_users):
    _, end_date = _date_range()

    df = _query_df(db_conn, Q_TOTAL_USERS, {"end_date": end_date})

    assert list(df.columns) == ["total_users"]
    assert df.iloc[0]["total_users"] == len(sample_users)


def test_signup_trend_returns_signup_dates_and_counts(db_conn, sample_users):
    start_date, end_date = _date_range()

    df = _query_df(
        db_conn,
        Q_SIGNUP_TREND,
        {"start_date": start_date, "end_date": end_date},
    )

    assert list(df.columns) == ["signup_date", "signups"]
    assert len(df) == len(sample_users)
    assert df["signups"].sum() == len(sample_users)
    assert (df["signups"] == 1).all()


def test_onboarding_funnel_returns_all_expected_stages(
    db_conn,
    sample_users,
    sample_household,
    sample_items,
    sample_recommendation_sessions,
    sample_meal_plans,
):
    start_date, end_date = _date_range()

    df = _query_df(
        db_conn,
        Q_ONBOARDING_FUNNEL,
        {"start_date": start_date, "end_date": end_date},
    )

    assert list(df.columns) == ["stage", "user_count"]
    assert df["stage"].tolist() == [
        "Signed Up",
        "Added First Item",
        "Got Recommendation",
        "Created Meal Plan",
    ]

    counts = dict(zip(df["stage"], df["user_count"], strict=True))
    assert counts == {
        "Signed Up": 10,
        "Added First Item": 10,
        "Got Recommendation": 10,
        "Created Meal Plan": 3,
    }


def test_activation_rate_returns_expected_metrics(
    db_conn, sample_users, sample_household, sample_items
):
    start_date, end_date = _date_range()

    df = _query_df(
        db_conn,
        Q_ACTIVATION_RATE,
        {"start_date": start_date, "end_date": end_date},
    )

    row = df.iloc[0]
    assert list(df.columns) == [
        "total_signups",
        "activated_users",
        "activation_rate_pct",
    ]
    assert row["total_signups"] == 10
    assert row["activated_users"] == 3
    assert float(row["activation_rate_pct"]) == pytest.approx(30.0)


def test_wau_returns_expected_active_users(db_conn, sample_users, sample_household, sample_items, sample_events):
    _, end_date = _date_range()

    df = _query_df(db_conn, Q_WAU, {"end_date": end_date})

    assert list(df.columns) == ["wau"]
    assert df.iloc[0]["wau"] == 7


def test_mau_returns_expected_active_users(db_conn, sample_users, sample_household, sample_items, sample_events):
    _, end_date = _date_range()

    df = _query_df(db_conn, Q_MAU, {"end_date": end_date})

    assert list(df.columns) == ["mau"]
    assert df.iloc[0]["mau"] == 7


def test_retention_cohorts_returns_expected_columns_and_values(
    db_conn, sample_users, sample_household, sample_items, sample_events
):
    start_date, end_date = _date_range()

    df = _query_df(
        db_conn,
        Q_RETENTION_COHORTS,
        {"start_date": start_date, "end_date": end_date},
    )

    assert list(df.columns) == [
        "cohort_week",
        "week_number",
        "active_users",
        "cohort_size",
        "retention_pct",
    ]
    assert not df.empty
    assert set(df["week_number"]) >= {0}
    assert (df["week_number"] >= 0).all()
    assert ((df["retention_pct"] >= 0) & (df["retention_pct"] <= 100)).all()


def test_waste_ratio_returns_expected_percentage(db_conn, sample_users, sample_household, sample_items):
    start_date, end_date = _date_range()

    df = _query_df(
        db_conn,
        Q_WASTE_RATIO,
        {"start_date": start_date, "end_date": end_date},
    )

    row = df.iloc[0]
    assert "waste_reduction_pct" in df.columns
    assert row["items_used"] == 10
    assert row["items_discarded"] == 10
    assert row["items_resolved"] == 20
    assert float(row["waste_reduction_pct"]) == pytest.approx(50.0)


def test_key_action_counts_returns_expected_daily_totals(
    db_conn,
    sample_users,
    sample_household,
    sample_items,
    sample_events,
    sample_recommendation_sessions,
    sample_meal_plans,
):
    start_date, end_date = _date_range()

    df = _query_df(
        db_conn,
        Q_KEY_ACTIONS,
        {"start_date": start_date, "end_date": end_date},
    )

    assert list(df.columns) == [
        "action_date",
        "items_added",
        "recommendation_sessions",
        "plans_generated",
    ]
    assert not df.empty
    assert df["items_added"].sum() == 22
    assert df["recommendation_sessions"].sum() == 5
    assert df["plans_generated"].sum() == 3


def test_item_source_distribution_returns_expected_sources(
    db_conn, sample_users, sample_household, sample_items
):
    start_date, end_date = _date_range()

    df = _query_df(
        db_conn,
        Q_ITEM_SOURCE_DISTRIBUTION,
        {"start_date": start_date, "end_date": end_date},
    )

    assert list(df.columns) == ["source", "item_count", "percentage"]
    counts = dict(zip(df["source"], df["item_count"], strict=True))
    assert counts == {"manual": 10, "barcode": 10, "photo": 10}


def test_household_size_distribution_returns_member_and_household_counts(
    db_conn, sample_users, sample_household
):
    df = _query_df(db_conn, Q_HOUSEHOLD_SIZE_DISTRIBUTION)

    assert list(df.columns) == ["member_count", "household_count"]
    assert df.to_dict("records") == [{"member_count": 10, "household_count": 1}]


def test_notification_adoption_returns_expected_percentage(
    db_conn, sample_users, sample_notification_prefs
):
    df = _query_df(db_conn, Q_NOTIFICATION_ADOPTION)

    row = df.iloc[0]
    assert "adoption_pct" in df.columns
    assert row["reminders_enabled"] == 7
    assert row["total_preferences"] == 10
    assert float(row["adoption_pct"]) == pytest.approx(70.0)


def test_device_platforms_returns_expected_distribution(
    db_conn, sample_users, sample_device_tokens
):
    df = _query_df(db_conn, Q_DEVICE_PLATFORMS)

    assert list(df.columns) == ["platform", "device_count"]
    counts = dict(zip(df["platform"], df["device_count"], strict=True))
    assert counts == {"ios": 3, "android": 2}

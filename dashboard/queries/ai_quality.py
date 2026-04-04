from datetime import date

import pandas as pd
import streamlit as st

from db.connection import run_query

Q_AVG_CONFIDENCE = """
SELECT
    ROUND(AVG(confidence)::numeric, 3) AS avg_confidence,
    COUNT(*) AS photo_item_count
FROM inventory_items
WHERE source = 'photo'
  AND created_at BETWEEN :start_date AND :end_date
"""

Q_CONFIDENCE_DISTRIBUTION = """
SELECT
    DATE_TRUNC('week', created_at) AS week_start,
    COUNT(*) FILTER (WHERE confidence >= 0.9) AS high_confidence,
    COUNT(*) FILTER (WHERE confidence >= 0.7 AND confidence < 0.9) AS medium_confidence,
    COUNT(*) FILTER (WHERE confidence >= 0.5 AND confidence < 0.7) AS low_confidence,
    COUNT(*) FILTER (WHERE confidence < 0.5) AS very_low_confidence
FROM inventory_items
WHERE source = 'photo'
  AND created_at BETWEEN :start_date AND :end_date
GROUP BY week_start
ORDER BY week_start
"""

Q_BARCODE_ITEM_TREND = """
SELECT
    DATE_TRUNC('week', created_at) AS week_start,
    COUNT(*) AS barcode_items
FROM inventory_items
WHERE source = 'barcode'
  AND created_at BETWEEN :start_date AND :end_date
GROUP BY week_start
ORDER BY week_start
"""

Q_PHOTO_FALLBACK_RATE = """
SELECT
    COUNT(*) AS total_photo_items,
    COUNT(*) FILTER (WHERE confidence < 0.5) AS fallback_items,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE confidence < 0.5)
        / NULLIF(COUNT(*), 0), 1
    ) AS fallback_rate_pct
FROM inventory_items
WHERE source = 'photo'
  AND created_at BETWEEN :start_date AND :end_date
"""

Q_PHOTO_FALLBACK_TREND = """
SELECT
    DATE_TRUNC('week', created_at) AS week_start,
    COUNT(*) AS total_photo_items,
    COUNT(*) FILTER (WHERE confidence < 0.5) AS fallback_items,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE confidence < 0.5)
        / NULLIF(COUNT(*), 0), 1
    ) AS fallback_rate_pct
FROM inventory_items
WHERE source = 'photo'
  AND created_at BETWEEN :start_date AND :end_date
GROUP BY week_start
ORDER BY week_start
"""

Q_RECOMMENDATION_STATS = """
SELECT
    DATE_TRUNC('week', created_at) AS week_start,
    COUNT(*) AS session_count,
    ROUND(
        AVG(json_array_length(recipes_shown::text::json))::numeric, 1
    ) AS avg_recipes_shown
FROM recommendation_sessions
WHERE created_at BETWEEN :start_date AND :end_date
GROUP BY week_start
ORDER BY week_start
"""

Q_PHOTO_ITEM_COUNT = """
SELECT COUNT(*) AS photo_items
FROM inventory_items
WHERE source = 'photo'
  AND created_at BETWEEN :start_date AND :end_date
"""

Q_BARCODE_ITEM_COUNT = """
SELECT COUNT(*) AS barcode_items
FROM inventory_items
WHERE source = 'barcode'
  AND created_at BETWEEN :start_date AND :end_date
"""

Q_RECOMMENDATION_SESSION_COUNT = """
SELECT COUNT(*) AS session_count
FROM recommendation_sessions
WHERE created_at BETWEEN :start_date AND :end_date
"""

Q_AVG_CONFIDENCE_TREND = """
SELECT
    DATE_TRUNC('week', created_at) AS week_start,
    ROUND(AVG(confidence)::numeric, 3) AS avg_confidence,
    COUNT(*) AS photo_item_count
FROM inventory_items
WHERE source = 'photo'
  AND created_at BETWEEN :start_date AND :end_date
GROUP BY week_start
ORDER BY week_start
"""


@st.cache_data(ttl=300)
def get_avg_confidence(start_date: date, end_date: date) -> pd.DataFrame:
    return run_query(Q_AVG_CONFIDENCE, {"start_date": start_date, "end_date": end_date})


@st.cache_data(ttl=300)
def get_confidence_distribution(start_date: date, end_date: date) -> pd.DataFrame:
    return run_query(
        Q_CONFIDENCE_DISTRIBUTION, {"start_date": start_date, "end_date": end_date}
    )


@st.cache_data(ttl=300)
def get_barcode_item_trend(start_date: date, end_date: date) -> pd.DataFrame:
    return run_query(
        Q_BARCODE_ITEM_TREND, {"start_date": start_date, "end_date": end_date}
    )


@st.cache_data(ttl=300)
def get_photo_fallback_rate(start_date: date, end_date: date) -> pd.DataFrame:
    return run_query(
        Q_PHOTO_FALLBACK_RATE, {"start_date": start_date, "end_date": end_date}
    )


@st.cache_data(ttl=300)
def get_photo_fallback_trend(start_date: date, end_date: date) -> pd.DataFrame:
    return run_query(
        Q_PHOTO_FALLBACK_TREND, {"start_date": start_date, "end_date": end_date}
    )


@st.cache_data(ttl=300)
def get_recommendation_stats(start_date: date, end_date: date) -> pd.DataFrame:
    return run_query(
        Q_RECOMMENDATION_STATS, {"start_date": start_date, "end_date": end_date}
    )


@st.cache_data(ttl=300)
def get_photo_item_count(start_date: date, end_date: date) -> pd.DataFrame:
    return run_query(
        Q_PHOTO_ITEM_COUNT, {"start_date": start_date, "end_date": end_date}
    )


@st.cache_data(ttl=300)
def get_barcode_item_count(start_date: date, end_date: date) -> pd.DataFrame:
    return run_query(
        Q_BARCODE_ITEM_COUNT, {"start_date": start_date, "end_date": end_date}
    )


@st.cache_data(ttl=300)
def get_recommendation_session_count(
    start_date: date, end_date: date
) -> pd.DataFrame:
    return run_query(
        Q_RECOMMENDATION_SESSION_COUNT,
        {"start_date": start_date, "end_date": end_date},
    )


@st.cache_data(ttl=300)
def get_avg_confidence_trend(start_date: date, end_date: date) -> pd.DataFrame:
    return run_query(
        Q_AVG_CONFIDENCE_TREND, {"start_date": start_date, "end_date": end_date}
    )

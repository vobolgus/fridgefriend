from datetime import date

import pandas as pd
import streamlit as st

from db.connection import check_table_exists, run_query

Q_LLM_COST = """
SELECT
    DATE_TRUNC('day', created_at) AS day,
    COUNT(*) AS parse_count,
    SUM(input_tokens) AS total_input_tokens,
    SUM(output_tokens) AS total_output_tokens,
    SUM(cost_usd) AS total_cost_usd,
    ROUND(AVG(cost_usd)::numeric, 4) AS avg_cost_per_parse
FROM ai_inference_log
WHERE provider = 'litellm'
  AND operation = 'photo_parse'
  AND created_at BETWEEN :start_date AND :end_date
GROUP BY day
ORDER BY day
"""

Q_SPOONACULAR_COST = """
SELECT
    DATE_TRUNC('day', created_at) AS day,
    COUNT(*) AS api_calls,
    SUM(api_points_used) AS total_points,
    ROUND(AVG(api_points_used)::numeric, 1) AS avg_points_per_call
FROM ai_inference_log
WHERE provider = 'spoonacular'
  AND created_at BETWEEN :start_date AND :end_date
GROUP BY day
ORDER BY day
"""

Q_TOTAL_COST_TREND = """
SELECT
    DATE_TRUNC('week', created_at) AS week_start,
    provider,
    SUM(cost_usd) AS total_cost_usd,
    COUNT(*) AS call_count
FROM ai_inference_log
WHERE created_at BETWEEN :start_date AND :end_date
  AND cost_usd IS NOT NULL
GROUP BY week_start, provider
ORDER BY week_start, provider
"""

Q_COST_PER_ACTIVE_USER = """
WITH monthly_cost AS (
    SELECT SUM(cost_usd) AS total_cost
    FROM ai_inference_log
    WHERE created_at >= :end_date - INTERVAL '30 days'
      AND created_at <= :end_date
      AND cost_usd IS NOT NULL
),
mau AS (
    SELECT COUNT(DISTINCT user_id) AS active_users
    FROM inventory_events
    WHERE created_at >= :end_date - INTERVAL '30 days'
      AND created_at <= :end_date
)
SELECT
    mc.total_cost,
    m.active_users,
    ROUND((mc.total_cost / NULLIF(m.active_users, 0))::numeric, 4) AS cost_per_active_user
FROM monthly_cost mc, mau m
"""


@st.cache_data(ttl=900)
def get_llm_cost(start_date: date, end_date: date) -> pd.DataFrame:
    if not check_table_exists("ai_inference_log"):
        return pd.DataFrame()
    return run_query(Q_LLM_COST, {"start_date": start_date, "end_date": end_date})


@st.cache_data(ttl=900)
def get_spoonacular_cost(start_date: date, end_date: date) -> pd.DataFrame:
    if not check_table_exists("ai_inference_log"):
        return pd.DataFrame()
    return run_query(
        Q_SPOONACULAR_COST, {"start_date": start_date, "end_date": end_date}
    )


@st.cache_data(ttl=900)
def get_total_cost_trend(start_date: date, end_date: date) -> pd.DataFrame:
    if not check_table_exists("ai_inference_log"):
        return pd.DataFrame()
    return run_query(
        Q_TOTAL_COST_TREND, {"start_date": start_date, "end_date": end_date}
    )


@st.cache_data(ttl=900)
def get_cost_per_active_user(end_date: date) -> pd.DataFrame:
    if not check_table_exists("ai_inference_log"):
        return pd.DataFrame()
    return run_query(Q_COST_PER_ACTIVE_USER, {"end_date": end_date})

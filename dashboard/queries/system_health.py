import os
from datetime import date

import pandas as pd
import streamlit as st

from db.connection import check_table_exists, run_query

BACKEND_HEALTH_URL = os.getenv("BACKEND_HEALTH_URL", "http://backend:8000/health")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


def check_backend_health() -> dict:
    import httpx

    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(BACKEND_HEALTH_URL)
            return {
                "status": "ok",
                "version": resp.json().get("version"),
                "latency_ms": resp.elapsed.total_seconds() * 1000,
            }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_postgres() -> dict:
    try:
        run_query("SELECT 1 AS ok")
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_redis() -> dict:
    import redis as redis_lib

    try:
        r = redis_lib.from_url(REDIS_URL, socket_timeout=3)
        r.ping()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def get_celery_queue_depth() -> int | None:
    import redis as redis_lib

    try:
        r = redis_lib.from_url(REDIS_URL, socket_timeout=3)
        return r.llen("celery")
    except Exception:
        return None


Q_API_LATENCY = """
SELECT
    path,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration_ms) AS p50_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) AS p95_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms) AS p99_ms,
    COUNT(*) AS request_count
FROM api_request_log
WHERE created_at BETWEEN :start_date AND :end_date
GROUP BY path
ORDER BY p95_ms DESC
"""

Q_ERROR_RATE = """
SELECT
    path,
    COUNT(*) FILTER (WHERE status_code >= 400) AS error_count,
    COUNT(*) AS total_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status_code >= 400)
        / NULLIF(COUNT(*), 0), 2
    ) AS error_rate_pct
FROM api_request_log
WHERE created_at BETWEEN :start_date AND :end_date
GROUP BY path
ORDER BY error_rate_pct DESC
"""

Q_THROUGHPUT = """
SELECT
    DATE_TRUNC('minute', created_at) AS time_bucket,
    COUNT(*) AS request_count
FROM api_request_log
WHERE created_at BETWEEN :start_date AND :end_date
GROUP BY time_bucket
ORDER BY time_bucket
"""

Q_LATENCY_TIMESERIES = """
SELECT
    DATE_TRUNC('hour', created_at) AS time_bucket,
    path,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration_ms) AS p50_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) AS p95_ms,
    COUNT(*) AS request_count
FROM api_request_log
WHERE created_at BETWEEN :start_date AND :end_date
GROUP BY time_bucket, path
ORDER BY time_bucket, path
"""


@st.cache_data(ttl=30)
def get_api_latency(start_date: date, end_date: date) -> pd.DataFrame:
    if not check_table_exists("api_request_log"):
        return pd.DataFrame()
    return run_query(Q_API_LATENCY, {"start_date": start_date, "end_date": end_date})


@st.cache_data(ttl=30)
def get_error_rate(start_date: date, end_date: date) -> pd.DataFrame:
    if not check_table_exists("api_request_log"):
        return pd.DataFrame()
    return run_query(Q_ERROR_RATE, {"start_date": start_date, "end_date": end_date})


@st.cache_data(ttl=30)
def get_throughput(start_date: date, end_date: date) -> pd.DataFrame:
    if not check_table_exists("api_request_log"):
        return pd.DataFrame()
    return run_query(Q_THROUGHPUT, {"start_date": start_date, "end_date": end_date})


@st.cache_data(ttl=30)
def get_latency_timeseries(start_date: date, end_date: date) -> pd.DataFrame:
    if not check_table_exists("api_request_log"):
        return pd.DataFrame()
    return run_query(
        Q_LATENCY_TIMESERIES, {"start_date": start_date, "end_date": end_date}
    )

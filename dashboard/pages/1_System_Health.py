import time

import streamlit as st

from components.charts import create_timeseries
from components.filters import render_refresh_controls, render_time_filter
from components.metrics import placeholder_metric, render_metric_card
from db.connection import check_table_exists
from queries.system_health import (
    check_backend_health,
    check_postgres,
    check_redis,
    get_api_latency,
    get_celery_queue_depth,
    get_error_rate,
    get_latency_timeseries,
    get_throughput,
)

st.set_page_config(page_title="System Health", page_icon="🔧", layout="wide")
st.title("System Health")

start_date, end_date = render_time_filter()

# --- KPI row ---
c1, c2, c3, c4 = st.columns(4)

health = check_backend_health()

with c1:
    if health["status"] == "ok":
        render_metric_card("Backend", "UP", delta=f"{health.get('latency_ms', 0):.0f}ms")
    else:
        render_metric_card("Backend", "DOWN")

has_telemetry = check_table_exists("api_request_log")

with c2:
    if has_telemetry:
        lat_df = get_api_latency(start_date, end_date)
        if not lat_df.empty:
            avg_p50 = lat_df["p50_ms"].mean()
            render_metric_card("Avg Latency (P50)", f"{avg_p50:.0f}ms")
        else:
            render_metric_card("Avg Latency", "No data")
    else:
        placeholder_metric("Avg Latency", "api_request_log table")

with c3:
    if has_telemetry:
        err_df = get_error_rate(start_date, end_date)
        if not err_df.empty:
            total_errors = err_df["error_count"].sum()
            total_reqs = err_df["total_count"].sum()
            rate = 100.0 * total_errors / total_reqs if total_reqs else 0
            render_metric_card("Error Rate", f"{rate:.1f}%")
        else:
            render_metric_card("Error Rate", "No data")
    else:
        placeholder_metric("Error Rate", "api_request_log table")

with c4:
    if has_telemetry:
        tp_df = get_throughput(start_date, end_date)
        if not tp_df.empty:
            avg_rpm = tp_df["request_count"].mean()
            render_metric_card("Req/min", f"{avg_rpm:.1f}")
        else:
            render_metric_card("Throughput", "No data")
    else:
        placeholder_metric("Req/sec", "api_request_log table")

st.divider()

# --- Latency timeseries ---
st.subheader("API Latency by Endpoint")
if has_telemetry:
    ts_df = get_latency_timeseries(start_date, end_date)
    if not ts_df.empty:
        st.plotly_chart(
            create_timeseries(ts_df, "time_bucket", ["p50_ms", "p95_ms"], "P50/P95 Latency"),
            use_container_width=True,
        )
    else:
        st.info("No latency data for this time range.")
else:
    st.info(
        "API latency metrics require the `api_request_log` table. "
        "See dashboard_spec.md Section 6.1."
    )

st.divider()

# --- Error rate + throughput ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Error Rate by Endpoint")
    if has_telemetry:
        err_df = get_error_rate(start_date, end_date)
        if not err_df.empty:
            st.dataframe(err_df, use_container_width=True)
        else:
            st.info("No error data for this time range.")
    else:
        st.info("Requires `api_request_log` table.")

with col_right:
    st.subheader("Throughput Over Time")
    if has_telemetry:
        tp_df = get_throughput(start_date, end_date)
        if not tp_df.empty:
            st.plotly_chart(
                create_timeseries(tp_df, "time_bucket", "request_count", "Requests per Minute"),
                use_container_width=True,
            )
        else:
            st.info("No throughput data for this time range.")
    else:
        st.info("Requires `api_request_log` table.")

st.divider()

# --- Infrastructure status ---
st.subheader("Infrastructure Status")
i1, i2, i3, i4 = st.columns(4)

with i1:
    pg = check_postgres()
    render_metric_card("PostgreSQL", "OK" if pg["status"] == "ok" else "ERROR")

with i2:
    rd = check_redis()
    render_metric_card("Redis", "OK" if rd["status"] == "ok" else "ERROR")

with i3:
    depth = get_celery_queue_depth()
    render_metric_card("Celery Queue", str(depth) if depth is not None else "Unknown")

with i4:
    version = health.get("version", "Unknown")
    render_metric_card("Backend Version", version or "Unknown")

# --- Auto-refresh ---
if render_refresh_controls():
    time.sleep(60)
    st.rerun()

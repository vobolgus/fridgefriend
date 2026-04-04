import time

import streamlit as st

from components.charts import create_stacked_area, create_timeseries
from components.filters import render_refresh_controls, render_source_filter, render_time_filter
from components.metrics import placeholder_metric, render_metric_card
from db.connection import check_table_exists
from queries.ai_quality import (
    get_avg_confidence,
    get_avg_confidence_trend,
    get_barcode_item_count,
    get_confidence_distribution,
    get_photo_fallback_rate,
    get_photo_fallback_trend,
    get_photo_item_count,
    get_recommendation_session_count,
    get_recommendation_stats,
)

st.set_page_config(page_title="AI Quality", page_icon="🤖", layout="wide")
st.title("AI Quality")

start_date, end_date = render_time_filter()
render_source_filter()

# --- KPI row ---
c1, c2, c3, c4 = st.columns(4)

with c1:
    df = get_photo_item_count(start_date, end_date)
    val = df.iloc[0]["photo_items"] if not df.empty else 0
    render_metric_card("Photo Items", f"{val:,}")

with c2:
    df = get_avg_confidence(start_date, end_date)
    val = df.iloc[0]["avg_confidence"] if not df.empty and df.iloc[0]["avg_confidence"] is not None else None
    render_metric_card("Avg Confidence", f"{val:.3f}" if val is not None else "N/A")

with c3:
    df = get_barcode_item_count(start_date, end_date)
    val = df.iloc[0]["barcode_items"] if not df.empty else 0
    render_metric_card("Barcode Items", f"{val:,}")

with c4:
    df = get_recommendation_session_count(start_date, end_date)
    val = df.iloc[0]["session_count"] if not df.empty else 0
    render_metric_card("Rec Sessions", f"{val:,}")

st.divider()

# --- Confidence distribution over time ---
st.subheader("Confidence Distribution Over Time")
conf_df = get_confidence_distribution(start_date, end_date)
if not conf_df.empty:
    st.plotly_chart(
        create_stacked_area(
            conf_df,
            "week_start",
            ["high_confidence", "medium_confidence", "low_confidence", "very_low_confidence"],
            "Photo Confidence Buckets by Week",
        ),
        use_container_width=True,
    )
else:
    st.info("No photo item data for this time range.")

st.divider()

# --- Photo parse metrics + recommendation quality ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Photo Parse Metrics")

    trend_df = get_avg_confidence_trend(start_date, end_date)
    if not trend_df.empty:
        st.plotly_chart(
            create_timeseries(trend_df, "week_start", "avg_confidence", "Avg Confidence Trend"),
            use_container_width=True,
        )

    fallback_df = get_photo_fallback_trend(start_date, end_date)
    if not fallback_df.empty:
        st.plotly_chart(
            create_timeseries(
                fallback_df, "week_start", "fallback_rate_pct", "Fallback Rate Trend"
            ),
            use_container_width=True,
        )

    rate_df = get_photo_fallback_rate(start_date, end_date)
    if not rate_df.empty:
        row = rate_df.iloc[0]
        pct = row["fallback_rate_pct"]
        render_metric_card(
            "Fallback Rate",
            f"{pct}%" if pct is not None else "N/A",
            delta=f"{row['fallback_items']}/{row['total_photo_items']} items",
        )

with col_right:
    st.subheader("Recommendation Quality")
    rec_df = get_recommendation_stats(start_date, end_date)
    if not rec_df.empty:
        st.plotly_chart(
            create_timeseries(
                rec_df, "week_start", "avg_recipes_shown", "Avg Recipes Shown per Session"
            ),
            use_container_width=True,
        )
    else:
        st.info("No recommendation session data.")

st.divider()

# --- Requires instrumentation ---
st.subheader("Requires Instrumentation")
col_left, col_right = st.columns(2)
with col_left:
    if check_table_exists("ai_inference_log"):
        st.info("LLM latency data available.")
    else:
        placeholder_metric("LLM Response Latency", "ai_inference_log table")

with col_right:
    placeholder_metric("Avg Coverage %", "scoring data persistence in recommendation_sessions")

# --- Auto-refresh ---
if render_refresh_controls():
    time.sleep(60)
    st.rerun()

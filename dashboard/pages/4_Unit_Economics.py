import time

import streamlit as st

from components.charts import create_timeseries
from components.filters import render_refresh_controls, render_time_filter
from components.metrics import placeholder_metric, render_metric_card
from db.connection import check_table_exists
from queries.unit_economics import (
    get_cost_per_active_user,
    get_llm_cost,
    get_spoonacular_cost,
    get_total_cost_trend,
)

st.set_page_config(page_title="Unit Economics", page_icon="💰", layout="wide")
st.title("Unit Economics")

start_date, end_date = render_time_filter()

has_data = check_table_exists("ai_inference_log")

# --- KPI row ---
c1, c2, c3 = st.columns(3)

with c1:
    if has_data:
        df = get_llm_cost(start_date, end_date)
        if not df.empty:
            total = df["total_cost_usd"].sum()
            render_metric_card("LLM Cost", f"${total:.2f}")
        else:
            render_metric_card("LLM Cost", "$0.00")
    else:
        placeholder_metric("LLM Cost", "ai_inference_log table")

with c2:
    if has_data:
        df = get_spoonacular_cost(start_date, end_date)
        if not df.empty:
            total_points = df["total_points"].sum()
            render_metric_card("Spoonacular Points", f"{total_points:,.0f}")
        else:
            render_metric_card("Spoonacular Points", "0")
    else:
        placeholder_metric("Spoonacular Cost", "ai_inference_log table")

with c3:
    if has_data:
        df = get_cost_per_active_user(end_date)
        if not df.empty and df.iloc[0]["cost_per_active_user"] is not None:
            val = df.iloc[0]["cost_per_active_user"]
            render_metric_card("Cost / Active User", f"${val:.4f}")
        else:
            render_metric_card("Cost / Active User", "N/A")
    else:
        placeholder_metric("Cost / Active User", "ai_inference_log table")

st.divider()

# --- Cost trend ---
st.subheader("Cost Trend Over Time")
if has_data:
    trend_df = get_total_cost_trend(start_date, end_date)
    if not trend_df.empty:
        st.plotly_chart(
            create_timeseries(trend_df, "week_start", "total_cost_usd", "Weekly Cost"),
            use_container_width=True,
        )
    else:
        st.info("No cost data for this time range.")
else:
    st.info(
        "All Unit Economics metrics require the `ai_inference_log` table. "
        "See dashboard_spec.md Section 6.2 for instrumentation instructions."
    )

st.divider()

# --- Per-call breakdowns ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("LLM Cost per Photo Parse")
    if has_data:
        llm_df = get_llm_cost(start_date, end_date)
        if not llm_df.empty:
            st.plotly_chart(
                create_timeseries(llm_df, "day", "avg_cost_per_parse", "Avg Cost per Parse"),
                use_container_width=True,
            )
        else:
            st.info("No LLM cost data.")
    else:
        placeholder_metric("Cost per Parse", "ai_inference_log table")

with col_right:
    st.subheader("Spoonacular Points per Call")
    if has_data:
        sp_df = get_spoonacular_cost(start_date, end_date)
        if not sp_df.empty:
            st.plotly_chart(
                create_timeseries(sp_df, "day", "avg_points_per_call", "Avg Points per Call"),
                use_container_width=True,
            )
        else:
            st.info("No Spoonacular cost data.")
    else:
        placeholder_metric("Points per Call", "ai_inference_log table")

# --- Auto-refresh ---
if render_refresh_controls():
    time.sleep(60)
    st.rerun()

import time

import streamlit as st

from components.charts import (
    create_funnel_chart,
    create_pie_chart,
    create_retention_heatmap,
    create_timeseries,
)
from components.filters import render_refresh_controls, render_source_filter, render_time_filter
from components.metrics import render_metric_card
from queries.product_health import (
    get_activation_rate,
    get_device_platforms,
    get_household_size_distribution,
    get_item_source_distribution,
    get_key_action_counts,
    get_notification_adoption,
    get_onboarding_funnel,
    get_retention_cohorts,
    get_signup_trend,
    get_total_users,
    get_waste_ratio,
    get_wau,
)

st.set_page_config(page_title="Product Health", page_icon="📈", layout="wide")
st.title("Product Health")

start_date, end_date = render_time_filter()
render_source_filter()

# --- KPI row ---
c1, c2, c3, c4 = st.columns(4)

with c1:
    df = get_total_users(end_date)
    render_metric_card("Total Users", f"{df.iloc[0]['total_users']:,}" if not df.empty else "0")

with c2:
    df = get_wau(end_date)
    render_metric_card("WAU", f"{df.iloc[0]['wau']:,}" if not df.empty else "0")

with c3:
    df = get_activation_rate(start_date, end_date)
    pct = df.iloc[0]["activation_rate_pct"] if not df.empty else None
    render_metric_card("Activation Rate", f"{pct}%" if pct is not None else "N/A")

with c4:
    df = get_waste_ratio(start_date, end_date)
    pct = df.iloc[0]["waste_reduction_pct"] if not df.empty else None
    render_metric_card("Waste Reduction", f"{pct}%" if pct is not None else "N/A")

st.divider()

# --- Onboarding funnel ---
st.subheader("Onboarding Funnel")
funnel_df = get_onboarding_funnel(start_date, end_date)
if not funnel_df.empty:
    st.plotly_chart(
        create_funnel_chart(funnel_df, "stage", "user_count", "User Onboarding Funnel"),
        use_container_width=True,
    )
else:
    st.info("No funnel data for this time range.")

st.divider()

# --- Retention + signup trend ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Retention Cohorts")
    cohorts_df = get_retention_cohorts(start_date, end_date)
    if not cohorts_df.empty:
        st.plotly_chart(create_retention_heatmap(cohorts_df), use_container_width=True)
    else:
        st.info("No retention data for this time range.")

with col_right:
    st.subheader("Signup Trend")
    signup_df = get_signup_trend(start_date, end_date)
    if not signup_df.empty:
        st.plotly_chart(
            create_timeseries(signup_df, "signup_date", "signups", "Daily Signups"),
            use_container_width=True,
        )
    else:
        st.info("No signup data for this time range.")

st.divider()

# --- Item source + household size ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Item Source Distribution")
    source_df = get_item_source_distribution(start_date, end_date)
    if not source_df.empty:
        st.plotly_chart(
            create_pie_chart(source_df, "source", "item_count", "Item Sources"),
            use_container_width=True,
        )
    else:
        st.info("No item data for this time range.")

with col_right:
    st.subheader("Household Size Distribution")
    hh_df = get_household_size_distribution()
    if not hh_df.empty:
        st.bar_chart(hh_df.set_index("member_count")["household_count"])
    else:
        st.info("No household data available.")

st.divider()

# --- Key actions ---
st.subheader("Key Action Counts")
actions_df = get_key_action_counts(start_date, end_date)
if not actions_df.empty:
    st.plotly_chart(
        create_timeseries(
            actions_df,
            "action_date",
            ["items_added", "recommendation_sessions", "plans_generated"],
            "Daily Key Actions",
        ),
        use_container_width=True,
    )
else:
    st.info("No action data for this time range.")

st.divider()

# --- Notifications + devices ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Notification Adoption")
    notif_df = get_notification_adoption()
    if not notif_df.empty:
        row = notif_df.iloc[0]
        render_metric_card(
            "Reminders Enabled",
            f"{row['adoption_pct']}%" if row["adoption_pct"] is not None else "N/A",
            delta=f"{row['reminders_enabled']}/{row['total_preferences']} users",
        )
    else:
        st.info("No notification preference data.")

with col_right:
    st.subheader("Device Registrations")
    device_df = get_device_platforms()
    if not device_df.empty:
        st.plotly_chart(
            create_pie_chart(device_df, "platform", "device_count", "Platforms"),
            use_container_width=True,
        )
    else:
        st.info("No device token data.")

# --- Auto-refresh ---
if render_refresh_controls():
    time.sleep(60)
    st.rerun()

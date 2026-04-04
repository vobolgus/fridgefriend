from datetime import date, datetime, timedelta

import streamlit as st

PRESET_DAYS = {
    "Last 24h": 1,
    "Last 7 days": 7,
    "Last 30 days": 30,
    "Last 90 days": 90,
}


def render_time_filter() -> tuple[date, date]:
    st.sidebar.header("Filters")
    preset = st.sidebar.selectbox(
        "Time Range",
        [*PRESET_DAYS.keys(), "Custom"],
        index=2,
        key="time_preset",
    )
    now = datetime.utcnow()
    if preset == "Custom":
        start = st.sidebar.date_input(
            "Start", value=now - timedelta(days=30), key="filter_start"
        )
        end = st.sidebar.date_input("End", value=now.date(), key="filter_end")
    else:
        start = (now - timedelta(days=PRESET_DAYS[preset])).date()
        end = now.date()
    return start, end


def render_source_filter() -> str | None:
    source = st.sidebar.selectbox(
        "Item Source",
        ["All", "manual", "barcode", "photo"],
        key="source_filter",
    )
    return None if source == "All" else source


def render_refresh_controls() -> bool:
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Refresh", key="refresh_btn"):
            st.cache_data.clear()
            st.rerun()
    with col2:
        auto_refresh = st.checkbox("Auto (60s)", key="auto_refresh")
    return auto_refresh

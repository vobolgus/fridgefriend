import streamlit as st

from db.connection import check_table_exists


def render_metric_card(label: str, value, delta: str | None = None):
    st.metric(label=label, value=value, delta=delta)


def placeholder_metric(title: str, requires: str):
    st.metric(label=title, value="--")
    st.caption(f"Requires: {requires}")


def render_metric_or_placeholder(
    label: str,
    value_fn,
    requires_table: str | None = None,
    requires_label: str = "",
):
    if requires_table and not check_table_exists(requires_table):
        placeholder_metric(label, requires_label or f"{requires_table} table")
        return
    try:
        value = value_fn()
        render_metric_card(label, value)
    except Exception:
        placeholder_metric(label, "data unavailable")

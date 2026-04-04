"""FridgeFriend Analytics Dashboard — Home Page."""

import streamlit as st

st.set_page_config(
    page_title="FridgeFriend Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("FridgeFriend Analytics Dashboard")

st.markdown(
    """
Welcome to the **FridgeFriend internal analytics dashboard**.

Use the sidebar to navigate between views:

- **System Health** — API uptime, latency, error rates, infrastructure status
- **Product Health** — User growth, retention cohorts, onboarding funnel, waste reduction
- **AI Quality** — Photo parse confidence, barcode success, recommendation quality
- **Unit Economics** — LLM costs, Spoonacular API costs, cost per active user
"""
)

st.divider()

st.subheader("North Star Metric")
st.info(
    "**Food Waste Reduction Ratio** = items used / (items used + items discarded). "
    "Track this on the Product Health page."
)

from datetime import date

import pandas as pd
import streamlit as st

from db.connection import run_query

Q_TOTAL_USERS = """
SELECT COUNT(*) AS total_users
FROM users
WHERE created_at <= :end_date
"""

Q_SIGNUP_TREND = """
SELECT
    DATE_TRUNC('day', created_at) AS signup_date,
    COUNT(*) AS signups
FROM users
WHERE created_at BETWEEN :start_date AND :end_date
GROUP BY signup_date
ORDER BY signup_date
"""

Q_ONBOARDING_FUNNEL = """
WITH cohort AS (
    SELECT id AS user_id, created_at
    FROM users
    WHERE created_at BETWEEN :start_date AND :end_date
),
first_item AS (
    SELECT DISTINCT ii.user_id
    FROM inventory_items ii
    INNER JOIN cohort c ON ii.user_id = c.user_id
),
first_recommendation AS (
    SELECT DISTINCT hm.user_id
    FROM recommendation_sessions rs
    INNER JOIN household_members hm
        ON rs.household_id = hm.household_id AND hm.is_active = true
    INNER JOIN cohort c ON hm.user_id = c.user_id
),
first_plan AS (
    SELECT DISTINCT mp.user_id
    FROM meal_plans mp
    INNER JOIN cohort c ON mp.user_id = c.user_id
)
SELECT 'Signed Up' AS stage, COUNT(*) AS user_count FROM cohort
UNION ALL
SELECT 'Added First Item', COUNT(*) FROM first_item
UNION ALL
SELECT 'Got Recommendation', COUNT(*) FROM first_recommendation
UNION ALL
SELECT 'Created Meal Plan', COUNT(*) FROM first_plan
"""

Q_ACTIVATION_RATE = """
WITH cohort AS (
    SELECT id AS user_id, created_at AS signup_at
    FROM users
    WHERE created_at BETWEEN :start_date AND :end_date
),
activated AS (
    SELECT DISTINCT c.user_id
    FROM cohort c
    INNER JOIN inventory_items ii ON ii.user_id = c.user_id
    WHERE ii.created_at <= c.signup_at + INTERVAL '24 hours'
)
SELECT
    (SELECT COUNT(*) FROM cohort) AS total_signups,
    (SELECT COUNT(*) FROM activated) AS activated_users,
    ROUND(
        100.0 * (SELECT COUNT(*) FROM activated)
        / NULLIF((SELECT COUNT(*) FROM cohort), 0), 1
    ) AS activation_rate_pct
"""

Q_WAU = """
SELECT COUNT(DISTINCT user_id) AS wau
FROM inventory_events
WHERE created_at >= :end_date - INTERVAL '7 days'
  AND created_at <= :end_date
"""

Q_MAU = """
SELECT COUNT(DISTINCT user_id) AS mau
FROM inventory_events
WHERE created_at >= :end_date - INTERVAL '30 days'
  AND created_at <= :end_date
"""

Q_WAU_TREND = """
SELECT
    DATE_TRUNC('week', created_at) AS week_start,
    COUNT(DISTINCT user_id) AS active_users
FROM inventory_events
WHERE created_at BETWEEN :start_date AND :end_date
GROUP BY week_start
ORDER BY week_start
"""

Q_RETENTION_COHORTS = """
WITH cohort AS (
    SELECT
        id AS user_id,
        DATE_TRUNC('week', created_at) AS cohort_week
    FROM users
    WHERE created_at BETWEEN :start_date AND :end_date
),
activity AS (
    SELECT
        ie.user_id,
        DATE_TRUNC('week', ie.created_at) AS activity_week
    FROM inventory_events ie
    INNER JOIN cohort c ON ie.user_id = c.user_id
),
retention AS (
    SELECT
        c.cohort_week,
        EXTRACT(DAYS FROM (a.activity_week - c.cohort_week))::int / 7 AS week_number,
        COUNT(DISTINCT a.user_id) AS active_users
    FROM cohort c
    INNER JOIN activity a ON c.user_id = a.user_id
    GROUP BY c.cohort_week, week_number
),
cohort_sizes AS (
    SELECT cohort_week, COUNT(DISTINCT user_id) AS cohort_size
    FROM cohort
    GROUP BY cohort_week
)
SELECT
    r.cohort_week,
    r.week_number,
    r.active_users,
    cs.cohort_size,
    ROUND(100.0 * r.active_users / NULLIF(cs.cohort_size, 0), 1) AS retention_pct
FROM retention r
JOIN cohort_sizes cs ON r.cohort_week = cs.cohort_week
ORDER BY r.cohort_week, r.week_number
"""

Q_WASTE_RATIO = """
SELECT
    COUNT(*) FILTER (WHERE status = 'used') AS items_used,
    COUNT(*) FILTER (WHERE status = 'discarded') AS items_discarded,
    COUNT(*) FILTER (WHERE status IN ('used', 'discarded')) AS items_resolved,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'used')
        / NULLIF(COUNT(*) FILTER (WHERE status IN ('used', 'discarded')), 0),
    1) AS waste_reduction_pct
FROM inventory_items
WHERE updated_at BETWEEN :start_date AND :end_date
  AND status IN ('used', 'discarded')
"""

Q_WASTE_RATIO_TREND = """
SELECT
    DATE_TRUNC('week', updated_at) AS week_start,
    COUNT(*) FILTER (WHERE status = 'used') AS used,
    COUNT(*) FILTER (WHERE status = 'discarded') AS discarded,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'used')
        / NULLIF(COUNT(*) FILTER (WHERE status IN ('used', 'discarded')), 0),
    1) AS waste_reduction_pct
FROM inventory_items
WHERE updated_at BETWEEN :start_date AND :end_date
  AND status IN ('used', 'discarded')
GROUP BY week_start
ORDER BY week_start
"""

Q_KEY_ACTIONS = """
SELECT
    d.day::date AS action_date,
    COALESCE(items.cnt, 0) AS items_added,
    COALESCE(recs.cnt, 0) AS recommendation_sessions,
    COALESCE(plans.cnt, 0) AS plans_generated
FROM generate_series(CAST(:start_date AS date), CAST(:end_date AS date), '1 day'::interval) AS d(day)
LEFT JOIN (
    SELECT DATE_TRUNC('day', created_at)::date AS day, COUNT(*) AS cnt
    FROM inventory_events
    WHERE action = 'added'
      AND created_at BETWEEN :start_date AND :end_date
    GROUP BY 1
) items ON d.day::date = items.day
LEFT JOIN (
    SELECT DATE_TRUNC('day', created_at)::date AS day, COUNT(*) AS cnt
    FROM recommendation_sessions
    WHERE created_at BETWEEN :start_date AND :end_date
    GROUP BY 1
) recs ON d.day::date = recs.day
LEFT JOIN (
    SELECT DATE_TRUNC('day', created_at)::date AS day, COUNT(*) AS cnt
    FROM meal_plans
    WHERE created_at BETWEEN :start_date AND :end_date
    GROUP BY 1
) plans ON d.day::date = plans.day
ORDER BY action_date
"""

Q_ITEM_SOURCE_DISTRIBUTION = """
SELECT
    source,
    COUNT(*) AS item_count,
    ROUND(100.0 * COUNT(*) / NULLIF(SUM(COUNT(*)) OVER(), 0), 1) AS percentage
FROM inventory_items
WHERE created_at BETWEEN :start_date AND :end_date
GROUP BY source
ORDER BY item_count DESC
"""

Q_HOUSEHOLD_SIZE_DISTRIBUTION = """
SELECT
    member_count,
    COUNT(*) AS household_count
FROM (
    SELECT household_id, COUNT(*) AS member_count
    FROM household_members
    WHERE is_active = true
    GROUP BY household_id
) hh_sizes
GROUP BY member_count
ORDER BY member_count
"""

Q_NOTIFICATION_ADOPTION = """
SELECT
    COUNT(*) FILTER (WHERE expiry_reminder_enabled = true) AS reminders_enabled,
    COUNT(*) AS total_preferences,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE expiry_reminder_enabled = true)
        / NULLIF(COUNT(*), 0), 1
    ) AS adoption_pct
FROM notification_preferences
"""

Q_DEVICE_PLATFORMS = """
SELECT
    platform,
    COUNT(*) AS device_count
FROM device_tokens
GROUP BY platform
ORDER BY device_count DESC
"""


@st.cache_data(ttl=300)
def get_total_users(end_date: date) -> pd.DataFrame:
    return run_query(Q_TOTAL_USERS, {"end_date": end_date})


@st.cache_data(ttl=300)
def get_signup_trend(start_date: date, end_date: date) -> pd.DataFrame:
    return run_query(Q_SIGNUP_TREND, {"start_date": start_date, "end_date": end_date})


@st.cache_data(ttl=300)
def get_onboarding_funnel(start_date: date, end_date: date) -> pd.DataFrame:
    return run_query(
        Q_ONBOARDING_FUNNEL, {"start_date": start_date, "end_date": end_date}
    )


@st.cache_data(ttl=300)
def get_activation_rate(start_date: date, end_date: date) -> pd.DataFrame:
    return run_query(
        Q_ACTIVATION_RATE, {"start_date": start_date, "end_date": end_date}
    )


@st.cache_data(ttl=300)
def get_wau(end_date: date) -> pd.DataFrame:
    return run_query(Q_WAU, {"end_date": end_date})


@st.cache_data(ttl=300)
def get_mau(end_date: date) -> pd.DataFrame:
    return run_query(Q_MAU, {"end_date": end_date})


@st.cache_data(ttl=300)
def get_wau_trend(start_date: date, end_date: date) -> pd.DataFrame:
    return run_query(Q_WAU_TREND, {"start_date": start_date, "end_date": end_date})


@st.cache_data(ttl=300)
def get_retention_cohorts(start_date: date, end_date: date) -> pd.DataFrame:
    return run_query(
        Q_RETENTION_COHORTS, {"start_date": start_date, "end_date": end_date}
    )


@st.cache_data(ttl=300)
def get_waste_ratio(start_date: date, end_date: date) -> pd.DataFrame:
    return run_query(Q_WASTE_RATIO, {"start_date": start_date, "end_date": end_date})


@st.cache_data(ttl=300)
def get_waste_ratio_trend(start_date: date, end_date: date) -> pd.DataFrame:
    return run_query(
        Q_WASTE_RATIO_TREND, {"start_date": start_date, "end_date": end_date}
    )


@st.cache_data(ttl=300)
def get_key_action_counts(start_date: date, end_date: date) -> pd.DataFrame:
    return run_query(Q_KEY_ACTIONS, {"start_date": start_date, "end_date": end_date})


@st.cache_data(ttl=300)
def get_item_source_distribution(
    start_date: date, end_date: date
) -> pd.DataFrame:
    return run_query(
        Q_ITEM_SOURCE_DISTRIBUTION,
        {"start_date": start_date, "end_date": end_date},
    )


@st.cache_data(ttl=300)
def get_household_size_distribution() -> pd.DataFrame:
    return run_query(Q_HOUSEHOLD_SIZE_DISTRIBUTION)


@st.cache_data(ttl=300)
def get_notification_adoption() -> pd.DataFrame:
    return run_query(Q_NOTIFICATION_ADOPTION)


@st.cache_data(ttl=300)
def get_device_platforms() -> pd.DataFrame:
    return run_query(Q_DEVICE_PLATFORMS)

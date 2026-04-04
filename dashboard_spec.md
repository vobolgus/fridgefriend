# FridgeFriend Internal Analytics Dashboard — Implementation Specification

**Version:** 1.0
**Date:** 2026-04-04
**Status:** Implementation-ready
**Author:** Engineering

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Technical Architecture](#2-technical-architecture)
3. [Data Source Audit](#3-data-source-audit)
4. [Dashboard Views](#4-dashboard-views)
5. [SQL Query Catalog](#5-sql-query-catalog)
6. [Missing Telemetry Schemas](#6-missing-telemetry-schemas)
7. [Cross-Cutting Filters & UX](#7-cross-cutting-filters--ux)
8. [TDD Testing Strategy](#8-tdd-testing-strategy)
9. [Atomic Commit Strategy](#9-atomic-commit-strategy)
10. [Work Plan](#10-work-plan)

---

## 1. Executive Summary

### 1.1 Purpose

An internal Streamlit-based analytics dashboard for FridgeFriend that provides four unified views: **System Health**, **Product Health**, **AI Quality**, and **Unit Economics / Cost Observability**. The dashboard reads directly from the production PostgreSQL database (read-only) and deploys as a Docker Compose service alongside the existing stack.

### 1.2 North Star Metric

**Food waste reduction ratio** = `COUNT(items WHERE status='used') / COUNT(items WHERE status IN ('used','discarded'))` — derived from `inventory_items` table, `status` column (`InventoryStatus` enum: `active|used|discarded|frozen`, defined in `backend/app/models/inventory_item.py:16-20`).

### 1.3 Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Framework | Streamlit 1.x (Python) | Same language as backend (Python 3.12); low-code dashboarding; internal-only audience |
| Charts | Plotly | Rich interactive charts; funnel/heatmap support; Streamlit-native integration via `st.plotly_chart` |
| Data access | Direct PostgreSQL reads via SQLAlchemy (sync, read-only) | No API layer needed for internal tool; simplifies architecture; same DB instance is fine for local dev/prototype |
| Deployment | Docker Compose service (`dashboard`) | Collocated with existing stack; shared `db` network; no additional infra |
| Auth | None (internal network only) | Dashboard is behind internal network; no external exposure; keep it simple |
| Caching | `@st.cache_data` with TTL per query class | Prevents redundant DB hits; per-query TTL based on freshness needs |
| Connection pool | SQLAlchemy `QueuePool` via `@st.cache_resource` | Single engine shared across Streamlit sessions |
| WAU/MAU definition | Based on `inventory_events` table | Active users who actually do things (add items, change status) are more meaningful than passive analytics events |
| Phase priority | Product Health first | Highest-value view with the most existing/derivable data |

### 1.4 Spec vs Repository Conflicts

| Conflict | Spec Says | Repository Reality | Resolution |
|----------|-----------|-------------------|------------|
| Recipe view/click events | Expected in analytics_events | `recipe_selected_id` in `recommendation_sessions` is always NULL (`backend/app/modules/recommendations/service.py:78-88`); no recipe view/save/cook events exist | Dashboard shows recommendation session counts only; recipe engagement tracked as "Missing" telemetry |
| API latency metrics | Expected per-endpoint P50/P95 | No request logging middleware exists in `backend/app/main.py:44-51` | New `api_request_log` table + middleware required (Section 6) |
| LLM token usage | Expected per photo parse | `LLMPhotoParser` in `backend/app/modules/catalog/photo_interfaces.py:33-139` does NOT extract or log token counts from LLM responses | New `ai_inference_log` table required (Section 6) |
| Push notification delivery | Expected delivery/open tracking | `FCMPushService` in `backend/app/modules/notifications/push.py` returns bool only; no delivery receipts tracked | Shown as "Missing"; notification count from Celery task return value is available |
| Sentry traces | Expected for latency data | `traces_sample_rate=0.0` in `backend/app/main.py:33` | Cannot derive latency from Sentry; dedicated middleware needed |
| Spoonacular cost | Expected API point tracking | `SpoonacularClient` in `backend/app/modules/recommendations/spoonacular.py` does not track API points | New `ai_inference_log` entry per Spoonacular call required |

### 1.5 Assumptions

1. **[A-1]** Dashboard connects to the same PostgreSQL instance as the backend (`postgresql+asyncpg://fridgefriend:fridgefriend@db:5432/fridgefriend` from `docker-compose.yml:13`); dashboard uses synchronous driver (`psycopg2`). Same-instance access is acceptable for this local dev/prototype project.
2. **[A-2]** Dashboard is internal-only; no authentication layer required. Keep it simple.
3. **[A-3]** Read-only access; no writes to production database from dashboard.
4. **[A-4]** Health endpoint polling (`GET /health`) runs from the dashboard container at 30s intervals for uptime tracking.
5. **[A-5]** Redis connectivity is checked via `REDIS_URL` from `backend/app/core/config.py:11`.
6. **[A-6]** New telemetry tables (`api_request_log`, `ai_inference_log`) will be created via SQLAlchemy `Base.metadata.create_all` in the backend lifespan hook (`backend/app/main.py:38-41`).
7. **[A-7]** Celery queue depth is readable via Redis keys (Celery uses Redis as broker per `backend/app/core/celery_app.py`).
8. **[A-8]** The `analytics_events` table (`backend/app/models/events.py:31-40`) stores product events with flexible `event_type` + `payload` JSON; new event types can be added without schema migration.
9. **[A-9]** Barcode miss events are not logged; only successfully created barcode items exist in `inventory_items`. Dashboard shows successful barcode items only until `analytics_events` captures `barcode_scan_attempted` events.
10. **[A-10]** Confidence < 0.5 indicates fallback to editable draft. The product spec states "Photo parsing confidence drives whether to show full auto-fill or partial editable draft." This threshold is confirmed as correct.

---

## 2. Technical Architecture

### 2.1 Directory Structure

```
dashboard/
├── Home.py                          # Streamlit entry point + page router
├── Dockerfile                       # Dashboard container
├── requirements.txt                 # Python dependencies
├── .streamlit/
│   └── config.toml                  # Streamlit server settings
├── pages/
│   ├── 1_System_Health.py           # System Health view
│   ├── 2_Product_Health.py          # Product Health view
│   ├── 3_AI_Quality.py              # AI Quality view
│   └── 4_Unit_Economics.py          # Unit Economics view
├── components/
│   ├── __init__.py
│   ├── filters.py                   # Shared time range, segment, source filters
│   ├── metrics.py                   # KPI card rendering helpers
│   └── charts.py                    # Reusable Plotly chart builders (funnel, cohort, timeseries)
├── queries/
│   ├── __init__.py
│   ├── system_health.py             # System health SQL queries
│   ├── product_health.py            # Product metrics SQL queries
│   ├── ai_quality.py                # AI quality SQL queries
│   └── unit_economics.py            # Cost observability SQL queries
├── db/
│   ├── __init__.py
│   └── connection.py                # SQLAlchemy engine + cached connection
└── tests/
    ├── __init__.py
    ├── conftest.py                  # Pytest fixtures (test DB, sample data factories)
    ├── test_queries_system_health.py
    ├── test_queries_product_health.py
    ├── test_queries_ai_quality.py
    ├── test_queries_unit_economics.py
    ├── test_components_charts.py
    ├── test_components_filters.py
    └── test_pages_smoke.py          # Streamlit AppTest smoke tests
```

### 2.2 Docker Compose Integration

New service added to `docker-compose.yml` (alongside existing `backend`, `db`, `redis`, `localstack`):

```yaml
  dashboard:
    build:
      context: .
      dockerfile: dashboard/Dockerfile
    ports:
      - "8501:8501"
    depends_on:
      - db
      - redis
      - backend
    environment:
      DATABASE_URL: postgresql://fridgefriend:fridgefriend@db:5432/fridgefriend
      REDIS_URL: redis://redis:6379/0
      BACKEND_HEALTH_URL: http://backend:8000/health
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
```

**Note:** Dashboard uses synchronous PostgreSQL driver (`postgresql://` not `postgresql+asyncpg://`) since Streamlit runs synchronously. The existing `docker-compose.yml:13` uses `postgresql+asyncpg://` for the async FastAPI backend.

### 2.3 Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY dashboard/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dashboard/ .

RUN useradd -m dashuser && chown -R dashuser:dashuser /app
USER dashuser

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "Home.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true", \
    "--browser.gatherUsageStats=false"]
```

### 2.4 Dependencies (`requirements.txt`)

```
streamlit>=1.40.0,<2.0
plotly>=5.24.0,<6.0
sqlalchemy>=2.0.36,<3.0
psycopg2-binary>=2.9.9,<3.0
pandas>=2.2.0,<3.0
redis>=5.0.0,<6.0
httpx>=0.28.0,<1.0
pytest>=8.0.0
```

### 2.5 Streamlit Config (`.streamlit/config.toml`)

```toml
[server]
headless = true
port = 8501
address = "0.0.0.0"
runOnSave = false
maxUploadSize = 5

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#4CAF50"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F5F5F5"
textColor = "#212121"
```

### 2.6 Database Connection (`db/connection.py`)

```python
import os

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://fridgefriend:fridgefriend@localhost:5432/fridgefriend",
)


@st.cache_resource
def get_engine():
    """Create a single SQLAlchemy engine shared across all Streamlit sessions."""
    return create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=3,
        max_overflow=5,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


def run_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Execute a read-only SQL query and return a DataFrame."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql_query(text(sql), conn, params=params or {})


def check_table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    try:
        df = run_query(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :name)",
            {"name": table_name},
        )
        return bool(df.iloc[0, 0])
    except Exception:
        return False
```

### 2.7 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Compose Network                        │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────────────┐    │
│  │   backend    │    │     db      │    │      redis       │    │
│  │  (FastAPI)   │───>│ (Postgres   │<───│   (Redis 7)      │    │
│  │  port 8000   │    │   16)       │    │   port 6379      │    │
│  └──────┬───────┘    │  port 5432  │    └──────────────────┘    │
│         │            └──────┬──────┘              ^              │
│         │ GET /health       │ read-only           │              │
│         │                   │                     │ queue depth  │
│  ┌──────v───────────────────v─────────────────────┴──────┐      │
│  │              dashboard (Streamlit)                      │      │
│  │              port 8501                                  │      │
│  │  ┌────────────┐ ┌────────────┐ ┌──────────┐           │      │
│  │  │ System     │ │ Product    │ │ AI       │           │      │
│  │  │ Health     │ │ Health     │ │ Quality  │           │      │
│  │  └────────────┘ └────────────┘ └──────────┘           │      │
│  │  ┌────────────┐ ┌─────────────────────────┐           │      │
│  │  │ Unit       │ │ Shared: filters,        │           │      │
│  │  │ Economics  │ │ charts, db connection    │           │      │
│  │  └────────────┘ └─────────────────────────┘           │      │
│  └────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Source Audit

### 3.1 Metric Classification Matrix

Each metric is classified as:
- **E** (Existing) — Queryable now from existing tables
- **D** (Derivable) — Computable from existing data with SQL joins/aggregations
- **M** (Missing) — Requires new instrumentation before it can be shown

| # | Metric | Class | Source Table(s) | Column(s) / Logic |
|---|--------|-------|-----------------|-------------------|
| **System Health** | | | | |
| S1 | API uptime | M | Requires health endpoint polling | `GET /health` response tracking from dashboard process |
| S2 | API latency per endpoint P50/P95 | M | `api_request_log` (new) | `duration_ms`, `path` |
| S3 | Error rate per endpoint | M | `api_request_log` (new) | `status_code >= 400` / total |
| S4 | Throughput (req/sec) | M | `api_request_log` (new) | `COUNT(*) / time_bucket` |
| S5 | Celery queue depth | M | Redis key inspection | `celery` broker queue length |
| S6 | DB connection pool status | M | SQLAlchemy engine `.pool.status()` | Runtime inspection |
| S7 | Redis connectivity | M | Redis `PING` command | Runtime check |
| **Product Health** | | | | |
| P1 | User signup count/rate | E | `users` | `created_at` |
| P2 | Onboarding funnel | D | `users` -> `inventory_items` -> `recommendation_sessions` -> `meal_plans` | Join on `user_id`, check existence per stage |
| P3 | Activation rate (first item within 24h) | D | `users` JOIN `inventory_items` | `MIN(inventory_items.created_at) - users.created_at <= 24h` |
| P4 | WAU/MAU | D | `inventory_events` | `COUNT(DISTINCT user_id)` per week/month from `created_at` |
| P5 | Retention cohorts | D | `users` JOIN `inventory_events` | Cohort = `users.created_at` month; activity = `inventory_events.created_at` |
| P6 | Waste reduction ratio (North Star) | D | `inventory_items` | `COUNT(status='used') / COUNT(status IN ('used','discarded'))` |
| P7 | Items added count | E | `inventory_events` | `action = 'added'` |
| P8 | Recipes viewed count | M | `analytics_events` | Requires new `recipe_viewed` event type |
| P9 | Plans generated count | E | `meal_plans` | `created_at` |
| P10 | Item source distribution | E | `inventory_items` | `source` column (`manual\|barcode\|photo`) |
| P11 | Household size distribution | D | `household_members` | `COUNT(*) GROUP BY household_id WHERE is_active=true` |
| P12 | Recommendation sessions | E | `recommendation_sessions` | `created_at` |
| P13 | Notification preference adoption | E | `notification_preferences` | `COUNT(WHERE expiry_reminder_enabled=true)` |
| P14 | Device registrations by platform | E | `device_tokens` | `platform` column |
| **AI Quality** | | | | |
| A1 | Photo parse success rate | D | `inventory_items` + `inventory_events` | `source='photo'` items with `confidence > 0` vs total photo attempts |
| A2 | Avg confidence score (photo) | E | `inventory_items` | `AVG(confidence) WHERE source='photo'` |
| A3 | Confidence distribution over time | E | `inventory_items` | `confidence` bucketed, grouped by `created_at` week |
| A4 | Barcode hit rate | D | `inventory_items` | `COUNT(source='barcode')` — **[A-9]** barcode miss events not logged; only successful items exist. Dashboard shows successful barcode items only until `analytics_events` captures `barcode_scan_attempted` events |
| A5 | Recipe avg coverage_pct | M | `recommendation_sessions.request_params` | Coverage pct is computed at runtime in `scorer.py:65` but NOT persisted in `recommendation_sessions`. Requires storing scores in session record |
| A6 | Recipe avg use_soon_score | M | Same as A5 | Not persisted |
| A7 | LLM response latency | M | `ai_inference_log` (new) | `duration_ms WHERE provider='litellm'` |
| A8 | Photo fallback rate | D | `inventory_items` | `COUNT(source='photo' AND confidence < 0.5) / COUNT(source='photo')` — **[A-10]** confidence < 0.5 = fallback to editable draft (confirmed) |
| **Unit Economics** | | | | |
| U1 | LLM cost per photo parse | M | `ai_inference_log` (new) | `input_tokens * input_rate + output_tokens * output_rate` |
| U2 | Spoonacular cost per recommendation | M | `ai_inference_log` (new) | Points per API call |
| U3 | Firebase auth cost | M | Not trackable without middleware | Firebase auth verification happens in `backend/app/core/auth.py` with no cost instrumentation |
| U4 | Infrastructure cost breakdown | M | External (AWS billing API or manual entry) | Out of scope for v1; placeholder panel |
| U5 | Cost per active user | M | Depends on U1 + U2 + U4 | Derived from total cost / MAU |

### 3.2 Summary

| Classification | Count | Percentage |
|---------------|-------|------------|
| Existing (E) | 8 | 27% |
| Derivable (D) | 10 | 33% |
| Missing (M) | 12 | 40% |

**Dashboard v1 scope**: Ship all E + D metrics immediately (18 metrics). Ship M metrics incrementally as telemetry tables are instrumented.

---

## 4. Dashboard Views

### 4.1 System Health (`pages/1_System_Health.py`)

#### Layout

```
┌──────────────────────────────────────────────────────────────┐
│  SYSTEM HEALTH                              [Refresh] [Auto] │
├──────────────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ Uptime   │ │ Avg      │ │ Error    │ │ Req/sec      │   │
│  │ 99.8%    │ │ Latency  │ │ Rate     │ │ 12.5         │   │
│  │ (24h)    │ │ 142ms    │ │ 1.2%     │ │ (1m avg)     │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
├──────────────────────────────────────────────────────────────┤
│  API Latency by Endpoint (P50/P95 timeseries)               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  [Plotly line chart: one line per endpoint]           │   │
│  └──────────────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────────────┤
│  Error Rate by Endpoint        │  Throughput over Time      │
│  ┌───────────────────────┐     │  ┌──────────────────────┐  │
│  │ [Plotly bar chart]    │     │  │ [Plotly area chart]  │  │
│  └───────────────────────┘     │  └──────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│  Infrastructure Status                                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ Postgres │ │ Redis    │ │ Celery Q │ │ Backend      │   │
│  │ OK       │ │ OK       │ │ depth: 0 │ │ v0.1.0       │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

#### Data Sources & Behavior

| Widget | Data Source | Availability | Fallback (before instrumentation) |
|--------|-----------|--------------|----------------------------------|
| Uptime KPI | Health endpoint polling (dashboard -> `http://backend:8000/health`) | Available now via `httpx` | Show "N/A — polling starting" |
| Avg Latency | `api_request_log.duration_ms` | **After instrumentation** | Show "Requires API telemetry middleware" |
| Error Rate | `api_request_log WHERE status_code >= 400` | **After instrumentation** | Same |
| Req/sec | `api_request_log COUNT(*) per minute` | **After instrumentation** | Same |
| Latency chart | `api_request_log` grouped by path + time bucket | **After instrumentation** | Empty chart with info message |
| Postgres status | `SELECT 1` via dashboard engine | Available now | Connection error = red |
| Redis status | `redis.ping()` via dashboard | Available now | Connection error = red |
| Celery queue depth | Redis key `celery` (broker queue length inspection) | Available now | Show "Unknown" if Redis unreachable |
| Backend version | `GET /health` -> `version` field | Available now | Show "Unreachable" |

### 4.2 Product Health (`pages/2_Product_Health.py`)

#### Layout

```
┌──────────────────────────────────────────────────────────────┐
│  PRODUCT HEALTH              [Time range v] [Segment v]      │
├──────────────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ Total    │ │ WAU      │ │ Activation│ │ Waste        │   │
│  │ Users    │ │ 342      │ │ Rate      │ │ Reduction    │   │
│  │ 1,247    │ │ (+5.2%)  │ │ 38.5%    │ │ 72.3%        │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
├──────────────────────────────────────────────────────────────┤
│  Onboarding Funnel                                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  [Plotly funnel: Signup -> 1st Item -> 1st Rec ->    │   │
│  │                  1st Plan]                             │   │
│  └──────────────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────────────┤
│  Retention Cohorts (weekly)     │  Signup Trend              │
│  ┌───────────────────────┐     │  ┌──────────────────────┐  │
│  │ [Plotly heatmap]      │     │  │ [Plotly line chart]  │  │
│  └───────────────────────┘     │  └──────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│  Item Source Distribution       │  Household Size Dist      │
│  ┌───────────────────────┐     │  ┌──────────────────────┐  │
│  │ [Plotly pie/donut]    │     │  │ [Plotly histogram]   │  │
│  └───────────────────────┘     │  └──────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│  Key Action Counts (timeseries)                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Items Added | Recommendations | Plans Generated     │   │
│  │  [Plotly multi-line]                                  │   │
│  └──────────────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────────────┤
│  Notification & Device Adoption                              │
│  ┌───────────────────────┐     ┌──────────────────────┐     │
│  │ Reminders enabled:    │     │ Device tokens by     │     │
│  │ 67% of users          │     │ platform (pie)       │     │
│  └───────────────────────┘     └──────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

#### Metrics Detail

| Metric | Query Key | Source | SQL Reference |
|--------|-----------|--------|---------------|
| Total Users | `total_users` | `users` | Section 5.2 Q-P1 |
| WAU | `weekly_active_users` | `inventory_events` | Section 5.2 Q-P4 |
| Activation Rate | `activation_rate` | `users` JOIN `inventory_items` | Section 5.2 Q-P3 |
| Waste Reduction Ratio | `waste_ratio` | `inventory_items` | Section 5.2 Q-P6 |
| Onboarding Funnel | `onboarding_funnel` | Multi-table join | Section 5.2 Q-P2 |
| Retention Cohorts | `retention_cohorts` | `users` JOIN `inventory_events` | Section 5.2 Q-P5 |
| Signup Trend | `signup_trend` | `users` | Section 5.2 Q-P1b |
| Item Source Distribution | `item_sources` | `inventory_items` | Section 5.2 Q-P10 |
| Household Size | `household_sizes` | `household_members` | Section 5.2 Q-P11 |
| Key Actions | `key_actions` | `inventory_events` + `recommendation_sessions` + `meal_plans` | Section 5.2 Q-P7 |
| Notification Adoption | `notification_adoption` | `notification_preferences` | Section 5.2 Q-P13 |
| Device Tokens | `device_platforms` | `device_tokens` | Section 5.2 Q-P14 |

### 4.3 AI Quality (`pages/3_AI_Quality.py`)

#### Layout

```
┌──────────────────────────────────────────────────────────────┐
│  AI QUALITY                  [Time range v] [Source v]       │
├──────────────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ Photo    │ │ Avg      │ │ Barcode  │ │ Rec Sessions │   │
│  │ Items    │ │ Confid.  │ │ Items    │ │ 523          │   │
│  │ 892      │ │ 0.78     │ │ 1,340    │ │ (this week)  │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
├──────────────────────────────────────────────────────────────┤
│  Confidence Distribution Over Time                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  [Plotly stacked area: confidence buckets by week]    │   │
│  └──────────────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────────────┤
│  Photo Parse Metrics            │  Recommendation Quality   │
│  ┌───────────────────────┐     │  ┌──────────────────────┐  │
│  │ Avg confidence trend  │     │  │ Recipes shown/sess.  │  │
│  │ Fallback rate trend   │     │  │ (line chart)         │  │
│  └───────────────────────┘     │  └──────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│  REQUIRES INSTRUMENTATION (greyed out until available)       │
│  ┌───────────────────────┐     ┌──────────────────────┐     │
│  │ LLM Response Latency  │     │ Avg Coverage %       │     │
│  │ [After ai_inference_  │     │ [After scoring data  │     │
│  │  log table]           │     │  persistence]        │     │
│  └───────────────────────┘     └──────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

#### Metrics Detail

| Metric | Class | Source | Notes |
|--------|-------|--------|-------|
| Photo items count | E | `inventory_items WHERE source='photo'` | Direct query |
| Avg confidence (photo) | E | `inventory_items WHERE source='photo'` | `AVG(confidence)` |
| Barcode items count | E | `inventory_items WHERE source='barcode'` | Direct query |
| Recommendation sessions | E | `recommendation_sessions` | `COUNT(*)` |
| Confidence distribution | E | `inventory_items` | Bucket by confidence ranges |
| Recipes shown per session | D | `recommendation_sessions.recipes_shown` | `AVG(json_array_length(recipes_shown::text::json))` |
| Photo fallback rate | D | `inventory_items` | `COUNT(source='photo' AND confidence < 0.5) / COUNT(source='photo')` **[A-10]** |
| LLM latency | M | `ai_inference_log` (new) | After instrumentation |
| Avg coverage_pct | M | Not persisted | Requires change to `RecommendationService.get_recommendations()` to store scores |

### 4.4 Unit Economics (`pages/4_Unit_Economics.py`)

#### Layout

```
┌──────────────────────────────────────────────────────────────┐
│  UNIT ECONOMICS              [Time range v]                  │
├──────────────────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐    │
│  │ LLM Cost     │ │ Spoonacular  │ │ Cost / Active    │    │
│  │ (this month) │ │ Cost (month) │ │ User             │    │
│  │ $12.50       │ │ $8.30        │ │ $0.04            │    │
│  └──────────────┘ └──────────────┘ └──────────────────┘    │
├──────────────────────────────────────────────────────────────┤
│  Cost Trend Over Time                                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  [Plotly stacked area: LLM + Spoonacular + Other]     │   │
│  └──────────────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────────────┤
│  Cost per Photo Parse           │  Cost per Recommendation  │
│  ┌───────────────────────┐     │  ┌──────────────────────┐  │
│  │ [Histogram]           │     │  │ [Histogram]          │  │
│  └───────────────────────┘     │  └──────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│  ALL METRICS REQUIRE INSTRUMENTATION                         │
│  Status: Waiting for ai_inference_log table                  │
│  See Section 6 for schema definitions                        │
└──────────────────────────────────────────────────────────────┘
```

**Note:** All Unit Economics metrics are classification **M** (Missing). This entire page will show placeholder messages until `ai_inference_log` telemetry is instrumented. The page structure is defined now so it is ready to populate.

---

## 5. SQL Query Catalog

All queries use parameterized inputs `:start_date`, `:end_date` for time filtering. Queries are implemented as functions in `queries/*.py` modules that return SQL strings + params dicts.

### 5.1 System Health Queries

#### Q-S1: Health Endpoint Poll (runtime, not SQL)

```python
# queries/system_health.py
import os

import httpx

BACKEND_HEALTH_URL = os.getenv("BACKEND_HEALTH_URL", "http://backend:8000/health")


def check_backend_health() -> dict:
    """Poll GET /health and return status + version + latency."""
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


def check_redis_health(redis_url: str) -> dict:
    """Ping Redis and return connectivity status."""
    import redis as redis_lib

    try:
        r = redis_lib.from_url(redis_url)
        r.ping()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_celery_queue_depth(redis_url: str) -> int | None:
    """Read Celery broker queue length from Redis."""
    import redis as redis_lib

    try:
        r = redis_lib.from_url(redis_url)
        return r.llen("celery")
    except Exception:
        return None
```

#### Q-S2: API Latency by Endpoint (requires `api_request_log`)

```sql
-- Q-S2: API latency percentiles per endpoint
SELECT
    path,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration_ms) AS p50_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) AS p95_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms) AS p99_ms,
    COUNT(*) AS request_count
FROM api_request_log
WHERE created_at BETWEEN :start_date AND :end_date
GROUP BY path
ORDER BY p95_ms DESC;
```

#### Q-S3: Error Rate by Endpoint (requires `api_request_log`)

```sql
-- Q-S3: Error rate per endpoint
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
ORDER BY error_rate_pct DESC;
```

#### Q-S4: Throughput Over Time (requires `api_request_log`)

```sql
-- Q-S4: Requests per minute over time
SELECT
    DATE_TRUNC('minute', created_at) AS time_bucket,
    COUNT(*) AS request_count
FROM api_request_log
WHERE created_at BETWEEN :start_date AND :end_date
GROUP BY time_bucket
ORDER BY time_bucket;
```

#### Q-S5: API Latency Timeseries by Endpoint (requires `api_request_log`)

```sql
-- Q-S5: P50/P95 latency timeseries per endpoint (5-minute buckets)
SELECT
    DATE_TRUNC('hour', created_at) AS time_bucket,
    path,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration_ms) AS p50_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) AS p95_ms,
    COUNT(*) AS request_count
FROM api_request_log
WHERE created_at BETWEEN :start_date AND :end_date
GROUP BY time_bucket, path
ORDER BY time_bucket, path;
```

### 5.2 Product Health Queries

#### Q-P1: Total Users + Signup Trend

```sql
-- Q-P1: Total user count
SELECT COUNT(*) AS total_users
FROM users
WHERE created_at <= :end_date;
```

```sql
-- Q-P1b: Signup trend (daily)
SELECT
    DATE_TRUNC('day', created_at) AS signup_date,
    COUNT(*) AS signups
FROM users
WHERE created_at BETWEEN :start_date AND :end_date
GROUP BY signup_date
ORDER BY signup_date;
```

#### Q-P2: Onboarding Funnel

```sql
-- Q-P2: Onboarding funnel stages
-- Stage 1: Signed up (all users in period)
-- Stage 2: Added first item (exists in inventory_items)
-- Stage 3: Got first recommendation (via household_members -> recommendation_sessions)
-- Stage 4: Created first meal plan (exists in meal_plans)
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
SELECT 'Created Meal Plan', COUNT(*) FROM first_plan;
```

#### Q-P3: Activation Rate

```sql
-- Q-P3: Activation rate — users who added >= 1 item within 24h of signup
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
    ) AS activation_rate_pct;
```

#### Q-P4: WAU / MAU

```sql
-- Q-P4a: Weekly Active Users (users with inventory_events in the last 7 days)
SELECT COUNT(DISTINCT user_id) AS wau
FROM inventory_events
WHERE created_at >= :end_date - INTERVAL '7 days'
  AND created_at <= :end_date;
```

```sql
-- Q-P4b: Monthly Active Users
SELECT COUNT(DISTINCT user_id) AS mau
FROM inventory_events
WHERE created_at >= :end_date - INTERVAL '30 days'
  AND created_at <= :end_date;
```

```sql
-- Q-P4c: WAU trend over time
SELECT
    DATE_TRUNC('week', created_at) AS week_start,
    COUNT(DISTINCT user_id) AS active_users
FROM inventory_events
WHERE created_at BETWEEN :start_date AND :end_date
GROUP BY week_start
ORDER BY week_start;
```

#### Q-P5: Retention Cohorts

```sql
-- Q-P5: Weekly retention cohort matrix
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
ORDER BY r.cohort_week, r.week_number;
```

#### Q-P6: Waste Reduction Ratio (North Star)

```sql
-- Q-P6: North Star — waste reduction ratio
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
  AND status IN ('used', 'discarded');
```

```sql
-- Q-P6b: Waste reduction trend (weekly)
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
ORDER BY week_start;
```

#### Q-P7: Key Action Counts

```sql
-- Q-P7: Key action counts over time (daily)
SELECT
    d.day::date AS action_date,
    COALESCE(items.cnt, 0) AS items_added,
    COALESCE(recs.cnt, 0) AS recommendation_sessions,
    COALESCE(plans.cnt, 0) AS plans_generated
FROM generate_series(:start_date::date, :end_date::date, '1 day'::interval) AS d(day)
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
ORDER BY action_date;
```

#### Q-P10: Item Source Distribution

```sql
-- Q-P10: Item source distribution
SELECT
    source,
    COUNT(*) AS item_count,
    ROUND(100.0 * COUNT(*) / NULLIF(SUM(COUNT(*)) OVER(), 0), 1) AS percentage
FROM inventory_items
WHERE created_at BETWEEN :start_date AND :end_date
GROUP BY source
ORDER BY item_count DESC;
```

#### Q-P11: Household Size Distribution

```sql
-- Q-P11: Household member count distribution
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
ORDER BY member_count;
```

#### Q-P13: Notification Preference Adoption

```sql
-- Q-P13: Notification adoption rate
SELECT
    COUNT(*) FILTER (WHERE expiry_reminder_enabled = true) AS reminders_enabled,
    COUNT(*) AS total_preferences,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE expiry_reminder_enabled = true)
        / NULLIF(COUNT(*), 0), 1
    ) AS adoption_pct
FROM notification_preferences;
```

#### Q-P14: Device Token Registrations by Platform

```sql
-- Q-P14: Device registrations by platform
SELECT
    platform,
    COUNT(*) AS device_count
FROM device_tokens
GROUP BY platform
ORDER BY device_count DESC;
```

### 5.3 AI Quality Queries

#### Q-A2: Avg Confidence (Photo Items)

```sql
-- Q-A2: Average confidence for photo-parsed items
SELECT
    ROUND(AVG(confidence)::numeric, 3) AS avg_confidence,
    COUNT(*) AS photo_item_count
FROM inventory_items
WHERE source = 'photo'
  AND created_at BETWEEN :start_date AND :end_date;
```

#### Q-A3: Confidence Distribution Over Time

```sql
-- Q-A3: Confidence score distribution by week (photo items)
SELECT
    DATE_TRUNC('week', created_at) AS week_start,
    COUNT(*) FILTER (WHERE confidence >= 0.9) AS high_confidence,
    COUNT(*) FILTER (WHERE confidence >= 0.7 AND confidence < 0.9) AS medium_confidence,
    COUNT(*) FILTER (WHERE confidence >= 0.5 AND confidence < 0.7) AS low_confidence,
    COUNT(*) FILTER (WHERE confidence < 0.5) AS very_low_confidence
FROM inventory_items
WHERE source = 'photo'
  AND created_at BETWEEN :start_date AND :end_date
GROUP BY week_start
ORDER BY week_start;
```

#### Q-A4: Barcode Item Count

```sql
-- Q-A4: Barcode items created (successful lookups only — see [A-9])
SELECT
    DATE_TRUNC('week', created_at) AS week_start,
    COUNT(*) AS barcode_items
FROM inventory_items
WHERE source = 'barcode'
  AND created_at BETWEEN :start_date AND :end_date
GROUP BY week_start
ORDER BY week_start;
```

#### Q-A8: Photo Fallback Rate

```sql
-- Q-A8: Photo fallback rate (confidence < 0.5 = editable draft, see [A-10])
SELECT
    COUNT(*) AS total_photo_items,
    COUNT(*) FILTER (WHERE confidence < 0.5) AS fallback_items,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE confidence < 0.5)
        / NULLIF(COUNT(*), 0), 1
    ) AS fallback_rate_pct
FROM inventory_items
WHERE source = 'photo'
  AND created_at BETWEEN :start_date AND :end_date;
```

#### Q-A8b: Photo Fallback Rate Trend

```sql
-- Q-A8b: Photo fallback rate trend (weekly)
SELECT
    DATE_TRUNC('week', created_at) AS week_start,
    COUNT(*) AS total_photo_items,
    COUNT(*) FILTER (WHERE confidence < 0.5) AS fallback_items,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE confidence < 0.5)
        / NULLIF(COUNT(*), 0), 1
    ) AS fallback_rate_pct
FROM inventory_items
WHERE source = 'photo'
  AND created_at BETWEEN :start_date AND :end_date
GROUP BY week_start
ORDER BY week_start;
```

#### Q-A-Rec: Recommendation Session Stats

```sql
-- Q-A-Rec: Recommendations per session
SELECT
    DATE_TRUNC('week', created_at) AS week_start,
    COUNT(*) AS session_count,
    ROUND(
        AVG(json_array_length(recipes_shown::text::json))::numeric, 1
    ) AS avg_recipes_shown
FROM recommendation_sessions
WHERE created_at BETWEEN :start_date AND :end_date
GROUP BY week_start
ORDER BY week_start;
```

### 5.4 Unit Economics Queries (all require `ai_inference_log`)

#### Q-U1: LLM Cost per Photo Parse

```sql
-- Q-U1: LLM cost per photo parse (requires ai_inference_log)
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
ORDER BY day;
```

#### Q-U2: Spoonacular Cost per Recommendation

```sql
-- Q-U2: Spoonacular cost per recommendation (requires ai_inference_log)
SELECT
    DATE_TRUNC('day', created_at) AS day,
    COUNT(*) AS api_calls,
    SUM(api_points_used) AS total_points,
    ROUND(AVG(api_points_used)::numeric, 1) AS avg_points_per_call
FROM ai_inference_log
WHERE provider = 'spoonacular'
  AND created_at BETWEEN :start_date AND :end_date
GROUP BY day
ORDER BY day;
```

#### Q-U3: Total Cost Trend

```sql
-- Q-U3: Total cost by provider over time
SELECT
    DATE_TRUNC('week', created_at) AS week_start,
    provider,
    SUM(cost_usd) AS total_cost_usd,
    COUNT(*) AS call_count
FROM ai_inference_log
WHERE created_at BETWEEN :start_date AND :end_date
  AND cost_usd IS NOT NULL
GROUP BY week_start, provider
ORDER BY week_start, provider;
```

#### Q-U5: Cost per Active User

```sql
-- Q-U5: Cost per active user (requires ai_inference_log + inventory_events for MAU)
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
FROM monthly_cost mc, mau m;
```

---

## 6. Missing Telemetry Schemas

### 6.1 Table: `api_request_log`

**Purpose:** Capture per-request telemetry for API latency, error rate, and throughput metrics.

**Implementation location:** FastAPI middleware in `backend/app/core/telemetry_middleware.py`.

#### SQLAlchemy Model

```python
# backend/app/models/api_request_log.py

from __future__ import annotations

from datetime import UTC, datetime
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class ApiRequestLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "api_request_log"

    method: Mapped[str] = mapped_column(String(10))
    path: Mapped[str] = mapped_column(String(255), index=True)
    status_code: Mapped[int] = mapped_column(Integer)
    duration_ms: Mapped[float] = mapped_column(Float)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True, index=True
    )
    request_id: Mapped[str] = mapped_column(String(36))
    error_detail: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )
```

#### Middleware Pattern

```python
# backend/app/core/telemetry_middleware.py

from __future__ import annotations

import time
import uuid as uuid_mod

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.database import AsyncSessionLocal
from app.models.api_request_log import ApiRequestLog


class TelemetryMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request to api_request_log for dashboard consumption."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid_mod.uuid4())
        start = time.perf_counter()
        status_code = 500
        error_detail = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            error_detail = str(exc)[:500]
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000

            # Extract user_id from request state if auth middleware set it
            user_id = getattr(request.state, "user_id", None)

            # Fire-and-forget: write log row without blocking response
            try:
                async with AsyncSessionLocal() as session:
                    log_entry = ApiRequestLog(
                        method=request.method,
                        path=request.url.path,
                        status_code=status_code,
                        duration_ms=duration_ms,
                        user_id=user_id,
                        request_id=request_id,
                        error_detail=error_detail,
                    )
                    session.add(log_entry)
                    await session.commit()
            except Exception:
                pass  # Telemetry failure must never break the API
```

#### Registration in `main.py`

```python
# Add after app creation in backend/app/main.py:
from app.core.telemetry_middleware import TelemetryMiddleware
app.add_middleware(TelemetryMiddleware)
```

#### Index Strategy

- `ix_api_request_log_path` on `path` (endpoint grouping)
- `ix_api_request_log_created_at` on `created_at` (time range queries)
- `ix_api_request_log_user_id` on `user_id` (per-user analysis)

**Retention policy:** 90 days. Rows older than 90 days should be purged via a Celery beat task.

**Estimated row volume:** ~50K-500K rows/day depending on traffic.

### 6.2 Table: `ai_inference_log`

**Purpose:** Track AI/external API calls with cost and performance data — covers LLM (LiteLLM/GPT-4.1-mini) photo parsing and Spoonacular recipe API calls.

#### SQLAlchemy Model

```python
# backend/app/models/ai_inference_log.py

from __future__ import annotations

from datetime import UTC, datetime
import uuid

from sqlalchemy import DateTime, Float, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class AiInferenceLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ai_inference_log"

    provider: Mapped[str] = mapped_column(String(50), index=True)
    # 'litellm', 'spoonacular', 'firebase_auth'
    operation: Mapped[str] = mapped_column(String(100))
    # 'photo_parse', 'recipe_search', 'token_verify'
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 'gpt-4.1-mini' for LLM calls
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True, index=True
    )
    household_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True
    )

    # Performance
    duration_ms: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20))
    # 'success', 'error', 'timeout'

    # Cost (LLM-specific)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Cost (API-specific)
    api_points_used: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    # Context
    request_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True
    )
    error_detail: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    # Result quality
    items_returned: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    avg_confidence: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )
```

#### Integration Points

**1. LLM Photo Parser** (`backend/app/modules/catalog/photo_interfaces.py:45-108`):

Wrap the `httpx.AsyncClient.post()` call at line 97:

```python
# Inside LLMPhotoParser.parse_image(), after getting the response:
import time
from app.models.ai_inference_log import AiInferenceLog

start = time.perf_counter()
# ... existing httpx.post() call ...
duration_ms = (time.perf_counter() - start) * 1000

# Extract token usage from LLM response (standard OpenAI format via LiteLLM)
usage = response_payload.get("usage", {}) if isinstance(response_payload, dict) else {}
input_tokens = usage.get("prompt_tokens")
output_tokens = usage.get("completion_tokens")

# Compute cost using configured rates
cost_usd = None
if input_tokens is not None and output_tokens is not None:
    cost_usd = (
        input_tokens * settings.LLM_INPUT_COST_PER_1M / 1_000_000
        + output_tokens * settings.LLM_OUTPUT_COST_PER_1M / 1_000_000
    )

# Log to ai_inference_log (fire-and-forget)
log_entry = AiInferenceLog(
    provider="litellm",
    operation="photo_parse",
    model=self._model,
    duration_ms=duration_ms,
    status="success",  # or "error" in except block
    input_tokens=input_tokens,
    output_tokens=output_tokens,
    cost_usd=cost_usd,
    items_returned=len(draft_items),
    avg_confidence=sum(i.get("confidence", 0) for i in draft_items) / max(len(draft_items), 1),
)
```

**2. Spoonacular Client** (`backend/app/modules/recommendations/spoonacular.py`):

```python
# Wrap the API call:
start = time.perf_counter()
# ... existing httpx.get() call to Spoonacular ...
duration_ms = (time.perf_counter() - start) * 1000

log_entry = AiInferenceLog(
    provider="spoonacular",
    operation="recipe_search",
    model=None,
    duration_ms=duration_ms,
    status="success",
    api_points_used=1,  # Spoonacular charges 1 point per findByIngredients call
    items_returned=len(recipes),
)
```

#### Cost Rate Configuration

Add to `backend/app/core/config.py`:

```python
# Cost tracking rates
LLM_INPUT_COST_PER_1M: float = 0.40      # USD per 1M input tokens (GPT-4.1-mini)
LLM_OUTPUT_COST_PER_1M: float = 1.60     # USD per 1M output tokens (GPT-4.1-mini)
SPOONACULAR_POINT_COST: float = 0.005    # USD per API point (estimated)
```

### 6.3 Product Event Schema (for existing `analytics_events` table)

The existing `analytics_events` table (`backend/app/models/events.py:31-40`) already supports flexible `event_type` + `payload` JSON. Define these new standard event types:

| Event Type | Trigger Point | Payload Schema |
|------------|--------------|----------------|
| `recipe_viewed` | User opens recipe detail screen (mobile) | `{"recipe_id": "<uuid>", "source": "recommendation\|search", "session_id": "<uuid>"}` |
| `recipe_saved` | User saves/bookmarks a recipe (mobile) | `{"recipe_id": "<uuid>"}` |
| `recipe_cooked` | User marks a recipe as cooked (mobile) | `{"recipe_id": "<uuid>", "meal_plan_day_id": "<uuid>\|null"}` |
| `barcode_scan_attempted` | Barcode scan initiated (mobile) | `{"success": true, "barcode": "<string>", "error": null}` |
| `photo_scan_attempted` | Photo scan initiated (mobile) | `{"success": true, "items_returned": 3, "avg_confidence": 0.82}` |
| `meal_plan_completed` | All days in a plan are done (mobile) | `{"plan_id": "<uuid>", "days_count": 7, "recipes_cooked": 5}` |
| `user_signed_in` | After successful auth (mobile) | `{"provider": "email\|apple\|google", "platform": "ios\|android"}` |
| `user_signed_out` | After sign out (mobile) | `{"platform": "ios\|android"}` |
| `item_status_changed` | Item status transitions (backend) | `{"item_id": "<uuid>", "from_status": "active", "to_status": "used"}` |

**Note:** These events are sent from mobile via `POST /v1/analytics/events` (existing endpoint at `backend/app/modules/analytics/router.py:19-36`). No backend schema migration required — just new event types flowing through the existing flexible schema.

---

## 7. Cross-Cutting Filters & UX

### 7.1 Shared Filter Component (`components/filters.py`)

All dashboard pages share a common filter sidebar:

```python
# components/filters.py

from datetime import date, datetime, timedelta

import streamlit as st


def render_time_filter() -> tuple[date, date]:
    """Render time range selector in sidebar. Returns (start_date, end_date)."""
    preset = st.sidebar.selectbox(
        "Time Range",
        ["Last 24h", "Last 7 days", "Last 30 days", "Last 90 days", "Custom"],
        index=2,
        key="time_preset",
    )
    now = datetime.utcnow()
    if preset == "Custom":
        start = st.sidebar.date_input(
            "Start", value=now - timedelta(days=30), key="filter_start"
        )
        end = st.sidebar.date_input("End", value=now, key="filter_end")
    else:
        days_map = {
            "Last 24h": 1,
            "Last 7 days": 7,
            "Last 30 days": 30,
            "Last 90 days": 90,
        }
        start = (now - timedelta(days=days_map[preset])).date()
        end = now.date()
    return start, end


def render_source_filter() -> str | None:
    """Item source filter: manual, barcode, photo, or All."""
    source = st.sidebar.selectbox(
        "Item Source",
        ["All", "manual", "barcode", "photo"],
        key="source_filter",
    )
    return None if source == "All" else source


def render_refresh_controls() -> bool:
    """Refresh button + auto-refresh toggle. Returns whether auto-refresh is on."""
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Refresh", key="refresh_btn"):
            st.cache_data.clear()
            st.rerun()
    with col2:
        auto_refresh = st.checkbox("Auto (60s)", key="auto_refresh")
    return auto_refresh
```

### 7.2 Metric Card Helpers (`components/metrics.py`)

```python
# components/metrics.py

import streamlit as st
from db.connection import check_table_exists


def render_metric_card(label: str, value, delta: str | None = None):
    """Render a standard KPI metric card."""
    st.metric(label=label, value=value, delta=delta)


def placeholder_metric(title: str, requires: str):
    """Show a greyed-out metric card with instrumentation requirement."""
    st.metric(label=title, value="--")
    st.caption(f"Requires: {requires}")


def render_metric_or_placeholder(
    label: str,
    value_fn,
    requires_table: str | None = None,
    requires_label: str = "",
):
    """Render a metric if data is available, otherwise show placeholder."""
    if requires_table and not check_table_exists(requires_table):
        placeholder_metric(label, requires_label or f"{requires_table} table")
        return
    try:
        value = value_fn()
        render_metric_card(label, value)
    except Exception:
        placeholder_metric(label, "data unavailable")
```

### 7.3 Filter Application

Filters are stored in `st.session_state` and accessed across pages:

| Filter | Key | Applied To | Pages |
|--------|-----|-----------|-------|
| Time range | `time_preset`, `filter_start`, `filter_end` | All SQL queries via `:start_date`, `:end_date` params | All |
| Item source | `source_filter` | `WHERE source = :source` on `inventory_items` queries | Product, AI |
| Refresh | `auto_refresh` | `st.rerun()` after 60s sleep | All |

### 7.4 Caching Strategy

| Query Category | TTL | Rationale |
|---------------|-----|-----------|
| System health (uptime, connectivity) | 30 seconds | Near-real-time monitoring |
| Product health (WAU, funnel, retention) | 5 minutes | Acceptable lag for product metrics |
| AI quality (confidence, session counts) | 5 minutes | Same as product |
| Unit economics (cost data) | 15 minutes | Cost data does not change rapidly |
| Static lookups (enums, labels) | 1 hour | Rarely changes |

Implementation pattern:

```python
@st.cache_data(ttl=300)  # 5 minutes for product metrics
def get_onboarding_funnel(start_date: date, end_date: date) -> pd.DataFrame:
    return run_query(ONBOARDING_FUNNEL_SQL, {"start_date": start_date, "end_date": end_date})

@st.cache_data(ttl=30)  # 30 seconds for system health
def get_backend_health() -> dict:
    return check_backend_health()
```

### 7.5 Auto-Refresh Pattern

```python
# At the end of each page:
import time

auto_refresh = render_refresh_controls()
if auto_refresh:
    time.sleep(60)
    st.rerun()
```

---

## 8. TDD Testing Strategy

### 8.1 Test Architecture

```
dashboard/tests/
├── conftest.py                      # Shared fixtures: test DB, sample data factories
├── test_queries_system_health.py    # Unit tests for system health queries
├── test_queries_product_health.py   # Unit tests for product health queries
├── test_queries_ai_quality.py       # Unit tests for AI quality queries
├── test_queries_unit_economics.py   # Unit tests for unit economics queries
├── test_components_charts.py        # Unit tests for Plotly chart builders
├── test_components_filters.py       # Unit tests for filter logic
└── test_pages_smoke.py              # Smoke tests for Streamlit page rendering
```

### 8.2 Test Database Setup (`conftest.py`)

```python
# dashboard/tests/conftest.py

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://fridgefriend:fridgefriend@localhost:5432/fridgefriend_test"


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine. Tables created by backend schema."""
    engine = create_engine(DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture
def db_conn(test_engine):
    """Provide a transactional connection that rolls back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    yield connection
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_users(db_conn):
    """Insert 10 sample users spread across the last 30 days."""
    users = []
    for i in range(10):
        user_id = uuid.uuid4()
        db_conn.execute(
            text(
                "INSERT INTO users (id, email, created_at, updated_at) "
                "VALUES (:id, :email, :ts, :ts)"
            ),
            {
                "id": user_id,
                "email": f"user{i}@test.com",
                "ts": datetime.now(UTC) - timedelta(days=30 - i * 3),
            },
        )
        users.append(user_id)
    return users


@pytest.fixture
def sample_household(db_conn, sample_users):
    """Create a household with all sample users as members."""
    hh_id = uuid.uuid4()
    db_conn.execute(
        text(
            "INSERT INTO households (id, name, invite_code, created_at, updated_at) "
            "VALUES (:id, :name, :code, :ts, :ts)"
        ),
        {
            "id": hh_id,
            "name": "Test Household",
            "code": "TEST123",
            "ts": datetime.now(UTC),
        },
    )
    for i, uid in enumerate(sample_users):
        db_conn.execute(
            text(
                "INSERT INTO household_members "
                "(id, household_id, user_id, role, is_active, created_at, updated_at) "
                "VALUES (:id, :hh, :uid, :role, true, :ts, :ts)"
            ),
            {
                "id": uuid.uuid4(),
                "hh": hh_id,
                "uid": uid,
                "role": "owner" if i == 0 else "member",
                "ts": datetime.now(UTC),
            },
        )
    return hh_id


@pytest.fixture
def sample_items(db_conn, sample_users, sample_household):
    """Insert inventory items with mixed sources and statuses."""
    items = []
    sources = ["manual", "barcode", "photo"]
    statuses = ["active", "used", "discarded", "used", "used"]  # 60% used
    for i, uid in enumerate(sample_users):
        for j in range(3):
            item_id = uuid.uuid4()
            db_conn.execute(
                text(
                    "INSERT INTO inventory_items "
                    "(id, user_id, household_id, display_name, quantity, unit, "
                    "storage_location, estimated_expiry_date, confidence, status, "
                    "source, canonical_name, version, created_at, updated_at) "
                    "VALUES (:id, :uid, :hh, :name, 1.0, 'unit', 'fridge', "
                    ":expiry, :conf, :status, :source, :canon, 1, :ts, :ts)"
                ),
                {
                    "id": item_id,
                    "uid": uid,
                    "hh": sample_household,
                    "name": f"Item {i}-{j}",
                    "expiry": date.today() + timedelta(days=j * 3),
                    "conf": 0.3 + j * 0.25,  # 0.3, 0.55, 0.8
                    "status": statuses[j % len(statuses)],
                    "source": sources[j % len(sources)],
                    "canon": f"item_{i}_{j}",
                    "ts": datetime.now(UTC) - timedelta(days=10 - j),
                },
            )
            items.append(item_id)
    return items


@pytest.fixture
def sample_events(db_conn, sample_users, sample_household, sample_items):
    """Insert inventory events for retention/WAU testing."""
    for week in range(4):
        for i, uid in enumerate(sample_users[:7 - week]):  # Decreasing retention
            db_conn.execute(
                text(
                    "INSERT INTO inventory_events "
                    "(id, household_id, user_id, item_id, action, "
                    "previous_state, new_state, created_at, updated_at) "
                    "VALUES (:id, :hh, :uid, NULL, 'added', "
                    "'{}'::json, '{}'::json, :ts, :ts)"
                ),
                {
                    "id": uuid.uuid4(),
                    "hh": sample_household,
                    "uid": uid,
                    "ts": datetime.now(UTC) - timedelta(weeks=week),
                },
            )
```

### 8.3 Query Test Patterns

Each query module gets corresponding tests. Tests follow **Arrange -> Act -> Assert** pattern with known data.

```python
# dashboard/tests/test_queries_product_health.py

import pytest
from datetime import date, timedelta
from queries.product_health import (
    get_total_users,
    get_onboarding_funnel,
    get_activation_rate,
    get_waste_ratio,
    get_wau,
    get_retention_cohorts,
    get_item_source_distribution,
    get_household_size_distribution,
    get_key_action_counts,
    get_notification_adoption,
    get_device_platforms,
    get_signup_trend,
)


class TestTotalUsers:
    def test_returns_correct_count(self, db_conn, sample_users):
        """Given 10 users in DB, total_users returns 10."""
        result = get_total_users(db_conn, end_date=date.today() + timedelta(days=1))
        assert result.iloc[0]["total_users"] == 10

    def test_respects_end_date_filter(self, db_conn, sample_users):
        """Users created after end_date are excluded."""
        result = get_total_users(db_conn, end_date=date.today() - timedelta(days=20))
        assert result.iloc[0]["total_users"] < 10

    def test_empty_db_returns_zero(self, db_conn):
        """No users returns count of 0."""
        result = get_total_users(db_conn, end_date=date.today())
        assert result.iloc[0]["total_users"] == 0


class TestOnboardingFunnel:
    def test_funnel_counts_decrease_monotonically(
        self, db_conn, sample_users, sample_items
    ):
        """Each funnel stage has equal or fewer users than the previous stage."""
        result = get_onboarding_funnel(
            db_conn,
            start_date=date.today() - timedelta(days=60),
            end_date=date.today() + timedelta(days=1),
        )
        counts = result["user_count"].tolist()
        for i in range(1, len(counts)):
            assert counts[i] <= counts[i - 1], (
                f"Stage {i} ({counts[i]}) > Stage {i-1} ({counts[i-1]})"
            )

    def test_empty_cohort_returns_zero_stages(self, db_conn):
        """No users in date range returns all zero counts."""
        result = get_onboarding_funnel(
            db_conn,
            start_date=date(2099, 1, 1),
            end_date=date(2099, 12, 31),
        )
        for _, row in result.iterrows():
            assert row["user_count"] == 0

    def test_first_stage_equals_signup_count(self, db_conn, sample_users):
        """First funnel stage (Signed Up) should match total users in cohort."""
        result = get_onboarding_funnel(
            db_conn,
            start_date=date.today() - timedelta(days=60),
            end_date=date.today() + timedelta(days=1),
        )
        assert result.iloc[0]["user_count"] == len(sample_users)


class TestActivationRate:
    def test_returns_valid_percentage(self, db_conn, sample_users, sample_items):
        """Activation rate is between 0 and 100."""
        result = get_activation_rate(
            db_conn,
            start_date=date.today() - timedelta(days=60),
            end_date=date.today() + timedelta(days=1),
        )
        pct = result.iloc[0]["activation_rate_pct"]
        assert pct is None or (0 <= pct <= 100)

    def test_no_users_returns_null_rate(self, db_conn):
        """Empty cohort returns null activation rate."""
        result = get_activation_rate(
            db_conn,
            start_date=date(2099, 1, 1),
            end_date=date(2099, 12, 31),
        )
        assert result.iloc[0]["activation_rate_pct"] is None


class TestWasteRatio:
    def test_mixed_statuses_returns_valid_ratio(
        self, db_conn, sample_users, sample_items, sample_household
    ):
        """With both used and discarded items, ratio is between 0 and 100."""
        result = get_waste_ratio(
            db_conn,
            start_date=date.today() - timedelta(days=60),
            end_date=date.today() + timedelta(days=1),
        )
        pct = result.iloc[0]["waste_reduction_pct"]
        if pct is not None:
            assert 0 <= pct <= 100

    def test_no_resolved_items_returns_null(self, db_conn):
        """No used or discarded items returns None for ratio."""
        result = get_waste_ratio(
            db_conn,
            start_date=date(2099, 1, 1),
            end_date=date(2099, 12, 31),
        )
        assert result.iloc[0]["waste_reduction_pct"] is None


class TestWAU:
    def test_returns_nonnegative_count(self, db_conn, sample_events):
        """WAU count is non-negative."""
        result = get_wau(db_conn, end_date=date.today() + timedelta(days=1))
        assert result.iloc[0]["wau"] >= 0


class TestRetentionCohorts:
    def test_week_zero_retention_is_100_percent(
        self, db_conn, sample_users, sample_events
    ):
        """Week 0 retention for every cohort should be 100%."""
        result = get_retention_cohorts(
            db_conn,
            start_date=date.today() - timedelta(days=60),
            end_date=date.today() + timedelta(days=1),
        )
        week_zero = result[result["week_number"] == 0]
        for _, row in week_zero.iterrows():
            assert row["retention_pct"] == 100.0

    def test_empty_result_for_future_dates(self, db_conn):
        """No data for future dates."""
        result = get_retention_cohorts(
            db_conn,
            start_date=date(2099, 1, 1),
            end_date=date(2099, 12, 31),
        )
        assert len(result) == 0


class TestItemSourceDistribution:
    def test_returns_known_sources(self, db_conn, sample_items):
        """Source values are manual, barcode, or photo."""
        result = get_item_source_distribution(
            db_conn,
            start_date=date.today() - timedelta(days=60),
            end_date=date.today() + timedelta(days=1),
        )
        valid_sources = {"manual", "barcode", "photo"}
        for _, row in result.iterrows():
            assert row["source"] in valid_sources

    def test_percentages_sum_to_100(self, db_conn, sample_items):
        """Source percentages should sum to approximately 100."""
        result = get_item_source_distribution(
            db_conn,
            start_date=date.today() - timedelta(days=60),
            end_date=date.today() + timedelta(days=1),
        )
        total = result["percentage"].sum()
        assert abs(total - 100.0) < 0.5


class TestHouseholdSize:
    def test_returns_positive_sizes(self, db_conn, sample_household):
        """All household sizes are positive."""
        result = get_household_size_distribution(db_conn)
        for _, row in result.iterrows():
            assert row["member_count"] > 0
```

### 8.4 Chart Component Tests

```python
# dashboard/tests/test_components_charts.py

import pandas as pd
import plotly.graph_objects as go
import pytest

from components.charts import (
    create_funnel_chart,
    create_retention_heatmap,
    create_timeseries,
    create_pie_chart,
    create_stacked_area,
)


class TestFunnelChart:
    def test_returns_plotly_figure(self):
        data = pd.DataFrame({"stage": ["A", "B", "C"], "count": [100, 50, 20]})
        fig = create_funnel_chart(data, "stage", "count")
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0

    def test_handles_empty_dataframe(self):
        data = pd.DataFrame({"stage": [], "count": []})
        fig = create_funnel_chart(data, "stage", "count")
        assert isinstance(fig, go.Figure)

    def test_handles_single_stage(self):
        data = pd.DataFrame({"stage": ["A"], "count": [100]})
        fig = create_funnel_chart(data, "stage", "count")
        assert isinstance(fig, go.Figure)


class TestRetentionHeatmap:
    def test_returns_plotly_figure(self):
        data = pd.DataFrame(
            {
                "cohort_week": pd.to_datetime(
                    ["2026-01-01", "2026-01-01", "2026-01-08"]
                ),
                "week_number": [0, 1, 0],
                "retention_pct": [100.0, 80.0, 100.0],
            }
        )
        fig = create_retention_heatmap(data)
        assert isinstance(fig, go.Figure)

    def test_handles_empty_dataframe(self):
        data = pd.DataFrame(
            {"cohort_week": [], "week_number": [], "retention_pct": []}
        )
        fig = create_retention_heatmap(data)
        assert isinstance(fig, go.Figure)


class TestTimeseries:
    def test_returns_plotly_figure(self):
        data = pd.DataFrame(
            {
                "date": pd.date_range("2026-01-01", periods=10),
                "value": range(10),
            }
        )
        fig = create_timeseries(data, "date", "value", title="Test")
        assert isinstance(fig, go.Figure)


class TestPieChart:
    def test_returns_plotly_figure(self):
        data = pd.DataFrame({"label": ["A", "B"], "value": [60, 40]})
        fig = create_pie_chart(data, "label", "value")
        assert isinstance(fig, go.Figure)
```

### 8.5 Filter Component Tests

```python
# dashboard/tests/test_components_filters.py

from datetime import date, timedelta


class TestTimeRangeLogic:
    """Test the time range calculation logic (not Streamlit widgets)."""

    def test_last_7_days_range(self):
        from datetime import datetime

        now = datetime.utcnow()
        start = (now - timedelta(days=7)).date()
        end = now.date()
        assert (end - start).days == 7

    def test_last_30_days_range(self):
        from datetime import datetime

        now = datetime.utcnow()
        start = (now - timedelta(days=30)).date()
        end = now.date()
        assert (end - start).days == 30

    def test_custom_range_start_before_end(self):
        start = date(2026, 1, 1)
        end = date(2026, 3, 1)
        assert start < end
```

### 8.6 Smoke Tests (Streamlit AppTest)

```python
# dashboard/tests/test_pages_smoke.py

import pytest
from streamlit.testing.v1 import AppTest


class TestHomePage:
    def test_home_page_loads_without_exception(self):
        at = AppTest.from_file("Home.py", default_timeout=10)
        at.run()
        assert not at.exception


class TestSystemHealthPage:
    def test_page_loads_without_exception(self):
        at = AppTest.from_file("pages/1_System_Health.py", default_timeout=10)
        at.run()
        assert not at.exception


class TestProductHealthPage:
    def test_page_loads_without_exception(self):
        at = AppTest.from_file("pages/2_Product_Health.py", default_timeout=10)
        at.run()
        assert not at.exception


class TestAIQualityPage:
    def test_page_loads_without_exception(self):
        at = AppTest.from_file("pages/3_AI_Quality.py", default_timeout=10)
        at.run()
        assert not at.exception


class TestUnitEconomicsPage:
    def test_page_loads_without_exception(self):
        at = AppTest.from_file("pages/4_Unit_Economics.py", default_timeout=10)
        at.run()
        assert not at.exception
```

### 8.7 Backend Telemetry Tests

```python
# backend/tests/core/test_telemetry_middleware.py

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_middleware_logs_successful_request(db_session):
    """Verify api_request_log row created for successful requests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200

    # Verify log entry created
    from sqlalchemy import select, text

    result = await db_session.execute(
        text("SELECT * FROM api_request_log WHERE path = '/health' ORDER BY created_at DESC LIMIT 1")
    )
    row = result.first()
    assert row is not None
    assert row.method == "GET"
    assert row.status_code == 200
    assert row.duration_ms > 0


@pytest.mark.asyncio
async def test_middleware_logs_error_request(db_session):
    """Verify api_request_log captures 404 errors."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/v1/nonexistent")
        assert response.status_code in (404, 405)

    result = await db_session.execute(
        text("SELECT * FROM api_request_log WHERE path = '/v1/nonexistent' ORDER BY created_at DESC LIMIT 1")
    )
    row = result.first()
    assert row is not None
    assert row.status_code >= 400


@pytest.mark.asyncio
async def test_middleware_includes_request_id_header(db_session):
    """Verify X-Request-ID header is returned."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert "x-request-id" in response.headers
```

### 8.8 Test Execution

```bash
# Run all dashboard tests
cd dashboard && python -m pytest tests/ -v --tb=short

# Run specific query tests
cd dashboard && python -m pytest tests/test_queries_product_health.py -v

# Run with coverage
cd dashboard && python -m pytest tests/ --cov=. --cov-report=term-missing

# Run backend telemetry tests
cd backend && python -m pytest tests/core/test_telemetry_middleware.py -v

# Run all tests (dashboard + backend)
python -m pytest dashboard/tests/ backend/tests/ -v --tb=short
```

---

## 9. Atomic Commit Strategy

### 9.1 Commit Sequence

Each commit is independently buildable and testable. Commits are ordered by dependency.

| # | Commit Message | Files Changed | Depends On | Test Gate |
|---|---------------|---------------|------------|-----------|
| **C1** | `feat(dashboard): scaffold project structure with Docker integration` | `dashboard/Home.py`, `dashboard/Dockerfile`, `dashboard/requirements.txt`, `dashboard/.streamlit/config.toml`, `dashboard/db/__init__.py`, `dashboard/db/connection.py`, `dashboard/pages/` (empty `__init__.py`), `dashboard/components/` (empty `__init__.py`), `dashboard/queries/` (empty `__init__.py`), `dashboard/tests/__init__.py`, `dashboard/tests/conftest.py`, `docker-compose.yml` (add dashboard service) | -- | Dashboard container builds and starts; `GET /_stcore/health` returns 200; Home.py loads without error |
| **C2** | `feat(dashboard): add shared filter components and metric card helpers` | `dashboard/components/filters.py`, `dashboard/components/metrics.py`, `dashboard/tests/test_components_filters.py` | C1 | Filter tests pass; `render_time_filter()` returns valid date range |
| **C3** | `feat(dashboard): add Plotly chart builders (funnel, heatmap, timeseries, pie)` | `dashboard/components/charts.py`, `dashboard/tests/test_components_charts.py` | C1 | All chart builder tests pass; each function returns valid Plotly Figure |
| **C4** | `feat(dashboard): add product health queries with tests` | `dashboard/queries/product_health.py`, `dashboard/tests/test_queries_product_health.py` | C1 | All 15+ product query tests pass against test DB |
| **C5** | `feat(dashboard): implement Product Health page` | `dashboard/pages/2_Product_Health.py`, `dashboard/tests/test_pages_smoke.py` (add product test) | C2, C3, C4 | Page loads without error; funnel renders; retention heatmap renders |
| **C6** | `feat(dashboard): add AI quality queries with tests` | `dashboard/queries/ai_quality.py`, `dashboard/tests/test_queries_ai_quality.py` | C1 | All AI quality query tests pass |
| **C7** | `feat(dashboard): implement AI Quality page` | `dashboard/pages/3_AI_Quality.py`, `dashboard/tests/test_pages_smoke.py` (add AI test) | C2, C3, C6 | Page loads; confidence distribution chart renders |
| **C8** | `feat(dashboard): add system health queries and runtime checks` | `dashboard/queries/system_health.py`, `dashboard/tests/test_queries_system_health.py` | C1 | Health check functions return expected dict structure |
| **C9** | `feat(dashboard): implement System Health page` | `dashboard/pages/1_System_Health.py`, `dashboard/tests/test_pages_smoke.py` (add system test) | C2, C3, C8 | Page loads; Postgres/Redis status indicators render |
| **C10** | `feat(dashboard): add unit economics queries (placeholder) with tests` | `dashboard/queries/unit_economics.py`, `dashboard/tests/test_queries_unit_economics.py` | C1 | Query functions return empty DataFrames gracefully when tables do not exist |
| **C11** | `feat(dashboard): implement Unit Economics page with placeholder UI` | `dashboard/pages/4_Unit_Economics.py`, `dashboard/tests/test_pages_smoke.py` (add economics test) | C2, C3, C10 | Page loads; shows instrumentation-required placeholders |
| **C12** | `feat(backend): add api_request_log model and telemetry middleware` | `backend/app/models/api_request_log.py`, `backend/app/core/telemetry_middleware.py`, `backend/app/main.py` (register middleware + import model), `backend/app/models/__init__.py`, `backend/tests/core/test_telemetry_middleware.py` | -- | Middleware test: request logged with correct path, status_code, duration_ms; X-Request-ID header returned |
| **C13** | `feat(backend): add ai_inference_log model` | `backend/app/models/ai_inference_log.py`, `backend/app/models/__init__.py` (register model), `backend/tests/test_models.py` (add ai_inference_log creation test) | -- | Model creates table; can insert and query rows |
| **C14** | `feat(backend): instrument LLM photo parser with ai_inference_log` | `backend/app/modules/catalog/photo_interfaces.py` (wrap LLM call with timing + token extraction), `backend/tests/modules/catalog/test_photo_scan.py` (verify ai_inference_log row created) | C13 | Photo parse creates ai_inference_log row with provider='litellm', duration_ms, tokens, cost |
| **C15** | `feat(backend): instrument Spoonacular client with ai_inference_log` | `backend/app/modules/recommendations/spoonacular.py` (wrap API call with timing), `backend/tests/modules/recommendations/test_spoonacular.py` (verify ai_inference_log row created) | C13 | Spoonacular call creates ai_inference_log row with provider='spoonacular', duration_ms, points |
| **C16** | `feat(backend): add LLM and Spoonacular cost rate configuration` | `backend/app/core/config.py` (add LLM_INPUT_COST_PER_1M, LLM_OUTPUT_COST_PER_1M, SPOONACULAR_POINT_COST) | -- | Config loads with default cost rates; settings accessible from config object |
| **C17** | `feat(dashboard): enable live system health metrics from api_request_log` | `dashboard/queries/system_health.py` (add latency/error/throughput queries), `dashboard/pages/1_System_Health.py` (render live charts when table exists) | C9, C12 | System Health page shows latency/error/throughput charts when api_request_log has data |
| **C18** | `feat(dashboard): enable live unit economics from ai_inference_log` | `dashboard/queries/unit_economics.py` (update with real queries), `dashboard/pages/4_Unit_Economics.py` (render live cost data when table exists) | C11, C14, C15 | Unit Economics page shows cost charts when ai_inference_log has data |

### 9.2 Commit Dependency Graph

```
C1 (scaffold)
├── C2 (filters + metrics) ─────────┐
├── C3 (charts) ────────────────────┤
├── C4 (product queries) ──────────┤
│   └── C5 (Product Health page) ←── C2 + C3 + C4
├── C6 (AI queries) ───────────────┤
│   └── C7 (AI Quality page) ←───── C2 + C3 + C6
├── C8 (system queries) ──────────┤
│   └── C9 (System Health page) ←── C2 + C3 + C8
│       └── C17 (live system) ←───── C9 + C12
├── C10 (econ queries) ───────────┤
│   └── C11 (Unit Econ page) ←───── C2 + C3 + C10
│       └── C18 (live econ) ←─────── C11 + C14 + C15
│
C12 (api_request_log + middleware) ── standalone backend change
C13 (ai_inference_log model) ──────── standalone backend change
├── C14 (instrument LLM parser) ←──── C13
├── C15 (instrument Spoonacular) ←─── C13
C16 (cost config) ─────────────────── standalone backend change
```

### 9.3 Parallel Work Streams

Two developers can work in parallel:

- **Stream A (Dashboard):** C1 -> C2 + C3 (parallel) -> C4 -> C5 -> C6 -> C7 -> C8 -> C9 -> C10 -> C11
- **Stream B (Backend Instrumentation):** C12 -> C13 -> C14 + C15 (parallel) -> C16
- **Integration:** C17 (needs Stream A: C9 + Stream B: C12), C18 (needs Stream A: C11 + Stream B: C14 + C15)

---

## 10. Work Plan

### 10.1 Phase Overview

| Phase | Description | Duration | Commits |
|-------|-------------|----------|---------|
| **Phase 1** | Dashboard scaffold + shared components | 1 day | C1, C2, C3 |
| **Phase 2** | Product Health (highest value, most E+D data) | 1.5 days | C4, C5 |
| **Phase 3** | AI Quality + System Health | 1.5 days | C6, C7, C8, C9 |
| **Phase 4** | Unit Economics (placeholder) | 0.5 day | C10, C11 |
| **Phase 5** | Backend instrumentation | 2 days | C12, C13, C14, C15, C16 |
| **Phase 6** | Integration (live metrics) | 1 day | C17, C18 |
| **Total** | | **~7.5 dev-days** | **18 commits** |

### 10.2 Detailed Task Breakdown

#### Phase 1: Dashboard Scaffold (Day 1)

| Task | Subtasks | Commit | Est. Hours |
|------|----------|--------|-----------|
| T1.1 Scaffold project structure | Create `dashboard/` directory tree: `Home.py`, `Dockerfile`, `requirements.txt`, `.streamlit/config.toml`, empty `__init__.py` files for all subpackages | C1 | 1h |
| T1.2 Database connection layer | Implement `db/connection.py` with `@st.cache_resource` engine, `run_query()`, `check_table_exists()` | C1 | 1h |
| T1.3 Docker Compose integration | Add `dashboard` service to `docker-compose.yml` with depends_on, env vars, healthcheck | C1 | 0.5h |
| T1.4 Test infrastructure | Create `tests/conftest.py` with `test_engine`, `db_conn`, `sample_users`, `sample_household`, `sample_items`, `sample_events` fixtures | C1 | 1h |
| T1.5 Shared filter components | Implement `components/filters.py` (time range selector, source filter, refresh controls); write `tests/test_components_filters.py` | C2 | 1.5h |
| T1.6 Metric card helpers | Implement `components/metrics.py` (KPI cards, placeholder pattern, conditional rendering) | C2 | 0.5h |
| T1.7 Chart builders | Implement `components/charts.py` with `create_funnel_chart()`, `create_retention_heatmap()`, `create_timeseries()`, `create_pie_chart()`, `create_stacked_area()`; write `tests/test_components_charts.py` | C3 | 2h |

#### Phase 2: Product Health (Day 2 -- Day 3 morning)

| Task | Subtasks | Commit | Est. Hours |
|------|----------|--------|-----------|
| T2.1 Product health queries | Implement all Q-P* queries from Section 5.2 as Python functions in `queries/product_health.py`: `get_total_users`, `get_signup_trend`, `get_onboarding_funnel`, `get_activation_rate`, `get_wau`, `get_mau`, `get_wau_trend`, `get_retention_cohorts`, `get_waste_ratio`, `get_waste_ratio_trend`, `get_key_action_counts`, `get_item_source_distribution`, `get_household_size_distribution`, `get_notification_adoption`, `get_device_platforms` | C4 | 3h |
| T2.2 Product health query tests | Write `tests/test_queries_product_health.py` with classes: `TestTotalUsers`, `TestOnboardingFunnel`, `TestActivationRate`, `TestWasteRatio`, `TestWAU`, `TestRetentionCohorts`, `TestItemSourceDistribution`, `TestHouseholdSize` | C4 | 3h |
| T2.3 Product Health page | Assemble `pages/2_Product_Health.py`: 4 KPI cards (Total Users, WAU, Activation Rate, Waste Reduction), onboarding funnel chart, retention cohort heatmap, signup trend line, item source pie, household size histogram, key actions multi-line, notification adoption metric, device platform pie | C5 | 3h |
| T2.4 Product Health smoke test | Add `TestProductHealthPage` to `tests/test_pages_smoke.py` | C5 | 0.5h |

#### Phase 3: AI Quality + System Health (Day 3 afternoon -- Day 4)

| Task | Subtasks | Commit | Est. Hours |
|------|----------|--------|-----------|
| T3.1 AI quality queries | Implement `queries/ai_quality.py`: `get_avg_confidence`, `get_confidence_distribution`, `get_barcode_item_trend`, `get_photo_fallback_rate`, `get_photo_fallback_trend`, `get_recommendation_session_stats`, `get_photo_item_count`, `get_barcode_item_count`, `get_recommendation_session_count` | C6 | 2h |
| T3.2 AI quality query tests | Write `tests/test_queries_ai_quality.py`: test confidence returns 0-1 range, test distribution buckets sum correctly, test empty data handling | C6 | 2h |
| T3.3 AI Quality page | Assemble `pages/3_AI_Quality.py`: 4 KPI cards (Photo Items, Avg Confidence, Barcode Items, Rec Sessions), confidence distribution stacked area, photo parse metrics (avg confidence trend, fallback rate trend), recommendation quality (recipes shown per session line), placeholder section for LLM latency and coverage_pct | C7 | 2h |
| T3.4 System health queries | Implement `queries/system_health.py`: `check_backend_health()`, `check_redis_health()`, `check_celery_queue_depth()`, `check_postgres_health()`, `get_api_latency_by_endpoint()` (guarded by table check), `get_error_rate_by_endpoint()` (guarded), `get_throughput_over_time()` (guarded) | C8 | 2h |
| T3.5 System health tests | Write `tests/test_queries_system_health.py`: test health check returns dict with 'status' key, test Redis check handles connection error, test guarded queries return empty when table missing | C8 | 1h |
| T3.6 System Health page | Assemble `pages/1_System_Health.py`: 4 KPI cards (Uptime, Avg Latency, Error Rate, Req/sec) with placeholders for missing api_request_log, API latency timeseries placeholder, error rate bar placeholder, throughput area placeholder, infrastructure status row (Postgres, Redis, Celery queue depth, Backend version) | C9 | 2h |

#### Phase 4: Unit Economics Placeholder (Day 5 morning)

| Task | Subtasks | Commit | Est. Hours |
|------|----------|--------|-----------|
| T4.1 Unit economics queries | Implement `queries/unit_economics.py`: `get_llm_cost_trend()`, `get_spoonacular_cost_trend()`, `get_total_cost_trend()`, `get_cost_per_active_user()` — all guarded by `check_table_exists('ai_inference_log')` returning empty DataFrame when table absent | C10 | 1.5h |
| T4.2 Unit economics tests | Write `tests/test_queries_unit_economics.py`: test graceful handling when `ai_inference_log` table does not exist, test queries return correct columns when table exists with sample data | C10 | 1h |
| T4.3 Unit Economics page | Assemble `pages/4_Unit_Economics.py`: 3 KPI cards (LLM Cost, Spoonacular Cost, Cost/Active User) all with `placeholder_metric()`, cost trend stacked area placeholder, cost per parse histogram placeholder, info banner explaining instrumentation requirement | C11 | 1h |

#### Phase 5: Backend Instrumentation (Day 5 afternoon -- Day 6, parallel stream)

| Task | Subtasks | Commit | Est. Hours |
|------|----------|--------|-----------|
| T5.1 API request log model | Create `backend/app/models/api_request_log.py` with `ApiRequestLog` class; add import to `backend/app/models/__init__.py` so `Base.metadata.create_all` picks it up | C12 | 1h |
| T5.2 Telemetry middleware | Create `backend/app/core/telemetry_middleware.py` with `TelemetryMiddleware` class; register in `backend/app/main.py` via `app.add_middleware(TelemetryMiddleware)` | C12 | 2h |
| T5.3 Middleware tests | Write `backend/tests/core/test_telemetry_middleware.py`: test successful request logged, test error request logged, test X-Request-ID header returned, test duration_ms is positive | C12 | 2h |
| T5.4 AI inference log model | Create `backend/app/models/ai_inference_log.py` with `AiInferenceLog` class; add import to `backend/app/models/__init__.py` | C13 | 1h |
| T5.5 AI inference log model test | Add test to `backend/tests/test_models.py` verifying `ai_inference_log` table can be created and rows inserted | C13 | 0.5h |
| T5.6 Instrument LLM parser | Modify `LLMPhotoParser.parse_image()` in `backend/app/modules/catalog/photo_interfaces.py:45-108`: add `time.perf_counter()` around HTTP call, extract `usage.prompt_tokens` and `usage.completion_tokens` from response, compute `cost_usd`, create `AiInferenceLog` row in try/except | C14 | 2h |
| T5.7 LLM instrumentation tests | Update `backend/tests/modules/catalog/test_photo_scan.py`: verify `ai_inference_log` row created with `provider='litellm'`, correct `operation='photo_parse'`, non-null `duration_ms` | C14 | 1.5h |
| T5.8 Instrument Spoonacular | Modify `SpoonacularClient.search_recipes()` in `backend/app/modules/recommendations/spoonacular.py`: add timing, create `AiInferenceLog` row with `provider='spoonacular'`, `operation='recipe_search'`, `api_points_used=1` | C15 | 1.5h |
| T5.9 Spoonacular instrumentation tests | Update `backend/tests/modules/recommendations/test_spoonacular.py`: verify `ai_inference_log` row created with `provider='spoonacular'` | C15 | 1h |
| T5.10 Cost rate config | Add `LLM_INPUT_COST_PER_1M`, `LLM_OUTPUT_COST_PER_1M`, `SPOONACULAR_POINT_COST` to `Settings` class in `backend/app/core/config.py` with default values | C16 | 0.5h |

#### Phase 6: Integration (Day 7)

| Task | Subtasks | Commit | Est. Hours |
|------|----------|--------|-----------|
| T6.1 Enable live system health metrics | Update `dashboard/queries/system_health.py`: add latency/error/throughput queries using `api_request_log`; update `dashboard/pages/1_System_Health.py`: conditionally render real charts when `api_request_log` exists, keep placeholders otherwise | C17 | 2h |
| T6.2 Enable live unit economics | Update `dashboard/queries/unit_economics.py`: add real queries using `ai_inference_log`; update `dashboard/pages/4_Unit_Economics.py`: conditionally render real cost charts when `ai_inference_log` exists | C18 | 2h |
| T6.3 End-to-end validation | Manual smoke test: `docker-compose up -d`, run `python scripts/seed_data.py`, make several API calls via curl, verify all 4 dashboard pages at `http://localhost:8501` show expected data | -- | 2h |

### 10.3 Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| `api_request_log` writes slow down API responses | High -- could violate <3s P95 SLO for item creation | Medium | Use fire-and-forget `asyncio.create_task` for log writes; wrap in try/except so telemetry failure never breaks API; batch inserts if needed |
| `ai_inference_log` changes break LLM parser | Medium -- could break photo parsing flow | Low | Wrap all instrumentation in try/except; log failure does not fail the parse; test both success and failure paths |
| PostgreSQL query load from dashboard | Medium -- dashboard queries on same DB instance | Low | Read-only queries only; `@st.cache_data` with TTL prevents hammering; small `pool_size=3` for dashboard; queries use indexes on `created_at` and `path` |
| Streamlit `AppTest` flakiness | Low -- smoke tests may be sensitive to environment | Medium | Use `--server.headless=true`; AppTest is headless-compatible; keep smoke tests minimal (just check page loads) |
| `json_array_length` compatibility with JSON column | Low -- `recipes_shown` is stored as JSON not JSONB | Low | Cast explicitly: `json_array_length(recipes_shown::text::json)` in Q-A-Rec query |
| Test DB isolation | Medium -- tests could affect each other | Low | Use transactional fixtures that rollback after each test (see `conftest.py` `db_conn` fixture) |

### 10.4 Definition of Done

The dashboard implementation is complete when:

1. All 4 pages render without errors in Docker Compose stack (`docker-compose up -d`)
2. All E + D metrics (18 metrics) display real data from the database
3. All M metrics (12 metrics) show clear placeholder messages identifying what instrumentation is needed
4. All SQL query tests pass: `cd dashboard && python -m pytest tests/test_queries_*.py -v`
5. All chart component tests pass: `cd dashboard && python -m pytest tests/test_components_*.py -v`
6. All Streamlit smoke tests pass: `cd dashboard && python -m pytest tests/test_pages_smoke.py -v`
7. All backend telemetry tests pass: `cd backend && python -m pytest tests/core/test_telemetry_middleware.py tests/test_models.py -v`
8. Time range filters work across all pages (session state propagation verified)
9. Refresh button clears cache and reruns; auto-refresh triggers rerun after 60s
10. Dashboard container healthcheck passes: `curl -f http://localhost:8501/_stcore/health`
11. North Star metric (waste reduction ratio) is prominently displayed as first KPI on Product Health page
12. Infrastructure status indicators (Postgres, Redis, Celery, Backend) are live on System Health page

### 10.5 GitHub Actions CI Extension

Add a new job to `.github/workflows/backend.yml`:

```yaml
  dashboard-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: fridgefriend
          POSTGRES_PASSWORD: fridgefriend
          POSTGRES_DB: fridgefriend_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dashboard dependencies
        run: pip install -r dashboard/requirements.txt
      - name: Install backend for schema creation
        run: pip install -e backend/[dev]
      - name: Create test database schema
        run: python -c "
          from sqlalchemy import create_engine;
          from app.models import Base;
          engine = create_engine('postgresql://fridgefriend:fridgefriend@localhost:5432/fridgefriend_test');
          Base.metadata.create_all(engine)"
        working-directory: backend
      - name: Run dashboard tests
        run: python -m pytest tests/ -v --tb=short
        working-directory: dashboard
        env:
          DATABASE_URL: postgresql://fridgefriend:fridgefriend@localhost:5432/fridgefriend_test
```

---

## Appendix A: Glossary

| Term | Definition |
|------|-----------|
| WAU | Weekly Active Users -- distinct users with >=1 `inventory_event` in trailing 7 days |
| MAU | Monthly Active Users -- distinct users with >=1 `inventory_event` in trailing 30 days |
| Activation | User who added >=1 inventory item within 24 hours of signup (based on `users.created_at` vs first `inventory_items.created_at`) |
| Waste Reduction Ratio | `used / (used + discarded)` -- the North Star metric. Derived from `inventory_items.status` column |
| Urgency Bucket | Classification from `backend/app/modules/expiry/urgency.py:7-11`: EXPIRED (days < 0), TODAY (days <= 1), THIS_WEEK (days <= 7), SAFE_LATER (days > 7) |
| Confidence Score | Float 0.0-1.0 assigned to inventory items. For photo-parsed items, represents the LLM's certainty of item identification |
| Fallback Rate | Percentage of photo parses where confidence < 0.5, requiring user editing of the draft. Threshold confirmed as 0.5 per product spec |
| Coverage Pct | Fraction of recipe ingredients available in user's inventory. Computed at runtime in `backend/app/modules/recommendations/scorer.py:65` but not persisted |
| Use Soon Score | Bonus score for recipes that use expiring items. Capped at 0.4 per `scorer.py:114`. Items expiring today/expired get 0.3; this week gets 0.15 |
| Idempotency Key | Unique token sent via `Idempotency-Key` header on all write endpoints to prevent duplicate operations. Cached in Redis/memory with 86400s TTL |

## Appendix B: Environment Variables (Dashboard Service)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://fridgefriend:fridgefriend@db:5432/fridgefriend` | Synchronous PostgreSQL connection string for dashboard reads |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection for queue depth checks and connectivity verification |
| `BACKEND_HEALTH_URL` | `http://backend:8000/health` | Backend health endpoint URL for uptime polling |

## Appendix C: File-to-Table Reference Map

Maps each dashboard query to the exact backend model file defining the source table.

| Table | Backend Model File | Key Columns for Dashboard |
|-------|-------------------|--------------------------|
| `users` | `backend/app/models/user.py` | `id`, `email`, `created_at` |
| `households` | `backend/app/models/household.py` | `id`, `name`, `created_at` |
| `household_members` | `backend/app/models/household.py` | `household_id`, `user_id`, `role`, `is_active` |
| `inventory_items` | `backend/app/models/inventory_item.py` | `user_id`, `household_id`, `source` (manual/barcode/photo), `status` (active/used/discarded/frozen), `confidence`, `estimated_expiry_date`, `canonical_name`, `created_at`, `updated_at` |
| `inventory_events` | `backend/app/models/events.py:15-28` | `user_id`, `household_id`, `item_id`, `action` (added/updated/status_updated/removed/undone), `previous_state`, `new_state`, `created_at` |
| `recommendation_sessions` | `backend/app/models/events.py:43-55` | `household_id`, `request_params`, `recipes_shown`, `recipe_selected_id`, `created_at` |
| `meal_plans` | `backend/app/models/meal_plan.py` | `user_id`, `household_id`, `days`, `servings`, `created_at` |
| `notification_preferences` | `backend/app/models/notification.py` | `user_id`, `expiry_reminder_enabled`, `reminder_days_before` |
| `device_tokens` | `backend/app/models/notification.py` | `user_id`, `platform` (ios/android/web), `token` |
| `analytics_events` | `backend/app/models/events.py:31-40` | `user_id`, `event_type`, `payload` (JSON), `created_at` |
| `api_request_log` | `backend/app/models/api_request_log.py` (new) | `method`, `path`, `status_code`, `duration_ms`, `user_id`, `request_id`, `created_at` |
| `ai_inference_log` | `backend/app/models/ai_inference_log.py` (new) | `provider`, `operation`, `model`, `duration_ms`, `status`, `input_tokens`, `output_tokens`, `cost_usd`, `api_points_used`, `created_at` |


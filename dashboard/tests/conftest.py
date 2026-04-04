"""Shared test fixtures for dashboard tests."""

from __future__ import annotations

import os
import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://fridgefriend:fridgefriend@localhost:5432/fridgefriend_test",
)

# Minimal DDL for dashboard-relevant tables (no ORM dependency on backend models).
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS households (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    invite_code VARCHAR(20) UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS household_members (
    id UUID PRIMARY KEY,
    household_id UUID REFERENCES households(id),
    user_id UUID REFERENCES users(id),
    role VARCHAR(20) NOT NULL DEFAULT 'member',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS inventory_items (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    household_id UUID REFERENCES households(id),
    display_name VARCHAR(255) NOT NULL,
    quantity FLOAT NOT NULL,
    unit VARCHAR(50) NOT NULL,
    storage_location VARCHAR(100) NOT NULL,
    estimated_expiry_date DATE NOT NULL,
    confidence FLOAT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    source VARCHAR(20) NOT NULL DEFAULT 'manual',
    canonical_name VARCHAR(255) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS inventory_events (
    id UUID PRIMARY KEY,
    household_id UUID REFERENCES households(id),
    user_id UUID REFERENCES users(id),
    item_id UUID,
    action VARCHAR(50) NOT NULL,
    previous_state JSONB DEFAULT '{}',
    new_state JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS recommendation_sessions (
    id UUID PRIMARY KEY,
    household_id UUID REFERENCES households(id),
    request_params JSONB DEFAULT '{}',
    recipes_shown JSONB DEFAULT '[]',
    recipe_selected_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS meal_plans (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    household_id UUID REFERENCES households(id),
    days INTEGER NOT NULL,
    servings INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS notification_preferences (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) UNIQUE,
    expiry_reminder_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    reminder_days_before INTEGER NOT NULL DEFAULT 2,
    quiet_hours_start INTEGER NOT NULL DEFAULT 22,
    quiet_hours_end INTEGER NOT NULL DEFAULT 8,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS device_tokens (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    platform VARCHAR(20) NOT NULL,
    token VARCHAR(500) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    event_type VARCHAR(100) NOT NULL,
    payload JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine and initialize schema."""
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text(SCHEMA_SQL))
        conn.commit()
    yield engine
    engine.dispose()


@pytest.fixture()
def db_conn(test_engine):
    """Provide a transactional connection that rolls back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    yield connection
    transaction.rollback()
    connection.close()


@pytest.fixture()
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


@pytest.fixture()
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


@pytest.fixture()
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


@pytest.fixture()
def sample_events(db_conn, sample_users, sample_household, sample_items):
    """Insert inventory events for retention/WAU testing."""
    for week in range(4):
        for uid in sample_users[: 7 - week]:  # Decreasing retention
            db_conn.execute(
                text(
                    "INSERT INTO inventory_events "
                    "(id, household_id, user_id, item_id, action, "
                    "previous_state, new_state, created_at, updated_at) "
                    "VALUES (:id, :hh, :uid, NULL, 'added', "
                    "'{}'::jsonb, '{}'::jsonb, :ts, :ts)"
                ),
                {
                    "id": uuid.uuid4(),
                    "hh": sample_household,
                    "uid": uid,
                    "ts": datetime.now(UTC) - timedelta(weeks=week),
                },
            )


@pytest.fixture()
def sample_recommendation_sessions(db_conn, sample_household):
    """Insert recommendation sessions with recipes_shown."""
    sessions = []
    for i in range(5):
        session_id = uuid.uuid4()
        recipes = [{"id": str(uuid.uuid4()), "title": f"Recipe {j}"} for j in range(3 + i)]
        db_conn.execute(
            text(
                "INSERT INTO recommendation_sessions "
                "(id, household_id, request_params, recipes_shown, created_at, updated_at) "
                "VALUES (:id, :hh, :params, :recipes, :ts, :ts)"
            ),
            {
                "id": session_id,
                "hh": sample_household,
                "params": "{}",
                "recipes": str(recipes).replace("'", '"'),
                "ts": datetime.now(UTC) - timedelta(days=i),
            },
        )
        sessions.append(session_id)
    return sessions


@pytest.fixture()
def sample_meal_plans(db_conn, sample_users, sample_household):
    """Insert sample meal plans."""
    plans = []
    for i, uid in enumerate(sample_users[:3]):
        plan_id = uuid.uuid4()
        db_conn.execute(
            text(
                "INSERT INTO meal_plans "
                "(id, user_id, household_id, days, servings, created_at, updated_at) "
                "VALUES (:id, :uid, :hh, :days, :servings, :ts, :ts)"
            ),
            {
                "id": plan_id,
                "uid": uid,
                "hh": sample_household,
                "days": 7,
                "servings": 2,
                "ts": datetime.now(UTC) - timedelta(days=i * 2),
            },
        )
        plans.append(plan_id)
    return plans


@pytest.fixture()
def sample_notification_prefs(db_conn, sample_users):
    """Insert notification preferences — 7 enabled, 3 disabled."""
    for i, uid in enumerate(sample_users):
        db_conn.execute(
            text(
                "INSERT INTO notification_preferences "
                "(id, user_id, expiry_reminder_enabled, reminder_days_before, "
                "quiet_hours_start, quiet_hours_end, created_at, updated_at) "
                "VALUES (:id, :uid, :enabled, 2, 22, 8, :ts, :ts)"
            ),
            {
                "id": uuid.uuid4(),
                "uid": uid,
                "enabled": i < 7,
                "ts": datetime.now(UTC),
            },
        )


@pytest.fixture()
def sample_device_tokens(db_conn, sample_users):
    """Insert device tokens — mix of iOS and Android."""
    platforms = ["ios", "android", "ios", "android", "ios"]
    for i, uid in enumerate(sample_users[:5]):
        db_conn.execute(
            text(
                "INSERT INTO device_tokens "
                "(id, user_id, platform, token, created_at, updated_at) "
                "VALUES (:id, :uid, :platform, :token, :ts, :ts)"
            ),
            {
                "id": uuid.uuid4(),
                "uid": uid,
                "platform": platforms[i % len(platforms)],
                "token": f"token-{i}",
                "ts": datetime.now(UTC),
            },
        )

"""Database connection layer for the analytics dashboard."""

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

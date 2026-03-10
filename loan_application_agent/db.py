"""Database connection layer for PostgreSQL."""

import os
import json
import psycopg2
import psycopg2.extras
from contextlib import contextmanager

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://riteshkumar@localhost:5433/loan_agent"
)


@contextmanager
def get_connection():
    """Get a database connection from the pool."""
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_all(query: str, params: tuple = ()) -> list[dict]:
    """Execute query and return all rows as dictionaries."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]


def fetch_one(query: str, params: tuple = ()) -> dict | None:
    """Execute query and return first row as dictionary."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None


def execute(query: str, params: tuple = ()) -> None:
    """Execute a query without returning results."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)


def execute_returning(query: str, params: tuple = ()) -> dict | None:
    """Execute a query and return the result (for INSERT ... RETURNING)."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None

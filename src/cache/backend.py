"""
Database backend — local SQLite OR shared cloud PostgreSQL, same code.

How it picks:
  * No DATABASE_URL set  -> local SQLite file at data/cache.db (great for testing).
  * DATABASE_URL=postgresql://...  -> shared hosted PostgreSQL (for production,
    where the worker and every customer share ONE cache).

The rest of the app doesn't care which one is active. We write all SQL with "?"
placeholders and translate to "%s" for PostgreSQL here, and we use ANSI
"INSERT ... ON CONFLICT ... DO UPDATE" upserts that work on BOTH engines, so the
schema and data are identical wherever it runs.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager

from config.settings import DATA_DIR, _secret

DATABASE_URL = _secret("DATABASE_URL")
IS_POSTGRES = DATABASE_URL.startswith(("postgres://", "postgresql://"))

SQLITE_PATH = DATA_DIR / "cache.db"


def backend_name() -> str:
    return "PostgreSQL (shared cloud)" if IS_POSTGRES else "SQLite (local file)"


def _translate(sql: str) -> str:
    """SQLite uses '?' placeholders; psycopg uses '%s'."""
    return sql.replace("?", "%s") if IS_POSTGRES else sql


def ddl(stmt: str) -> str:
    """Adjust a CREATE TABLE statement for the active engine's type names."""
    if IS_POSTGRES:
        # SQLite's flexible REAL -> Postgres DOUBLE PRECISION (safe for prices).
        return stmt.replace(" REAL", " DOUBLE PRECISION")
    return stmt


class _Conn:
    """Thin wrapper so callers use the same .execute()/.commit() on both engines."""

    def __init__(self, raw):
        self._raw = raw

    def execute(self, sql: str, params=()):
        return self._raw.execute(_translate(sql), params)

    def commit(self):
        self._raw.commit()

    def rollback(self):
        self._raw.rollback()

    def close(self):
        self._raw.close()


@contextmanager
def raw_connection():
    """Open a connection to whichever backend is configured."""
    if IS_POSTGRES:
        import psycopg
        from psycopg.rows import dict_row
        raw = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    else:
        SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
        raw = sqlite3.connect(SQLITE_PATH)
        raw.row_factory = sqlite3.Row  # rows accessible by column name

    conn = _Conn(raw)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

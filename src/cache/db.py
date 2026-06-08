"""
SQLite/PostgreSQL cache — the heart of low cost-per-user.

Everything is stored in ONE shared store keyed by property/address, never per
user. With a hosted PostgreSQL (DATABASE_URL set), the background worker and all
customers share the SAME cache, so a listing viewed by 500 people still costs one
lookup + one image fetch total. Locally (no DATABASE_URL) it's a SQLite file.

This module manages:
  * api_cache      — value/rent/streetview/aerial responses, with EXPIRY.
  * listings       — for-sale homes, with price-drop detection across runs.
  * price_history  — every price we've seen, per listing.
  * api_usage      — every BILLABLE call, so we can watch cost.
  * cache_counters — cache hits vs misses, to prove the shared cache is working.
  * user_usage     — per-user monthly billable lookups, for the soft cap.
  * worker_runs    — history of background-worker refreshes (what each one cost).
  * meta           — small key/value store (e.g. last-sync timestamps).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from src.cache import backend

# Schema as a list of idempotent CREATE statements (run on every connect).
# No AUTOINCREMENT/SERIAL anywhere — ids are natural keys — so it's identical on
# SQLite and PostgreSQL.
_SCHEMA = [
    """CREATE TABLE IF NOT EXISTS listings (
        id TEXT PRIMARY KEY, address TEXT, city TEXT, zip_code TEXT,
        list_price REAL, previous_price REAL, payload TEXT,
        first_seen TEXT, last_seen TEXT)""",
    """CREATE TABLE IF NOT EXISTS price_history (
        listing_id TEXT, price REAL, seen_at TEXT)""",
    """CREATE TABLE IF NOT EXISTS api_cache (
        cache_key TEXT PRIMARY KEY, kind TEXT, payload TEXT, fetched_at TEXT)""",
    """CREATE TABLE IF NOT EXISTS api_usage (kind TEXT, called_at TEXT)""",
    """CREATE TABLE IF NOT EXISTS cache_counters (
        source TEXT PRIMARY KEY, hits INTEGER DEFAULT 0, misses INTEGER DEFAULT 0)""",
    """CREATE TABLE IF NOT EXISTS user_usage (
        user_id TEXT, month TEXT, source TEXT, n INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, month, source))""",
    """CREATE TABLE IF NOT EXISTS worker_runs (
        run_id TEXT PRIMARY KEY, started_at TEXT, finished_at TEXT, status TEXT,
        cities INTEGER, new_count INTEGER, updated_count INTEGER,
        estimates_updated INTEGER, billable_calls INTEGER, notes TEXT)""",
    """CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)""",
]


def connect():
    """Open the configured backend and make sure tables exist."""
    cm = backend.raw_connection()
    conn = cm.__enter__()
    try:
        for stmt in _SCHEMA:
            conn.execute(backend.ddl(stmt))
    except Exception:
        cm.__exit__(None, None, None)
        raise
    # Return a small object that closes the context manager on exit.
    return _ConnSession(cm, conn)


class _ConnSession:
    """Lets callers keep using `with db.connect() as conn:`."""

    def __init__(self, cm, conn):
        self._cm = cm
        self._conn = conn

    def __enter__(self):
        return self._conn

    def __exit__(self, *exc):
        return self._cm.__exit__(*exc)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return _now().isoformat()


# --- Shared API cache, WITH EXPIRY ----------------------------------------

def cache_get(cache_key: str, max_age_seconds: int | None = None):
    """Return cached payload, or None if missing OR older than max_age_seconds."""
    with connect() as conn:
        row = conn.execute(
            "SELECT payload, fetched_at FROM api_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
    if not row:
        return None
    if max_age_seconds is not None and row["fetched_at"]:
        try:
            fetched = datetime.fromisoformat(row["fetched_at"])
            if (_now() - fetched).total_seconds() > max_age_seconds:
                return None
        except ValueError:
            pass
    return json.loads(row["payload"])


def cache_put(cache_key: str, kind: str, payload, when_iso: str | None = None):
    with connect() as conn:
        conn.execute(
            "INSERT INTO api_cache (cache_key, kind, payload, fetched_at) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(cache_key) DO UPDATE SET kind=excluded.kind, "
            "payload=excluded.payload, fetched_at=excluded.fetched_at",
            (cache_key, kind, json.dumps(payload), when_iso or now_iso()),
        )


# --- Billable-call usage ---------------------------------------------------

def record_usage(kind: str, when_iso: str | None = None):
    with connect() as conn:
        conn.execute("INSERT INTO api_usage (kind, called_at) VALUES (?, ?)",
                     (kind, when_iso or now_iso()))


def usage_summary() -> dict:
    with connect() as conn:
        rows = conn.execute(
            "SELECT kind, COUNT(*) AS n FROM api_usage GROUP BY kind"
        ).fetchall()
        return {r["kind"]: r["n"] for r in rows}


def total_billable_calls() -> int:
    with connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM api_usage").fetchone()
        return int(row["n"])


# --- Cache hit/miss counters ----------------------------------------------

def note_cache_hit(source: str):
    _bump_counter(source, hit=True)


def note_cache_miss(source: str):
    _bump_counter(source, hit=False)


def _bump_counter(source: str, hit: bool):
    col = "hits" if hit else "misses"
    with connect() as conn:
        conn.execute(
            "INSERT INTO cache_counters (source, hits, misses) VALUES (?, ?, ?) "
            "ON CONFLICT(source) DO UPDATE SET " + col + " = cache_counters."
            + col + " + 1",
            (source, 1 if hit else 0, 0 if hit else 1),
        )


def cache_stats() -> dict:
    with connect() as conn:
        rows = conn.execute(
            "SELECT source, hits, misses FROM cache_counters"
        ).fetchall()
    stats: dict = {}
    total_h = total_m = 0
    for r in rows:
        h, m = r["hits"], r["misses"]
        total_h += h
        total_m += m
        denom = h + m
        stats[r["source"]] = {"hits": h, "misses": m,
                              "hit_rate": (h / denom) if denom else 0.0}
    denom = total_h + total_m
    stats["overall"] = {"hits": total_h, "misses": total_m,
                        "hit_rate": (total_h / denom) if denom else 0.0}
    return stats


# --- Per-user monthly usage (soft cap) -------------------------------------

def current_month() -> str:
    return _now().strftime("%Y-%m")


def record_user_lookup(user_id: str, source: str, count: int = 1):
    with connect() as conn:
        conn.execute(
            "INSERT INTO user_usage (user_id, month, source, n) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(user_id, month, source) DO UPDATE SET "
            "n = user_usage.n + ?",
            (user_id, current_month(), source, count, count),
        )


def user_lookup_count(user_id: str, month: str | None = None) -> int:
    month = month or current_month()
    with connect() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(n), 0) AS total FROM user_usage "
            "WHERE user_id = ? AND month = ?", (user_id, month),
        ).fetchone()
        return int(row["total"])


# --- Worker run history ----------------------------------------------------

def record_worker_run(run: dict):
    """Insert (or update) one worker-run record. Keyed by run_id -> idempotent."""
    with connect() as conn:
        conn.execute(
            "INSERT INTO worker_runs (run_id, started_at, finished_at, status, "
            "cities, new_count, updated_count, estimates_updated, billable_calls, "
            "notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(run_id) DO UPDATE SET finished_at=excluded.finished_at, "
            "status=excluded.status, cities=excluded.cities, "
            "new_count=excluded.new_count, updated_count=excluded.updated_count, "
            "estimates_updated=excluded.estimates_updated, "
            "billable_calls=excluded.billable_calls, notes=excluded.notes",
            (run["run_id"], run.get("started_at"), run.get("finished_at"),
             run.get("status"), run.get("cities"), run.get("new_count"),
             run.get("updated_count"), run.get("estimates_updated"),
             run.get("billable_calls"), run.get("notes")),
        )


def worker_run_history(limit: int = 20) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM worker_runs ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


# --- Small key/value meta --------------------------------------------------

def set_meta(key: str, value: str):
    with connect() as conn:
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value)
        )


def get_meta(key: str) -> str | None:
    with connect() as conn:
        row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None


# --- Listings + price-drop detection ---------------------------------------

def upsert_listing(listing_id: str, address: str, city: str, zip_code: str,
                   list_price, payload: dict, when_iso: str) -> dict:
    with connect() as conn:
        existing = conn.execute(
            "SELECT list_price FROM listings WHERE id = ?", (listing_id,)
        ).fetchone()

        previous_price = existing["list_price"] if existing else None
        is_new = existing is None
        price_changed = (
            not is_new and previous_price is not None and list_price is not None
            and float(previous_price) != float(list_price)
        )

        if is_new:
            conn.execute(
                "INSERT INTO listings (id, address, city, zip_code, list_price, "
                "previous_price, payload, first_seen, last_seen) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (listing_id, address, city, zip_code, list_price, None,
                 json.dumps(payload), when_iso, when_iso),
            )
        else:
            conn.execute(
                "UPDATE listings SET address=?, city=?, zip_code=?, list_price=?, "
                "previous_price=?, payload=?, last_seen=? WHERE id=?",
                (address, city, zip_code, list_price, previous_price,
                 json.dumps(payload), when_iso, listing_id),
            )

        conn.execute(
            "INSERT INTO price_history (listing_id, price, seen_at) VALUES (?, ?, ?)",
            (listing_id, list_price, when_iso),
        )
        return {"is_new": is_new, "price_changed": price_changed,
                "previous_price": previous_price}

"""
Mortgage rates — FREE Freddie Mac PMMS (weekly 30-yr average), no API key.

Keeps "true monthly cost" honest by using the REAL current 30-year fixed rate
instead of a hand-typed guess. Free public CSV, not billable. Parsed into a tiny
local file (data/mortgage_rate.json) that the app reads with NO network on page
load — same shape as market.py. The worker refreshes it about weekly.

Optional upgrade: set FRED_API_KEY (free) to pull the same rate from the Federal
Reserve (FRED series MORTGAGE30US) instead. If no key is set, Freddie Mac is used
automatically, so this works out of the box.

Sources:
  Freddie Mac PMMS:  https://www.freddiemac.com/pmms
  FRED MORTGAGE30US: https://fred.stlouisfed.org/series/MORTGAGE30US
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Optional

import requests

from config.settings import DATA_DIR, settings
from src.cache import db

PMMS_URL = "https://www.freddiemac.com/pmms/docs/PMMS_history.csv"
FRED_URL = "https://api.stlouisfed.org/fred/series/observations"
DATA_FILE = DATA_DIR / "mortgage_rate.json"
_CACHE: Optional[dict] = None


def _from_fred(api_key: str) -> Optional[dict]:
    """Latest 30-yr fixed rate from FRED (needs a free key). Returns dict or None."""
    params = {
        "series_id": "MORTGAGE30US",
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 1,
    }
    resp = requests.get(FRED_URL, params=params, timeout=30)
    resp.raise_for_status()
    for o in resp.json().get("observations", []):
        v = o.get("value")
        if v not in (None, "", "."):
            return {"rate30": round(float(v), 3), "as_of": o.get("date"),
                    "source": "FRED MORTGAGE30US"}
    return None


def _from_freddie() -> Optional[dict]:
    """Latest 30-yr fixed rate from Freddie Mac's free PMMS CSV (no key)."""
    resp = requests.get(PMMS_URL, timeout=60,
                        headers={"User-Agent": "Underlisted/1.0"})
    resp.raise_for_status()
    latest = None
    for row in csv.DictReader(io.StringIO(resp.text)):
        v = (row.get("pmms30") or "").strip()
        if not v:
            continue
        try:
            rate = float(v)
        except ValueError:
            continue
        # Rows are oldest -> newest, so the last valid one is the current week.
        latest = {"rate30": round(rate, 3), "as_of": (row.get("date") or "").strip(),
                  "source": "Freddie Mac PMMS"}
    return latest


def refresh() -> Optional[dict]:
    """Fetch the latest 30-yr rate (FRED if a key is set, else Freddie Mac) and cache it."""
    data = None
    key = settings.fred_api_key
    if key:
        try:
            data = _from_fred(key)
        except Exception:
            data = None  # fall back to the free no-key source
    if data is None:
        data = _from_freddie()
    if data is None:
        return None
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(data))
    db.set_meta("mortgage_rate:refreshed", db.now_iso())
    global _CACHE
    _CACHE = data
    return data


def _load() -> dict:
    global _CACHE
    if _CACHE is None:
        _CACHE = json.loads(DATA_FILE.read_text()) if DATA_FILE.exists() else {}
    return _CACHE


def current_30yr_rate() -> Optional[float]:
    """Latest cached 30-yr fixed rate as a percent (e.g. 6.72), or None. NO network."""
    r = _load().get("rate30")
    return float(r) if r is not None else None


def current_info() -> dict:
    """The cached {rate30, as_of, source} (may be empty). NO network — safe on page load."""
    return dict(_load())


def ensure_fresh(max_age_days: int = 7) -> Optional[dict]:
    """Refresh only if missing or older than max_age_days (rates move weekly)."""
    last = db.get_meta("mortgage_rate:refreshed")
    if DATA_FILE.exists() and last:
        try:
            if (datetime.now(timezone.utc) - datetime.fromisoformat(last)).days < max_age_days:
                return None
        except ValueError:
            pass
    return refresh()

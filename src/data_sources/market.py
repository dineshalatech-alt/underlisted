"""
Market context — FREE FHFA House Price Index (5-digit ZIP, annual).

Shows each ZIP's recent home-price appreciation ("prices up X% last year"), so a
buyer sees the local price trend. Free download, no key, not billable. The 39 MB
file is parsed ONCE into a small local lookup (data/fhfa_zip5.json); the app reads
that file with no network on page load. The worker refreshes it ~once a year.

Source: https://www.fhfa.gov/data/hpi/datasets  (Five-Digit ZIP, developmental)
"""

from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from typing import Optional

import requests

from config.settings import DATA_DIR
from src.cache import db

FHFA_URL = "https://www.fhfa.gov/hpi/download/annual/hpi_at_zip5.xlsx"
DATA_FILE = DATA_DIR / "fhfa_zip5.json"
_CACHE: Optional[dict] = None


def refresh() -> int:
    """Download + parse the FHFA ZIP5 file into a compact {zip: {year, change}} map."""
    import openpyxl

    resp = requests.get(FHFA_URL, timeout=180)
    resp.raise_for_status()
    wb = openpyxl.load_workbook(io.BytesIO(resp.content), read_only=True, data_only=True)
    ws = wb.active

    latest: dict = {}
    started = False
    for row in ws.iter_rows(values_only=True):
        if not started:
            if row and row[0] == "Five-Digit ZIP Code":
                started = True
            continue
        z, year, change = row[0], row[1], row[2]
        if not z or year is None:
            continue
        z = str(z).zfill(5)
        cur = latest.get(z)
        if cur is None or int(year) > cur["year"]:
            latest[z] = {"year": int(year),
                         "change": (round(float(change), 1) if change is not None else None)}

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(latest))
    db.set_meta("fhfa:refreshed", db.now_iso())
    global _CACHE
    _CACHE = latest
    return len(latest)


def _load() -> dict:
    global _CACHE
    if _CACHE is None:
        _CACHE = json.loads(DATA_FILE.read_text()) if DATA_FILE.exists() else {}
    return _CACHE


def price_trend(zip_code) -> Optional[dict]:
    """Latest annual home-price change for a ZIP: {year, change} or None. No network."""
    if not zip_code:
        return None
    return _load().get(str(zip_code).zfill(5))


def ensure_fresh(max_age_days: int = 300) -> int:
    """Refresh only if the file is missing or older than max_age_days. Returns count."""
    last = db.get_meta("fhfa:refreshed")
    if DATA_FILE.exists() and last:
        try:
            if (datetime.now(timezone.utc) - datetime.fromisoformat(last)).days < max_age_days:
                return 0
        except ValueError:
            pass
    return refresh()

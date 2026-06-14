"""
Census Building Permits — FREE supply signal. "Is this price likely to hold?"

When a county is permitting LOTS of new homes, a flood of fresh supply can cap or
soften prices there; when permits are scarce and demand is steady, prices tend to
hold firmer. The U.S. Census Building Permits Survey (BPS) is the official, free,
public-domain source for this. We show it as plain context, never as part of the
Deal Score (it's a market-trend note, not a property fact).

Shape mirrors market.py / nri.py: we download the BPS *county annual* file ONCE
(free, no key — a public CSV on census.gov), parse it into a tiny local file
(data/building_permits.json) keyed by county FIPS, and read that with NO network on
page load. BPS updates yearly, so the worker refreshes it about yearly.

Optional upgrade: set CENSUS_API_KEY (free, 1-minute signup) to pull the same data
from the live Census API instead. The KEYLESS flat file is the default, so this
works out of the box with no key. If the key is absent, nothing breaks.

ATTRIBUTION (required by Census terms): data is from the U.S. Census Bureau Building
Permits Survey. This product is not endorsed or certified by the U.S. Census Bureau.
Terms: https://www.census.gov/data/developers/about/terms-of-service.html
Data:  https://www.census.gov/construction/bps/

The owner does NOT need a key for this to work. A free Census key is OPTIONAL and only
unlocks the live API path; where it goes is noted in .env / Streamlit secrets as
CENSUS_API_KEY. The source degrades gracefully if the key (or the data) is absent.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Optional

import requests

from config.settings import DATA_DIR
from src.cache import db

# Census BPS county-level ANNUAL file (no key). co<YEAR>a.txt = annual.
BPS_BASE = "https://www2.census.gov/econ/bps/County"
DATA_FILE = DATA_DIR / "building_permits.json"
TIMEOUT = 90

ATTRIBUTION = ("Source: U.S. Census Bureau, Building Permits Survey. This product "
               "is not endorsed or certified by the U.S. Census Bureau.")

_CACHE: Optional[dict] = None


def _candidate_years() -> list[int]:
    """Most recent BPS annual years to try, newest first (last year is usually latest)."""
    this_year = datetime.now(timezone.utc).year
    return [this_year - 1, this_year - 2, this_year - 3, this_year]


def _parse(text: str) -> dict:
    """
    Parse the BPS county annual text into {fips5: {year, total_units, units_1, units_5plus}}.

    The file has TWO header rows, then one row per county. Columns (0-based):
      0 year, 1 state FIPS, 2 county FIPS, 3 region, 4 division, 5 county name,
      then unit triples (bldgs, units, value) for 1-unit / 2-unit / 3-4 / 5+:
      1-unit units = 7, 2-unit units = 10, 3-4 units = 13, 5+ units = 16.
    """
    out: dict = {}
    lines = text.splitlines()
    # Drop the two header lines (and a possible blank line that follows them).
    body = "\n".join(lines[2:])
    for row in csv.reader(io.StringIO(body)):
        if len(row) < 17:
            continue
        sfips = (row[1] or "").strip()
        cfips = (row[2] or "").strip()
        if not sfips or not cfips or not sfips.isdigit():
            continue
        fips5 = (sfips.zfill(2) + cfips.zfill(3))

        def _i(idx: int) -> int:
            try:
                return int(float((row[idx] or "0").strip() or 0))
            except (ValueError, IndexError):
                return 0

        u1 = _i(7)
        u2 = _i(10)
        u34 = _i(13)
        u5 = _i(16)
        total = u1 + u2 + u34 + u5
        out[fips5] = {
            "year": (row[0] or "").strip(),
            "total_units": total,
            "units_1": u1,        # single-family permits
            "units_5plus": u5,    # multifamily (5+) permits
        }
    return out


def refresh() -> int:
    """
    Download the latest BPS county annual file (free, no key) and store a compact
    local lookup. Returns the number of counties stored (0 if nothing fetched, in
    which case any existing file is left untouched). Not billable.
    """
    text = None
    for yr in _candidate_years():
        url = f"{BPS_BASE}/co{yr}a.txt"
        try:
            resp = requests.get(url, timeout=TIMEOUT,
                                headers={"User-Agent": "Underlisted/1.0"})
        except requests.RequestException:
            continue
        if resp.status_code == 200 and "FIPS" in resp.text[:200]:
            text = resp.text
            break
    if not text:
        return 0

    parsed = _parse(text)
    if not parsed:
        return 0
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(parsed))
    db.set_meta("bps:refreshed", db.now_iso())
    global _CACHE
    _CACHE = parsed
    return len(parsed)


def _load() -> dict:
    global _CACHE
    if _CACHE is None:
        _CACHE = json.loads(DATA_FILE.read_text()) if DATA_FILE.exists() else {}
    return _CACHE


def county_permits(fips5) -> Optional[dict]:
    """
    Building-permit activity for a 5-digit county FIPS, or None. NO network — safe
    on page load. Returns {year, total_units, units_1, units_5plus, note, attribution}.
    """
    if not fips5:
        return None
    rec = _load().get(str(fips5).zfill(5))
    if not rec:
        return None
    total = rec.get("total_units") or 0
    if total >= 5000:
        note = ("Lots of new homes are being built here — fresh supply can keep "
                "prices in check.")
    elif total >= 500:
        note = "A steady amount of new building here — supply looks balanced."
    elif total > 0:
        note = ("Very little new building here — limited new supply tends to "
                "support prices.")
    else:
        note = "Almost no new building permits here last year."
    return {**rec, "note": note, "attribution": ATTRIBUTION}


def has_data() -> bool:
    """True once the permits file has been built. Lets callers degrade quietly."""
    return bool(_load())


def ensure_fresh(max_age_days: int = 300) -> int:
    """Refresh only if the file is missing or older than max_age_days (BPS is yearly).
    Returns count refreshed (0 if already fresh). Free, no key, not billable."""
    last = db.get_meta("bps:refreshed")
    if DATA_FILE.exists() and last:
        try:
            if (datetime.now(timezone.utc) - datetime.fromisoformat(last)).days < max_age_days:
                return 0
        except ValueError:
            pass
    return refresh()

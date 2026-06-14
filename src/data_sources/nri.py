"""
OpenFEMA National Risk Index (NRI) — FREE, no key. Hardens our insurance-risk moat.

Our per-home risk (src/data_sources/risk.py) asks FEMA's *census-tract* layer for a
single point. That's precise, but it can come back empty (rural gaps, an off-coast
coordinate, or the tract service being briefly down) — and an empty risk reading
weakens the whole point of warning a buyer about fire/flood insurance.

This source is the safety net. It pulls the official FEMA NRI *county* table ONCE
into a tiny local file (data/nri_counties.json), exactly like market.py does with the
FHFA file. The app then reads that file with NO network on page load to get a
county-level risk rating (wildfire / flood / earthquake / overall) for ANY U.S.
address — so the insurance-risk warning is never blank.

This is the SAME official FEMA NRI dataset risk.py already uses, just the published
county feature layer (the direct NRI feed) instead of point-by-point tract queries.
Public-domain U.S. government data, no key, not billable.

FAIR HOUSING: risk ratings are natural-hazard / insurance signals only. They are
info-only and are NEVER used as a demographic or "neighborhood-quality" score.

Source: FEMA National Risk Index  ·  https://hazards.fema.gov/nri/
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

import requests

from config.settings import DATA_DIR
from src.cache import db

# FEMA's published NRI Counties feature layer (same ArcGIS org as the tract layer
# in risk.py). Public, no key. We page through every county once.
NRI_COUNTIES_URL = ("https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/"
                    "services/National_Risk_Index_Counties/FeatureServer/0/query")
DATA_FILE = DATA_DIR / "nri_counties.json"
TIMEOUT = 60
PAGE = 1000  # ArcGIS default max records per request

# The few NRI fields we keep (rating strings, not raw scores). STCOFIPS is the
# 5-digit state+county FIPS we key the lookup on. CFLD = coastal flood,
# IFLD = inland flood, WFIR = wildfire, ERQK = earthquake, RISK_RATNG = overall.
_FIELDS = ["STCOFIPS", "STATEABBRV", "COUNTY", "RISK_RATNG",
           "WFIR_RISKR", "CFLD_RISKR", "IFLD_RISKR", "ERQK_RISKR"]

_CACHE: Optional[dict] = None


def _fetch_page(offset: int) -> list[dict]:
    """One page of county records from FEMA (free, not billable)."""
    params = {
        "where": "1=1",
        "outFields": ",".join(_FIELDS),
        "returnGeometry": "false",
        "orderByFields": "STCOFIPS",
        "resultOffset": offset,
        "resultRecordCount": PAGE,
        "f": "json",
    }
    resp = requests.get(NRI_COUNTIES_URL, params=params, timeout=TIMEOUT,
                        headers={"User-Agent": "Underlisted/1.0"})
    resp.raise_for_status()
    return resp.json().get("features", []) or []


def refresh() -> int:
    """
    Download the full FEMA NRI county table once into a compact local file:
        { "<STCOFIPS>": {wildfire, flood, earthquake, overall, county, state} }
    Returns the number of counties stored. Free, no key, not billable.
    """
    out: dict = {}
    offset = 0
    while True:
        feats = _fetch_page(offset)
        if not feats:
            break
        for f in feats:
            a = f.get("attributes", {}) or {}
            fips = a.get("STCOFIPS")
            if not fips:
                continue
            # NRI marks irrelevant hazards "Not Applicable" — treat that as no
            # signal (None) so the app shows "Unknown", never a false "Low".
            def _clean(v):
                v = (v or "").strip() if isinstance(v, str) else v
                return None if v in (None, "", "Not Applicable", "Insufficient Data",
                                     "No Rating", "No Expected Annual Losses") else v
            # Flood = the worse of coastal and inland for this county.
            flood = _worse(_clean(a.get("CFLD_RISKR")), _clean(a.get("IFLD_RISKR")))
            out[str(fips).zfill(5)] = {
                "wildfire": _clean(a.get("WFIR_RISKR")),
                "flood": flood,
                "earthquake": _clean(a.get("ERQK_RISKR")),
                "overall": _clean(a.get("RISK_RATNG")),
                "county": (a.get("COUNTY") or "").strip() or None,
                "state": a.get("STATEABBRV"),
            }
        if len(feats) < PAGE:
            break
        offset += PAGE

    if not out:
        return 0  # API gave us nothing — keep any existing file untouched.

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(out))
    db.set_meta("nri:refreshed", db.now_iso())
    global _CACHE
    _CACHE = out
    return len(out)


# Order FEMA uses for its qualitative ratings, low -> high.
_RANK = {
    "very low": 0, "relatively low": 1, "relatively moderate": 2,
    "relatively high": 3, "very high": 4,
}


def _worse(a: Optional[str], b: Optional[str]) -> Optional[str]:
    """Return whichever rating is higher-risk (or whichever isn't None)."""
    if a is None:
        return b
    if b is None:
        return a
    return a if _RANK.get(a.lower(), -1) >= _RANK.get(b.lower(), -1) else b


def _load() -> dict:
    global _CACHE
    if _CACHE is None:
        _CACHE = json.loads(DATA_FILE.read_text()) if DATA_FILE.exists() else {}
    return _CACHE


def county_risk(fips5) -> Optional[dict]:
    """
    County-level NRI ratings for a 5-digit FIPS, or None. NO network — safe on
    page load. Returns {wildfire, flood, earthquake, overall, county, state},
    each a FEMA rating string (e.g. "Relatively High") or None when not rated.
    """
    if not fips5:
        return None
    return _load().get(str(fips5).zfill(5))


def has_data() -> bool:
    """True once the county file has been built. Lets the app/worker degrade quietly."""
    return bool(_load())


def ensure_fresh(max_age_days: int = 180) -> int:
    """Refresh only if the file is missing or older than max_age_days. Returns count
    (0 if already fresh). NRI updates a couple of times a year, so this is rare."""
    last = db.get_meta("nri:refreshed")
    if DATA_FILE.exists() and last:
        try:
            if (datetime.now(timezone.utc) - datetime.fromisoformat(last)).days < max_age_days:
                return 0
        except ValueError:
            pass
    return refresh()

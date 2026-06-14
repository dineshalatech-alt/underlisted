"""
HUD Fair Market Rents (FMR) — FREE area rent benchmark (needs a free HUD token).

HUD publishes the "fair market rent" (about the 40th-percentile gross rent) for
every U.S. metro and county, by bedroom count. It's an AREA benchmark, not a
per-home estimate — so we use it as a FREE fallback rent when RentCast has none.
That keeps the rent-yield part of the Deal Score working at zero extra cost.

Shape mirrors market.py: we fetch each state's whole FMR table ONCE (free), store
it under data/hud_fmr/<STATE>.json, and read that file with NO network on page
load. FMR updates about yearly, so the worker refreshes it ~yearly.

Set HUD_FMR_TOKEN (free, 5-min signup) to enable. Dormant if the token is missing.
Docs: https://www.huduser.gov/portal/dataset/fmr-api.html
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

import requests

from config.settings import DATA_DIR, settings
from src.cache import db

BASE_URL = "https://www.huduser.gov/hudapi/public/fmr"
FMR_DIR = DATA_DIR / "hud_fmr"

# beds -> the key HUD uses in its response
_BED_KEYS = {0: "Efficiency", 1: "One-Bedroom", 2: "Two-Bedroom",
             3: "Three-Bedroom", 4: "Four-Bedroom"}
_STATE_CACHE: dict[str, dict] = {}


def _state_file(state: str):
    return FMR_DIR / f"{state.upper()}.json"


def refresh_state(state: str) -> Optional[dict]:
    """Fetch one state's full FMR table (free) and cache it. None if no token."""
    if not settings.has_hud_fmr:
        return None
    headers = {"Authorization": f"Bearer {settings.hud_fmr_token}"}
    resp = requests.get(f"{BASE_URL}/statedata/{state.upper()}",
                        headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json().get("data", {})
    payload = {
        "year": data.get("year"),
        "metros": data.get("metroareas", []),
        "counties": data.get("counties", []),
    }
    FMR_DIR.mkdir(parents=True, exist_ok=True)
    _state_file(state).write_text(json.dumps(payload))
    db.set_meta(f"hud_fmr:{state.upper()}:refreshed", db.now_iso())
    _STATE_CACHE[state.upper()] = payload
    return payload


def ensure_state_fresh(state: str, max_age_days: int = 300) -> Optional[dict]:
    """Refresh a state's FMR table only if missing or older than max_age_days."""
    if not settings.has_hud_fmr:
        return None
    last = db.get_meta(f"hud_fmr:{state.upper()}:refreshed")
    if _state_file(state).exists() and last:
        try:
            if (datetime.now(timezone.utc) - datetime.fromisoformat(last)).days < max_age_days:
                return None
        except ValueError:
            pass
    return refresh_state(state)


def _load_state(state: str) -> dict:
    s = state.upper()
    if s not in _STATE_CACHE:
        f = _state_file(s)
        _STATE_CACHE[s] = json.loads(f.read_text()) if f.exists() else {}
    return _STATE_CACHE[s]


def _bed_key(beds: Optional[int]) -> str:
    if beds is None:
        return "Two-Bedroom"  # a sensible standard when bedroom count is unknown
    return _BED_KEYS.get(max(0, min(int(beds), 4)), "Two-Bedroom")


def area_rent(listing) -> Optional[dict]:
    """
    Free area Fair Market Rent for a listing, matched by city -> metro name.
    Reads only the local cache (NO network — safe on page load). Returns
    {rent, area, bedrooms, year, source} or None if we can't match it.
    """
    state = getattr(listing, "state", None)
    city = (getattr(listing, "city", None) or "").strip().lower()
    if not state or not city:
        return None
    table = _load_state(state)
    metros = table.get("metros", [])
    if not metros:
        return None

    bed_key = _bed_key(getattr(listing, "beds", None))
    # Match the listing's city to a metro whose name contains it (e.g.
    # "Sacramento" -> "Sacramento--Roseville--Arden-Arcade, CA HUD Metro FMR Area").
    match = next((m for m in metros if city in (m.get("metro_name") or "").lower()), None)
    if not match:
        return None
    rent = match.get(bed_key)
    if rent in (None, "", 0):
        return None
    return {
        "rent": float(rent),
        "area": match.get("metro_name"),
        "bedrooms": bed_key,
        "year": table.get("year"),
        "source": "HUD Fair Market Rent (area)",
    }

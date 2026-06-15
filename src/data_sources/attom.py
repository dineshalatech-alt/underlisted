"""
ATTOM Data — nationwide property data + sold-price comps.

Why we added this: RentCast gives us list price + an AVM, but ATTOM adds two
things that directly sharpen our Deal Score and unlock real "comps":
  * an independent **AVM** (estimated value + a low/high range), and
  * **sale history** (what the home actually sold for, and when) plus nearby
    **sold comparables**.

This module is OPTIONAL and ADDITIVE. If `ATTOM_API_KEY` is missing the app
behaves exactly as before (RentCast only). It mirrors `rentcast.py`'s shape:
fetch raw -> map to our model -> cache by address (shared, weekly TTL) so a
repeat view of the same home is FREE and never re-bills ATTOM.

Cost control (same rules as RentCast):
  * Never called on page load or from listing cards — only when a user opens a
    specific property, or from the background worker.
  * Every billable call is recorded via db.record_usage so Admin/Usage can see it.
  * Results are cached per address for all users; a repeat within the TTL is a
    free cache hit.

Docs:  https://api.developer.attomdata.com/docs
Base:  https://api.gateway.attomdata.com/propertyapi/v1.0.0/
Auth:  header  apikey: <your key>   (also send  Accept: application/json)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import requests

from config.settings import settings
from src.cache import db
from src.models import Listing, ValueEstimate

BASE_URL = "https://api.gateway.attomdata.com/propertyapi/v1.0.0"
AVM_PATH = "/avm/detail"
SALEHISTORY_PATH = "/saleshistory/detail"
PROPERTY_DETAIL_PATH = "/property/detail"
REQUEST_TIMEOUT = 30  # seconds


class AttomError(RuntimeError):
    """Raised when ATTOM returns an error we should surface."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _headers() -> dict:
    if not settings.has_attom:
        raise AttomError(
            "ATTOM_API_KEY is not set. Add it to your .env file "
            "(get a free trial key at https://api.developer.attomdata.com/signup)."
        )
    return {"apikey": settings.attom_api_key, "Accept": "application/json"}


# --- Low-level API call ----------------------------------------------------

def _get(path: str, params: dict, usage_kind: str) -> dict:
    """One billable ATTOM call. Returns the parsed JSON dict.

    Records usage regardless of outcome (the request was made) and raises
    AttomError with a clear message on any non-200 response.
    """
    url = BASE_URL + path
    try:
        resp = requests.get(
            url, headers=_headers(), params=params, timeout=REQUEST_TIMEOUT
        )
    except requests.RequestException as exc:
        raise AttomError(f"Could not reach ATTOM: {exc}") from exc

    db.record_usage(usage_kind, _now_iso())

    if resp.status_code == 401:
        raise AttomError("ATTOM rejected the key (401). Check ATTOM_API_KEY.")
    if resp.status_code == 403:
        raise AttomError(
            "ATTOM denied this endpoint (403). Your plan/trial may not include it."
        )
    if resp.status_code == 429:
        raise AttomError("ATTOM rate limit hit (429). Wait a bit and retry.")

    # Parse the body BEFORE judging status — ATTOM quirkily returns HTTP 400 with
    # msg "SuccessWithoutResult" when the address simply has no data. That's benign
    # (auth + endpoint were fine), so we treat it as an empty result, not an error.
    try:
        data = resp.json()
    except ValueError:
        data = None

    status = (data or {}).get("status") or {}
    msg = str(status.get("msg") or "")
    no_data = "SuccessWithoutResult" in msg or "no record" in msg.lower()

    if no_data:
        return data or {}
    if resp.status_code >= 400:
        raise AttomError(f"ATTOM error {resp.status_code}: {resp.text[:200]}")
    if data is None:
        raise AttomError(f"ATTOM returned non-JSON: {resp.text[:200]}")
    return data


# --- Address helpers -------------------------------------------------------

def _address_pair(listing: Listing) -> Optional[tuple[str, str]]:
    """Build ATTOM's (address1, address2) pair.

    address1 = the street line (e.g. "4529 Winona Court")
    address2 = "City, ST" (e.g. "Denver, CO")
    Returns None if we don't have enough to identify the home.
    """
    if listing.city and listing.state:
        address2 = f"{listing.city}, {listing.state}"
    else:
        address2 = ""
    # Street line: the part of the full address before the first comma.
    street = ""
    if listing.address:
        street = listing.address.split(",")[0].strip()
    if not street or not address2:
        return None
    return street, address2


def _cache_key(listing: Listing, kind: str) -> Optional[str]:
    pair = _address_pair(listing)
    if not pair:
        return None
    street, area = pair
    norm = " ".join(f"{street} {area}".lower().split())
    return f"attom:{kind}:{norm}"


def _num(value) -> Optional[float]:
    """Coerce ATTOM's numeric-ish fields to float, tolerating None/blank/str."""
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if f > 0 else None


# --- Connectivity / auth check (one cheap call) ----------------------------

def ping(listing: Optional[Listing] = None) -> dict:
    """Make ONE minimal call to confirm the key works and the AVM endpoint is in
    the plan. Returns {ok, status_code|code, msg, value?}. Never raises — it
    reports the outcome so the caller can decide what to do.

    Pass a real Listing for a meaningful test; otherwise a known public address
    is used purely to validate auth + endpoint access.
    """
    if listing is not None:
        pair = _address_pair(listing)
    else:
        # ATTOM's own documented sample address — known to return AVM data.
        pair = ("4529 Winona Court", "Denver, CO")
    if not pair:
        return {"ok": False, "msg": "Could not build an address to test."}
    address1, address2 = pair
    try:
        data = _get(
            AVM_PATH,
            {"address1": address1, "address2": address2},
            "attom_value",
        )
    except AttomError as exc:
        return {"ok": False, "msg": str(exc)}
    prop = (data.get("property") or [{}])[0]
    amount = ((prop.get("avm") or {}).get("amount") or {})
    return {
        "ok": True,
        "code": (data.get("status") or {}).get("code"),
        "msg": (data.get("status") or {}).get("msg"),
        "value": _num(amount.get("value")),
    }


# --- Mapping: ATTOM AVM -> our ValueEstimate -------------------------------

def _map_avm(data: dict) -> ValueEstimate:
    prop = (data.get("property") or [{}])[0]
    amount = ((prop.get("avm") or {}).get("amount") or {})
    return ValueEstimate(
        avm=_num(amount.get("value")),
        value_low=_num(amount.get("low")),
        value_high=_num(amount.get("high")),
        comps=[],  # comps come from get_sale_history / a dedicated comps endpoint
    )


def get_value_estimate(
    listing: Listing,
    *,
    count_against_user: bool = True,
    cache_only: bool = False,
) -> ValueEstimate:
    """ATTOM AVM (estimated value + low/high). Shared cache, weekly TTL.

    `cache_only=True` serves a cached estimate but won't make a NEW (billable)
    call — used to honor the per-user monthly cap.
    """
    key = _cache_key(listing, "value")
    if not key:
        return ValueEstimate()
    ttl = settings.ttl_seconds("value_estimate_days", 7 * 86400)

    cached = db.cache_get(key, max_age_seconds=ttl)
    if cached is not None:
        db.note_cache_hit("attom_value")
        return _map_avm(cached)
    if cache_only:
        return ValueEstimate()  # capped: don't bill

    pair = _address_pair(listing)
    if not pair:
        return ValueEstimate()
    address1, address2 = pair
    db.note_cache_miss("attom_value")
    data = _get(AVM_PATH, {"address1": address1, "address2": address2}, "attom_value")
    if count_against_user:
        db.record_user_lookup(settings.current_user_id, "attom_value")
    db.cache_put(key, "value", data)
    return _map_avm(data)


# --- Sale history (what it actually sold for) ------------------------------

def get_last_sale(
    listing: Listing,
    *,
    count_against_user: bool = True,
    cache_only: bool = False,
) -> Optional[dict]:
    """Most recent recorded sale for the home: {amount, date}. Shared cache.

    Returns None if ATTOM has no sale on record (common for never-sold or new
    construction) — that's not an error.
    """
    key = _cache_key(listing, "salehistory")
    if not key:
        return None
    ttl = settings.ttl_seconds("value_estimate_days", 7 * 86400)

    cached = db.cache_get(key, max_age_seconds=ttl)
    if cached is not None:
        db.note_cache_hit("attom_salehistory")
        return _extract_last_sale(cached)
    if cache_only:
        return None

    pair = _address_pair(listing)
    if not pair:
        return None
    address1, address2 = pair
    db.note_cache_miss("attom_salehistory")
    data = _get(
        SALEHISTORY_PATH, {"address1": address1, "address2": address2},
        "attom_salehistory",
    )
    if count_against_user:
        db.record_user_lookup(settings.current_user_id, "attom_salehistory")
    db.cache_put(key, "salehistory", data)
    return _extract_last_sale(data)


def _extract_last_sale(data: dict) -> Optional[dict]:
    prop = (data.get("property") or [{}])[0]
    history = prop.get("salehistory") or []
    best: Optional[dict] = None
    for evt in history:
        amt = _num(((evt.get("amount") or {}).get("saleamt")))
        date = ((evt.get("amount") or {}).get("salerecdate")) or evt.get("saleTransDate")
        if amt is None:
            continue
        if best is None or (date and date > (best.get("date") or "")):
            best = {"amount": amt, "date": date}
    return best

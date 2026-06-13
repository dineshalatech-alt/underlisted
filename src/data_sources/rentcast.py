"""
RentCast — for-sale listings data source.

Responsibilities:
  * Fetch active for-sale listings from RentCast for our configured cities/zips.
  * Save each listing into the SQLite cache (so the app reads from cache and
    never re-bills the API just to *view* a property again).
  * Detect price changes across runs (flag price drops).
  * Count every billable call so we can watch costs.

Docs: https://developers.rentcast.io/reference/sale-listings
Endpoint:  GET https://api.rentcast.io/v1/listings/sale
Auth:      header  X-Api-Key: <your key>
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Callable, Iterable, Optional

import requests

from config.settings import settings
from src.cache import db
from src.models import Listing, RentEstimate, ValueEstimate

API_URL = "https://api.rentcast.io/v1/listings/sale"
VALUE_URL = "https://api.rentcast.io/v1/avm/value"
RENT_URL = "https://api.rentcast.io/v1/avm/rent/long-term"
REQUEST_TIMEOUT = 30  # seconds
MAX_LIMIT = 500       # RentCast returns up to 500 per request


class RentCastError(RuntimeError):
    """Raised when RentCast returns an error we should show the user."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _headers() -> dict:
    if not settings.has_rentcast:
        raise RentCastError(
            "RENTCAST_API_KEY is not set. Add it to your .env file (README Step 4)."
        )
    return {"X-Api-Key": settings.rentcast_api_key, "Accept": "application/json"}


# --- Low-level API call ----------------------------------------------------

def fetch_listings_raw(
    *,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None,
    status: str = "Active",
    limit: int = MAX_LIMIT,
    offset: int = 0,
    days_old: Optional[int] = None,
) -> list[dict]:
    """
    One billable RentCast call. Returns the raw list of listing dicts.

    Pass either a city (+state) or a zipCode. This function records one unit of
    API usage and raises RentCastError on any non-200 response.
    """
    params: dict = {
        "status": status,
        "limit": min(int(limit), MAX_LIMIT),
        "offset": int(offset),
    }
    if zip_code:
        params["zipCode"] = zip_code
    if city:
        params["city"] = city
    if state:
        params["state"] = state
    if days_old:
        params["daysOld"] = int(days_old)

    try:
        resp = requests.get(
            API_URL, headers=_headers(), params=params, timeout=REQUEST_TIMEOUT
        )
    except requests.RequestException as exc:
        raise RentCastError(f"Could not reach RentCast: {exc}") from exc

    # Record the billable call regardless of outcome — the request was made.
    db.record_usage("rentcast", _now_iso())

    if resp.status_code == 401:
        raise RentCastError("RentCast rejected the key (401). Check RENTCAST_API_KEY.")
    if resp.status_code == 429:
        raise RentCastError("RentCast rate limit hit (429). Wait a bit and retry.")
    if resp.status_code >= 400:
        raise RentCastError(
            f"RentCast error {resp.status_code}: {resp.text[:200]}"
        )

    data = resp.json()
    # RentCast returns a JSON array; be tolerant if it ever wraps in an object.
    if isinstance(data, dict):
        data = data.get("listings") or data.get("data") or []
    return data or []


# --- Mapping raw JSON -> our Listing model ---------------------------------

def raw_to_listing(raw: dict) -> Listing:
    """Convert one RentCast JSON record into our tidy Listing object."""
    return Listing(
        id=str(raw.get("id") or raw.get("formattedAddress")),
        address=raw.get("formattedAddress") or raw.get("addressLine1") or "",
        city=raw.get("city") or "",
        state=raw.get("state") or "",
        zip_code=raw.get("zipCode") or "",
        latitude=raw.get("latitude"),
        longitude=raw.get("longitude"),
        list_price=raw.get("price"),
        beds=raw.get("bedrooms"),
        baths=raw.get("bathrooms"),
        sqft=raw.get("squareFootage"),
        year_built=raw.get("yearBuilt"),
        property_type=raw.get("propertyType"),
        status=raw.get("status"),
        days_on_market=raw.get("daysOnMarket"),
    )


# --- Sync: fetch for all configured targets and cache the results ----------

def _iter_targets() -> Iterable[tuple[str, str, Optional[str]]]:
    """
    Yield (city, state, zip) for each search we should run.

    If a city lists zips, we search by zip (more precise). If it has no zips,
    we search the whole city.
    """
    state = settings.cities.get("state", "CA")
    for target in settings.cities.get("targets", []):
        city = target.get("name")
        zips = target.get("zips") or []
        if zips:
            for z in zips:
                yield city, state, z
        else:
            yield city, state, None


def _area_key(city: str, zip_code: Optional[str]) -> str:
    return f"lastsync:{city}:{zip_code or 'all'}"


def _incremental_days_old(area_key: str, lookback_days: int) -> Optional[int]:
    """
    For an incremental refresh, only ask RentCast for listings as old as the
    time since we last synced THIS area (plus a safety overlap). If we've never
    synced it, return None so we do a full pull the first time.
    """
    last = db.get_meta(area_key)
    if not last:
        return None
    try:
        elapsed = datetime.now(timezone.utc) - datetime.fromisoformat(last)
    except ValueError:
        return None
    days = math.ceil(elapsed.total_seconds() / 86400) + lookback_days
    return max(1, min(days, 90))  # RentCast daysOld is at least 1


def sync_listings(
    *,
    status: str = "Active",
    limit_per_area: int = MAX_LIMIT,
    days_old: Optional[int] = None,
    incremental: bool = False,
    progress: Optional[Callable[[str], None]] = None,
) -> dict:
    """
    Fetch listings for every configured city/zip and cache them in SQLite.

    Cost control:
      * `incremental=True` only pulls listings new since this area's last sync
        (using each area's own last-sync time), so day-to-day refreshes are cheap.
        Do a FULL refresh (incremental=False) about weekly to catch price changes
        on older listings — `daysOld` can't see those.
      * `days_old` forces a fixed window and overrides the incremental calc.

    Returns: {new, updated, price_drops[], total_seen, errors[], synced_at}
    """
    when = _now_iso()
    lookback = int(settings.cache.get("sync", {}).get("incremental_lookback_days", 7))
    new_count = 0
    updated_count = 0
    price_drops: list[dict] = []
    total_seen = 0
    errors: list[str] = []

    for city, state, zip_code in _iter_targets():
        where = f"{city} {zip_code}" if zip_code else city
        area_key = _area_key(city, zip_code)

        # Decide how far back to look for THIS area.
        area_days_old = days_old
        if area_days_old is None and incremental:
            area_days_old = _incremental_days_old(area_key, lookback)

        if progress:
            scope = f"last {area_days_old}d" if area_days_old else "full"
            progress(f"Fetching {where} ({scope})…")
        try:
            raw_listings = fetch_listings_raw(
                city=city,
                state=state,
                zip_code=zip_code,
                status=status,
                limit=limit_per_area,
                days_old=area_days_old,
            )
        except RentCastError as exc:
            errors.append(f"{where}: {exc}")
            continue

        db.set_meta(area_key, when)  # remember we synced this area just now

        for raw in raw_listings:
            listing = raw_to_listing(raw)
            if not listing.id:
                continue
            total_seen += 1
            result = db.upsert_listing(
                listing_id=listing.id,
                address=listing.address,
                city=listing.city,
                zip_code=listing.zip_code,
                list_price=listing.list_price,
                payload=raw,
                when_iso=when,
            )
            if result["is_new"]:
                new_count += 1
            else:
                updated_count += 1
            if result["price_changed"] and result["previous_price"] is not None:
                old = float(result["previous_price"])
                newp = float(listing.list_price)
                if newp < old:  # only a DROP is interesting
                    price_drops.append(
                        {"address": listing.address, "old": old, "new": newp}
                    )

    db.set_meta("lastsync:global", when)
    return {
        "new": new_count,
        "updated": updated_count,
        "price_drops": price_drops,
        "total_seen": total_seen,
        "errors": errors,
        "synced_at": when,
    }


def last_sync_time() -> Optional[str]:
    """ISO timestamp of the most recent sync, or None if never synced."""
    return db.get_meta("lastsync:global")


def sync_area(*, city: Optional[str] = None, state: Optional[str] = None,
              zip_code: Optional[str] = None, status: str = "Active",
              limit: int = MAX_LIMIT) -> dict:
    """
    Fetch ONE arbitrary U.S. area on demand (a city+state or a ZIP) and cache it.

    This powers nationwide "search any city/ZIP": it bills exactly ONE RentCast call,
    caches the results in the shared store (so every later viewer is free), and is
    only ever called when the user explicitly asks to load a new area.

    Returns: {new, updated, total_seen, errors[], synced_at}
    """
    when = _now_iso()
    new_count = updated_count = total_seen = 0
    try:
        raw_listings = fetch_listings_raw(city=city, state=state, zip_code=zip_code,
                                          status=status, limit=limit)
    except RentCastError as exc:
        return {"new": 0, "updated": 0, "total_seen": 0,
                "errors": [str(exc)], "synced_at": when}

    for raw in raw_listings:
        listing = raw_to_listing(raw)
        if not listing.id:
            continue
        total_seen += 1
        result = db.upsert_listing(
            listing_id=listing.id, address=listing.address, city=listing.city,
            zip_code=listing.zip_code, list_price=listing.list_price,
            payload=raw, when_iso=when,
        )
        if result["is_new"]:
            new_count += 1
        else:
            updated_count += 1

    area_key = zip_code or (f"{city},{state}" if city else "area")
    db.set_meta(f"lastsync:area:{area_key}", when)
    return {"new": new_count, "updated": updated_count, "total_seen": total_seen,
            "errors": [], "synced_at": when}


# --- Read cached listings for display (NO API call) ------------------------

def load_cached_listings(
    city_filter: Optional[list[str]] = None,
    limit: int = 500,
) -> list[Listing]:
    """
    Read listings from the SQLite cache for the app to display. This never calls
    RentCast, so viewing/refiltering listings costs nothing.
    """
    import json

    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, payload, previous_price FROM listings "
            "WHERE id NOT LIKE 'FC:%' "       # foreclosures load via foreclosure.py
            "ORDER BY last_seen DESC LIMIT ?",
            (limit,),
        ).fetchall()

    listings: list[Listing] = []
    for row in rows:
        try:
            raw = json.loads(row["payload"])
        except (TypeError, ValueError):
            continue
        listing = raw_to_listing(raw)
        if row["previous_price"] is not None:
            listing.previous_price = float(row["previous_price"])
        if city_filter and listing.city not in city_filter:
            continue
        listings.append(listing)
    return listings


def cached_listing_count() -> int:
    with db.connect() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM listings").fetchone()["n"]


# ---------------------------------------------------------------------------
# Value (AVM) + Rent estimates — SHARED, address-keyed, weekly-cached.
#
# These are the cost-controlled fetchers the detail page will call in Phase 3.
# They are NOT called from the listing cards or on page load — only when a user
# opens a specific property — so we never pay for an estimate nobody looks at.
# Each result is cached by address for all users; a repeat view within the TTL
# is free and counted as a cache hit.
# ---------------------------------------------------------------------------

def _address_key(listing: Listing) -> Optional[str]:
    if listing.address:
        return " ".join(listing.address.lower().split())
    if listing.latitude is not None and listing.longitude is not None:
        return f"{round(float(listing.latitude), 5)},{round(float(listing.longitude), 5)}"
    return None


def _avm_params(listing: Listing) -> dict:
    """Extra hints improve AVM accuracy and reduce wasted calls."""
    params: dict = {}
    if listing.address:
        params["address"] = listing.address
    if listing.latitude is not None and listing.longitude is not None:
        params["latitude"] = listing.latitude
        params["longitude"] = listing.longitude
    if listing.property_type:
        params["propertyType"] = listing.property_type
    if listing.beds is not None:
        params["bedrooms"] = listing.beds
    if listing.baths is not None:
        params["bathrooms"] = listing.baths
    if listing.sqft is not None:
        params["squareFootage"] = listing.sqft
    return params


def _avm_call(url: str, listing: Listing, usage_kind: str,
              count_against_user: bool = True) -> Optional[dict]:
    try:
        resp = requests.get(
            url, headers=_headers(), params=_avm_params(listing),
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise RentCastError(f"Could not reach RentCast: {exc}") from exc
    db.record_usage(usage_kind, _now_iso())
    if count_against_user:
        db.record_user_lookup(settings.current_user_id, usage_kind)
    if resp.status_code >= 400:
        raise RentCastError(f"RentCast {usage_kind} error {resp.status_code}: "
                            f"{resp.text[:200]}")
    return resp.json()


def get_value_estimate(listing: Listing, *, count_against_user: bool = True,
                       cache_only: bool = False) -> ValueEstimate:
    """
    Estimated current value (AVM) + sale comps. Shared cache, weekly TTL.
    `cache_only=True` serves a cached estimate but won't make a NEW (billable)
    call — used to honor the per-user monthly cap.
    """
    key = _address_key(listing)
    if not key:
        return ValueEstimate()
    cache_key = f"value:{key}"
    ttl = settings.ttl_seconds("value_estimate_days", 7 * 86400)

    cached = db.cache_get(cache_key, max_age_seconds=ttl)
    if cached is not None:
        db.note_cache_hit("rentcast_value")
        raw = cached
    elif cache_only:
        return ValueEstimate()  # capped: don't bill
    else:
        db.note_cache_miss("rentcast_value")
        raw = _avm_call(VALUE_URL, listing, "rentcast_value",
                        count_against_user=count_against_user) or {}
        db.cache_put(cache_key, "value", raw)

    return ValueEstimate(
        avm=raw.get("price"),
        value_low=raw.get("priceRangeLow"),
        value_high=raw.get("priceRangeHigh"),
        comps=raw.get("comparables", []) or [],
    )


def get_rent_estimate(listing: Listing, *, count_against_user: bool = True,
                      cache_only: bool = False) -> RentEstimate:
    """
    Estimated monthly rent + rent comps. Shared cache, weekly TTL.
    `cache_only=True` serves a cached estimate but won't make a NEW (billable)
    call — used to honor the per-user monthly cap.
    """
    key = _address_key(listing)
    if not key:
        return RentEstimate()
    cache_key = f"rent:{key}"
    ttl = settings.ttl_seconds("rent_estimate_days", 7 * 86400)

    cached = db.cache_get(cache_key, max_age_seconds=ttl)
    if cached is not None:
        db.note_cache_hit("rentcast_rent")
        raw = cached
    elif cache_only:
        return RentEstimate()  # capped: don't bill
    else:
        db.note_cache_miss("rentcast_rent")
        raw = _avm_call(RENT_URL, listing, "rentcast_rent",
                        count_against_user=count_against_user) or {}
        db.cache_put(cache_key, "rent", raw)

    return RentEstimate(
        monthly_rent=raw.get("rent"),
        rent_low=raw.get("rentRangeLow"),
        rent_high=raw.get("rentRangeHigh"),
        comps=raw.get("comparables", []) or [],
    )

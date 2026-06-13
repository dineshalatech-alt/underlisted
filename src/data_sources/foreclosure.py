"""
Foreclosure Data Hub — bank-owned / foreclosure (REO) listings data source.

Mirrors rentcast.py so it plugs into the SAME shared cache + worker:
  * Fetch foreclosure / REO records for our configured California zips.
  * Save each into the shared `listings` cache (ids are PREFIXED "FC:" so they're
    kept separate from RentCast for-sale listings in the same table).
  * Count every billable call (kind="foreclosure") so cost stays visible.

Why a separate source: RentCast carries only active for-sale listings — it has NO
foreclosure data. Foreclosure Data Hub is a licensed REST API (flat $49/mo), so we
never scrape Auction.com / Zillow / county sites.

⚠️ DATA SHAPE: these are auction/recorder records, NOT full MLS listings. They carry
address, price (bid amount), county, sale date, owner, and an ESTIMATED VALUE
(Redfin-derived) — but usually NOT beds / baths / sqft / rent. So we surface a
"bank-owned" card with a bid-vs-estimated-value discount, not the full deal card.

⚠️ FIELD NAMES below are best-effort from the API docs. After the $1 trial, run
`.tmp/foreclosure_probe.py` to see the real keys and adjust `_first()` lists if needed.

Docs:     https://www.foreclosuredatahub.com/api-docs
Endpoint: GET https://api.foreclosuredatahub.com/api/v1/properties/search?mode=unified
Auth:     header  x-api-key: fdh_ak_<your key>
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Callable, Optional

import requests

from config.settings import settings
from src.cache import db
from src.models import Listing

API_URL = "https://api.foreclosuredatahub.com/api/v1/properties/search"
REQUEST_TIMEOUT = 30
MAX_PAGE_SIZE = 100
ID_PREFIX = "FC:"   # marks foreclosure rows inside the shared `listings` table


class ForeclosureError(RuntimeError):
    """Raised when Foreclosure Data Hub returns an error we should show."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _headers() -> dict:
    if not settings.has_foreclosure:
        raise ForeclosureError(
            "FORECLOSURE_API_KEY is not set. Sign up for the $1 trial at "
            "foreclosuredatahub.com and add the key to your .env file."
        )
    return {"x-api-key": settings.foreclosure_api_key, "Accept": "application/json"}


def _first(raw: dict, *keys, default=None):
    """Return the first present, non-empty value among several possible key names."""
    for k in keys:
        if k in raw and raw[k] not in (None, ""):
            return raw[k]
    return default


# --- Low-level API call ----------------------------------------------------

def fetch_listings_raw(
    *,
    state: Optional[str] = None,
    county: Optional[str] = None,
    zip_code: Optional[str] = None,
    page_size: int = MAX_PAGE_SIZE,
) -> list[dict]:
    """
    One billable Foreclosure Data Hub call. Returns the raw list of records.

    Uses the unified search (normalized flat list). Requires at least one location
    filter (state / county / zip). Records one unit of usage and raises on errors.
    """
    params: dict = {"mode": "unified", "page_size": min(int(page_size), MAX_PAGE_SIZE)}
    if state:
        params["state"] = state
    if county:
        params["county"] = county
    if zip_code:
        params["zip"] = zip_code

    try:
        resp = requests.get(API_URL, headers=_headers(), params=params,
                            timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        raise ForeclosureError(f"Could not reach Foreclosure Data Hub: {exc}") from exc

    # Record the billable call regardless of outcome — the request was made.
    db.record_usage("foreclosure", _now_iso())

    if resp.status_code == 401:
        raise ForeclosureError("Foreclosure Data Hub rejected the key (401). "
                               "Check FORECLOSURE_API_KEY.")
    if resp.status_code == 403:
        raise ForeclosureError("Foreclosure Data Hub 403 — subscription inactive or "
                               "your plan lacks API access (weekly plans don't).")
    if resp.status_code == 429:
        raise ForeclosureError("Foreclosure Data Hub rate limit hit (429). Wait a bit.")
    if resp.status_code >= 400:
        raise ForeclosureError(f"Foreclosure Data Hub error {resp.status_code}: "
                               f"{resp.text[:200]}")

    data = resp.json()
    # Standard envelope: {"data": [...], "meta": {...}} — be tolerant of variants.
    if isinstance(data, dict):
        data = data.get("data") or data.get("properties") or data.get("results") or []
    return data or []


# --- Mapping raw JSON -> our Listing model ---------------------------------

def _slug(*parts) -> str:
    text = " ".join(str(p) for p in parts if p)
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:80]


def raw_to_listing(raw: dict) -> Listing:
    """Convert one Foreclosure Data Hub record into our Listing object.

    beds/baths/sqft are usually absent in foreclosure data and stay None. The bid
    amount becomes list_price; the lender's estimated value becomes est_value.
    """
    address = _first(raw, "address", "property_address", "addressLine", "street", default="")
    city = _first(raw, "city", default="")
    state = _first(raw, "state", default="")
    zip_code = _first(raw, "zip", "zip_code", "zipcode", "postal_code", default="")
    sale_date = _first(raw, "sale_date", "saleDate", "auction_date", "auctionDate")
    source = _first(raw, "source", "source_id", "data_source", default="fdh")

    bid = _first(raw, "bid_amount", "bidAmount", "opening_bid", "openingBid",
                 "amount", "price")
    est_value = _first(raw, "est_value", "estimated_value", "estimatedValue",
                       "redfin_value", "redfinValue", "value")
    status = _first(raw, "status", "type", "foreclosure_type", "category",
                    default="Foreclosure")

    # Stable id, prefixed so it's clearly a foreclosure row in the shared table.
    natural = _slug(address, zip_code, sale_date or "", source)
    listing_id = ID_PREFIX + (natural or _slug(str(raw.get("id") or address)))

    return Listing(
        id=listing_id,
        address=address or "",
        city=city or "",
        state=state or "",
        zip_code=str(zip_code or ""),
        latitude=_first(raw, "latitude", "lat"),
        longitude=_first(raw, "longitude", "lng", "lon"),
        list_price=_num(bid),
        beds=None, baths=None, sqft=None, year_built=None,
        property_type="Foreclosure",
        status=str(status or "Foreclosure"),
        est_value=_num(est_value),
    )


def _num(v):
    """Coerce a possibly-string number to float, or None."""
    if v in (None, ""):
        return None
    try:
        return float(str(v).replace("$", "").replace(",", ""))
    except (TypeError, ValueError):
        return None


# --- Sync: fetch for all configured zips and cache the results -------------

def sync_listings(
    *,
    limit_per_area: int = MAX_PAGE_SIZE,
    incremental: bool = False,  # accepted for a uniform call signature; full each run
    progress: Optional[Callable[[str], None]] = None,
    state: Optional[str] = None,
    zips: Optional[list[str]] = None,
) -> dict:
    """
    Fetch foreclosure/REO records for the given (or configured) U.S. areas and cache.

    Nationwide-capable: pass `state` and/or `zips` to fetch any U.S. region on demand;
    if omitted, falls back to the configured area (settings). Foreclosure data is small
    and bounded (capped per area), so we pull it fresh each run rather than diffing.
    `incremental` is accepted but ignored, so the worker can call this exactly like
    rentcast.sync_listings().

    Returns: {new, updated, price_drops[], total_seen, errors[], synced_at}
    """
    when = _now_iso()
    state = state or settings.active_state
    zips = zips if zips is not None else settings.all_zips()
    targets: list[tuple[Optional[str], Optional[str]]]
    if zips:
        targets = [(z, None) for z in zips]      # (zip, county)
    else:
        targets = [(None, None)]                 # whole-state fallback

    new_count = updated_count = total_seen = 0
    price_drops: list[dict] = []
    errors: list[str] = []

    for zip_code, county in targets:
        where = zip_code or county or state
        if progress:
            progress(f"Fetching foreclosures {where}…")
        try:
            records = fetch_listings_raw(state=state, county=county,
                                         zip_code=zip_code, page_size=limit_per_area)
        except ForeclosureError as exc:
            errors.append(f"{where}: {exc}")
            continue

        for raw in records:
            listing = raw_to_listing(raw)
            if not listing.id or listing.id == ID_PREFIX:
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
            if (result["price_changed"] and result["previous_price"] is not None
                    and listing.list_price is not None
                    and float(listing.list_price) < float(result["previous_price"])):
                price_drops.append({"address": listing.address,
                                    "old": float(result["previous_price"]),
                                    "new": float(listing.list_price)})

    db.set_meta("lastsync:fc:global", when)
    return {"new": new_count, "updated": updated_count, "price_drops": price_drops,
            "total_seen": total_seen, "errors": errors, "synced_at": when}


def last_sync_time() -> Optional[str]:
    """ISO timestamp of the most recent foreclosure sync, or None."""
    return db.get_meta("lastsync:fc:global")


# --- Read cached foreclosure listings for display (NO API call) ------------

def load_cached_listings(limit: int = 300) -> list[Listing]:
    """Read ONLY foreclosure rows (id LIKE 'FC:%') from the shared cache."""
    import json

    with db.connect() as conn:
        rows = conn.execute(
            "SELECT id, payload, previous_price FROM listings "
            "WHERE id LIKE ? ORDER BY last_seen DESC LIMIT ?",
            (ID_PREFIX + "%", limit),
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
        listings.append(listing)
    return listings


def cached_listing_count() -> int:
    with db.connect() as conn:
        return conn.execute(
            "SELECT COUNT(*) AS n FROM listings WHERE id LIKE ?",
            (ID_PREFIX + "%",),
        ).fetchone()["n"]

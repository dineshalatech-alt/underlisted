"""
Aerial (satellite) image of a property — Google Static Maps.

Same cost design as Street View:
  * Keyed by LOCATION, shared across users and listings.
  * Downloaded ONCE at a small size, then served from disk forever.
  * Billable, so it is gated behind an explicit user action (a button on the
    detail page) — never fetched for cards or on page load.

Reuses your Google key (STREETVIEW_API_KEY). You must also enable the
"Maps Static API" in the same Google Cloud project for this to work.
Docs: https://developers.google.com/maps/documentation/maps-static
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

import requests

from config.settings import DATA_DIR, settings
from src.cache import db
from src.models import Listing

STATIC_MAP_URL = "https://maps.googleapis.com/maps/api/staticmap"
REQUEST_TIMEOUT = 30

AERIAL_DIR = DATA_DIR / "aerial"
SOURCE = "aerial"


def _location_for(listing: Listing) -> Optional[str]:
    if listing.latitude is not None and listing.longitude is not None:
        return f"{listing.latitude},{listing.longitude}"
    if listing.address:
        return listing.address
    return None


def _location_key(listing: Listing) -> Optional[str]:
    if listing.latitude is not None and listing.longitude is not None:
        return f"geo:{round(float(listing.latitude), 5)},{round(float(listing.longitude), 5)}"
    if listing.address:
        return "addr:" + " ".join(listing.address.lower().split())
    return None


def _aerial_path(location_key: str) -> Path:
    digest = hashlib.sha1(location_key.encode("utf-8")).hexdigest()[:16]
    return AERIAL_DIR / f"{digest}.png"


def get_aerial(listing: Listing, *, count_against_user: bool = True,
               cache_only: bool = False) -> dict:
    """Return {"status": "ok"|"no_key"|"no_location"|"capped"|"error", "path": ...}."""
    if not settings.has_streetview:  # same Google key
        return {"status": "no_key", "path": None}

    location = _location_for(listing)
    loc_key = _location_key(listing)
    if not location or not loc_key:
        return {"status": "no_location", "path": None}

    cache_key = f"aerial:{loc_key}"
    path = _aerial_path(loc_key)

    cached = db.cache_get(cache_key)  # images effectively never expire
    if cached is not None and cached.get("status") == "ok" and path.exists():
        db.note_cache_hit(SOURCE)
        return {"status": "ok", "path": str(path)}

    if cache_only:
        return {"status": "capped", "path": None}

    db.note_cache_miss(SOURCE)
    try:
        img = requests.get(
            STATIC_MAP_URL,
            params={
                "center": location,
                "zoom": settings.aerial_zoom,
                "size": settings.aerial_size,
                "maptype": "satellite",
                "key": settings.streetview_api_key,
            },
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        return {"status": "error", "path": None, "detail": str(exc)}

    if img.status_code != 200 or not img.content:
        return {"status": "error", "path": None,
                "detail": f"Static Map HTTP {img.status_code}: {img.text[:120]}"}

    AERIAL_DIR.mkdir(parents=True, exist_ok=True)
    path.write_bytes(img.content)
    db.record_usage(SOURCE)
    db.cache_put(cache_key, "aerial", {"status": "ok"})
    if count_against_user:
        db.record_user_lookup(settings.current_user_id, SOURCE)

    return {"status": "ok", "path": str(path)}

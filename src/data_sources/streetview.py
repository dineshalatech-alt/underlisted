"""
Google Street View — the REAL exterior photo of each property.

Cost design:
  * The cache key is the LOCATION (rounded lat/long, else normalized address) —
    NOT the listing id and NOT the user. So the same house photographed under two
    different listing ids, viewed by any number of customers, costs ONE fetch.
  * Google's metadata check is FREE; the image is billable. We metadata-check
    first, download the image ONCE at a small size, save it, and serve that file
    forever after (images effectively never expire — a building doesn't move).
  * Lazy by design: the UI calls this only when a user opens/asks for a photo.

We always use the real Street View image for the current property — never AI.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

import requests

from config.settings import DATA_DIR, settings
from src.cache import db
from src.models import Listing

METADATA_URL = "https://maps.googleapis.com/maps/api/streetview/metadata"
IMAGE_URL = "https://maps.googleapis.com/maps/api/streetview"
REQUEST_TIMEOUT = 30

PHOTO_DIR = DATA_DIR / "streetview"
SOURCE = "streetview"


def has_streetview() -> bool:
    return settings.has_streetview


def _location_for(listing: Listing) -> Optional[str]:
    """The query Google understands — exact coords preferred, else the address."""
    if listing.latitude is not None and listing.longitude is not None:
        return f"{listing.latitude},{listing.longitude}"
    if listing.address:
        return listing.address
    return None


def _location_key(listing: Listing) -> Optional[str]:
    """
    A STABLE, user-independent key for this physical spot. Rounding coords to
    5 decimals (~1 meter) means tiny differences collapse to the same key, so we
    never pay twice for effectively the same location.
    """
    if listing.latitude is not None and listing.longitude is not None:
        return f"geo:{round(float(listing.latitude), 5)},{round(float(listing.longitude), 5)}"
    if listing.address:
        return "addr:" + " ".join(listing.address.lower().split())
    return None


def _photo_path(location_key: str) -> Path:
    digest = hashlib.sha1(location_key.encode("utf-8")).hexdigest()[:16]
    return PHOTO_DIR / f"{digest}.jpg"


def get_photo(listing: Listing, *, count_against_user: bool = True,
              cache_only: bool = False) -> dict:
    """
    Return {"status": ..., "path": <str|None>} for a listing's real photo.

    status: "ok" | "none" | "no_key" | "no_location" | "capped" | "error"

    A cache HIT (already downloaded) costs nothing and is NOT counted against the
    user's monthly cap. Only a real, billable download is counted.
    `cache_only=True` serves cached photos but refuses NEW fetches (returns
    "capped") — used to enforce the per-user monthly cap.
    """
    if not settings.has_streetview:
        return {"status": "no_key", "path": None}

    location = _location_for(listing)
    loc_key = _location_key(listing)
    if not location or not loc_key:
        return {"status": "no_location", "path": None}

    cache_key = f"streetview:{loc_key}"
    path = _photo_path(loc_key)

    # 1) Shared-cache HIT — serve the saved file, no call, no bill, no user charge.
    cached = db.cache_get(cache_key)  # images never expire
    if cached is not None:
        db.note_cache_hit(SOURCE)
        if cached.get("status") == "ok" and path.exists():
            return {"status": "ok", "path": str(path)}
        if cached.get("status") == "none":
            return {"status": "none", "path": None}
        # else fall through (file went missing) and re-fetch

    if cache_only:
        return {"status": "capped", "path": None}

    db.note_cache_miss(SOURCE)

    # 2) FREE metadata check.
    try:
        meta = requests.get(
            METADATA_URL,
            params={"location": location, "key": settings.streetview_api_key,
                    "source": "outdoor"},
            timeout=REQUEST_TIMEOUT,
        ).json()
    except requests.RequestException as exc:
        return {"status": "error", "path": None, "detail": str(exc)}

    status = meta.get("status")
    if status == "REQUEST_DENIED":
        return {"status": "error", "path": None,
                "detail": meta.get("error_message", "Street View request denied.")}
    if status != "OK":
        db.cache_put(cache_key, "streetview", {"status": "none"})
        return {"status": "none", "path": None}

    # 3) Download ONCE at the configured (small) size.
    try:
        img = requests.get(
            IMAGE_URL,
            params={
                "size": settings.streetview_size,
                "location": location,
                "source": "outdoor",
                "key": settings.streetview_api_key,
            },
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        return {"status": "error", "path": None, "detail": str(exc)}

    if img.status_code != 200 or not img.content:
        return {"status": "error", "path": None,
                "detail": f"Street View image HTTP {img.status_code}"}

    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    path.write_bytes(img.content)
    db.record_usage(SOURCE)
    db.cache_put(cache_key, "streetview", {"status": "ok"})
    if count_against_user:
        db.record_user_lookup(settings.current_user_id, SOURCE)

    return {"status": "ok", "path": str(path)}

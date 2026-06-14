"""
Risk flags — fire & flood — from FREE public FEMA data. THE differentiator.

The big competitors show price, comps, rent — but DON'T warn you that a "cheap"
home sits in a wildfire or flood zone where insurance is expensive (or unavailable),
which wrecks the real cost. We do, using free government data:
  * FEMA National Flood Hazard Layer (NFHL)  -> the flood zone (AE, X, VE, …)
  * FEMA National Risk Index (NRI)            -> the wildfire risk rating

Both are FREE ArcGIS REST endpoints (no key, NOT billable). Results are cached in
the shared store with a long TTL (risk barely changes), so it's cheap and fast, and
the app only ever reads the cache (the worker populates it on a schedule).
"""

from __future__ import annotations

import json
from typing import Optional

import requests

from config.settings import settings
from src.cache import db
from src.data_sources import nri
from src.models import Listing, RiskFlags

# FEMA NFHL — layer 28 = Flood Hazard Zones (S_FLD_HAZ_AR), field FLD_ZONE.
NFHL_URL = ("https://hazards.fema.gov/arcgis/rest/services/public/NFHL/"
            "MapServer/28/query")
# FEMA National Risk Index — census tracts; WFIR_RISKR = wildfire risk rating.
NRI_URL = ("https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/"
           "National_Risk_Index_Census_Tracts/FeatureServer/0/query")
# FCC Area API — free, no key: a lat/lon -> its county FIPS (for the NRI county
# fallback below). The result never changes for a point, so we cache it forever.
FCC_AREA_URL = "https://geo.fcc.gov/api/census/area"
TIMEOUT = 25


def _key(lat: float, lon: float) -> str:
    """Shared cache key, rounded so nearby homes share one risk lookup."""
    return f"risk:{round(float(lat), 4)},{round(float(lon), 4)}"


def _flood_zone(lat: float, lon: float) -> Optional[str]:
    """FEMA flood zone string (e.g. 'AE', 'X', 'VE') for a point, or None."""
    params = {"geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint",
              "inSR": "4326", "spatialRel": "esriSpatialRelIntersects",
              "outFields": "FLD_ZONE,ZONE_SUBTY", "returnGeometry": "false", "f": "json"}
    resp = requests.get(NFHL_URL, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    feats = resp.json().get("features", [])
    return feats[0]["attributes"].get("FLD_ZONE") if feats else None


def _nri(lat: float, lon: float) -> dict:
    """FEMA NRI ratings (wildfire, earthquake, overall) for a point."""
    geom = json.dumps({"x": lon, "y": lat, "spatialReference": {"wkid": 4326}})
    params = {"where": "1=1", "geometry": geom, "geometryType": "esriGeometryPoint",
              "inSR": "4326", "spatialRel": "esriSpatialRelIntersects",
              "outFields": "WFIR_RISKR,ERQK_RISKR,RISK_RATNG", "returnGeometry": "false",
              "resultRecordCount": 1, "f": "json"}
    resp = requests.get(NRI_URL, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    feats = resp.json().get("features", [])
    a = feats[0]["attributes"] if feats else {}
    return {"wildfire": a.get("WFIR_RISKR"), "earthquake": a.get("ERQK_RISKR"),
            "overall": a.get("RISK_RATNG")}


def _norm_fire(rating: Optional[str]) -> str:
    r = (rating or "").lower()
    if "very high" in r or "relatively high" in r:
        return "High"
    if "moderate" in r:
        return "Moderate"
    if r:
        return "Low"
    return "Unknown"


def _is_sfha(zone: Optional[str]) -> bool:
    """Special Flood Hazard Area = zones starting A or V (mandatory flood insurance)."""
    return (zone or "").upper()[:1] in ("A", "V")


def _flood_cat(zone: Optional[str]) -> str:
    if zone is None:
        return "Unknown"
    if _is_sfha(zone):
        return "High"
    if zone.upper().startswith("X"):
        return "Minimal"
    return zone


def _note(fire_cat: str, flood_zone: Optional[str], flood_cat: str,
          quake_cat: str = "Unknown") -> Optional[str]:
    notes = []
    if fire_cat == "High":
        notes.append("High wildfire risk — insurance may be costly or hard to get.")
    elif fire_cat == "Moderate":
        notes.append("Some wildfire risk — check the insurance cost.")
    if flood_cat == "High":
        if flood_zone:
            notes.append(f"In a FEMA flood zone ({flood_zone}) — flood insurance is "
                         "likely required and adds to the monthly cost.")
        else:
            notes.append("High flood risk for this county (FEMA) — budget for flood "
                         "insurance; it adds to the monthly cost.")
    elif flood_cat == "Moderate":
        notes.append("Some flood risk for this county (FEMA) — check the flood-"
                     "insurance cost.")
    if quake_cat == "High":
        notes.append("High earthquake risk — earthquake insurance is usually a separate, "
                     "pricey policy.")
    return " ".join(notes) or None


def _county_fips(lat: float, lon: float) -> Optional[str]:
    """The 5-digit county FIPS for a point (FREE FCC lookup), cached forever."""
    ck = f"fips:{round(float(lat), 4)},{round(float(lon), 4)}"
    cached = db.cache_get(ck)  # no TTL — a coordinate's county never changes
    if cached is not None:
        return cached or None
    try:
        resp = requests.get(FCC_AREA_URL, params={"lat": lat, "lon": lon,
                            "format": "json"}, timeout=TIMEOUT)
        resp.raise_for_status()
        results = resp.json().get("results", []) or []
        fips = (results[0].get("county_fips") if results else None) or ""
    except Exception:
        return None  # FCC down -> just skip the county fallback, never crash
    db.cache_put(ck, "fips", fips)
    return fips or None


def _merge_county_fallback(raw: dict, lat: float, lon: float) -> dict:
    """
    Fill any MISSING NRI rating in `raw` from the FREE county-level NRI table.
    The per-point tract query is preferred; this only fills the blanks so a
    buyer's insurance-risk warning is never empty. No-op if county data isn't
    built yet or we can't resolve the county. Never overwrites a tract value.
    """
    if not nri.has_data():
        return raw
    if raw.get("wildfire") and raw.get("flood_zone") and raw.get("overall"):
        return raw  # tract layer already gave us everything we need
    fips = _county_fips(lat, lon)
    if not fips:
        return raw
    c = nri.county_risk(fips)
    if not c:
        return raw
    if not raw.get("wildfire") and c.get("wildfire"):
        raw["wildfire"] = c["wildfire"]
    if not raw.get("earthquake") and c.get("earthquake"):
        raw["earthquake"] = c["earthquake"]
    if not raw.get("overall") and c.get("overall"):
        raw["overall"] = c["overall"]
    # Flood: the tract FLD_ZONE (e.g. "AE") is more specific; only when it's
    # missing do we fall back to the county flood RATING (e.g. "Relatively High").
    if not raw.get("flood_zone") and c.get("flood"):
        raw["county_flood"] = c["flood"]
    return raw


def get_risk(listing: Listing, *, cache_only: bool = False) -> RiskFlags:
    """
    Fire & flood risk for a listing (free FEMA data). Shared cache, long TTL.
    `cache_only=True` returns cached risk but makes NO live call (used on page load).
    """
    lat, lon = listing.latitude, listing.longitude
    if lat is None or lon is None:
        return RiskFlags()

    ck = _key(lat, lon)
    ttl = settings.ttl_seconds("risk_days", 180 * 86400)
    cached = db.cache_get(ck, max_age_seconds=ttl)
    if cached is not None:
        db.note_cache_hit("risk")
        raw = cached
    elif cache_only:
        return RiskFlags()
    else:
        db.note_cache_miss("risk")
        try:
            zone = _flood_zone(lat, lon)
        except Exception:
            zone = None
        try:
            nri_pt = _nri(lat, lon)
        except Exception:
            nri_pt = {}
        raw = {"flood_zone": zone, "wildfire": nri_pt.get("wildfire"),
               "earthquake": nri_pt.get("earthquake"), "overall": nri_pt.get("overall")}
        # FREE county-level NRI fills any blanks the per-point query left.
        raw = _merge_county_fallback(raw, lat, lon)
        db.cache_put(ck, "risk", raw)

    fire_cat = _norm_fire(raw.get("wildfire"))
    quake_cat = _norm_fire(raw.get("earthquake"))
    flood_zone = raw.get("flood_zone")
    flood_cat = _flood_cat(flood_zone)
    # No specific FEMA flood zone? Use the county flood RATING as a softer signal.
    if flood_zone is None and raw.get("county_flood"):
        flood_cat = _norm_fire(raw["county_flood"])
    return RiskFlags(fire_zone=fire_cat, flood_zone=flood_cat, quake_zone=quake_cat,
                     overall_risk=raw.get("overall"),
                     insurance_note=_note(fire_cat, flood_zone, flood_cat, quake_cat))

"""
Tests for the two FREE enrichment sources added 2026-06-14:
  * src/data_sources/nri.py             — OpenFEMA National Risk Index (county)
  * src/data_sources/building_permits.py — Census Building Permits (supply signal)

Same style as test_affordability.py: PURE-logic, NO network, NO API calls. We test
the parsing, the rating logic, the "fill the blanks" risk merge, and — most
importantly — that everything degrades gracefully when the data files are absent
(so the app never crashes if a free source hasn't been built yet).

Run from the project root:
    .venv/Scripts/python.exe -m pytest tests/test_free_sources.py -q
or without pytest:
    .venv/Scripts/python.exe tests/test_free_sources.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_sources import building_permits as bps  # noqa: E402
from src.data_sources import nri  # noqa: E402
from src.data_sources import risk  # noqa: E402


# --- A small real-shaped slice of the Census BPS county annual file -----------
# Two header rows + a blank-ish row + real county rows (taken from co2024a.txt).
_BPS_SAMPLE = (
    "Survey,FIPS,FIPS,Region,Division,County,,1-unit,,,2-units,,,3-4 units,,,5+ units\n"
    "Date,State,County,Code,Code,Name,Bldgs,Units,Value,Bldgs,Units,Value,"
    "Bldgs,Units,Value,Bldgs,Units,Value\n"
    " \n"
    "2024,01,001,3,6,Autauga County,221,221,82537210,0,0,0,0,0,0,0,0,0\n"
    "2024,01,003,3,6,Baldwin County,3394,3394,1101017641,4,8,1037436,0,0,0,11,481,121592707\n"
    "2024,06,037,4,9,Los Angeles County,1200,1200,500000000,10,20,5000000,0,0,0,300,9000,900000000\n"
)


# ---------------------------------------------------------------------------
# Census Building Permits
# ---------------------------------------------------------------------------

def test_bps_parses_real_file_shape():
    parsed = bps._parse(_BPS_SAMPLE)
    # FIPS are zero-padded state(2)+county(3).
    assert "01001" in parsed
    assert "06037" in parsed
    autauga = parsed["01001"]
    assert autauga["units_1"] == 221
    assert autauga["total_units"] == 221  # only 1-unit permits
    la = parsed["06037"]
    # total = 1200 (1u) + 20 (2u) + 0 (3-4) + 9000 (5+)
    assert la["total_units"] == 1200 + 20 + 0 + 9000
    assert la["units_5plus"] == 9000


def test_bps_skips_garbage_rows():
    parsed = bps._parse("h1\nh2\nnot,a,real,row\n,,,\n")
    assert parsed == {}


def test_bps_county_permits_categorises_supply():
    # Inject a parsed map directly so there's no network.
    bps._CACHE = {
        "10000": {"year": "2024", "total_units": 6000, "units_1": 6000, "units_5plus": 0},
        "20000": {"year": "2024", "total_units": 800, "units_1": 800, "units_5plus": 0},
        "30000": {"year": "2024", "total_units": 50, "units_1": 50, "units_5plus": 0},
    }
    try:
        hot = bps.county_permits("10000")
        assert "new homes are being built" in hot["note"].lower() \
            or "fresh supply" in hot["note"].lower()
        assert "not endorsed" in hot["attribution"].lower()  # required notice present
        mid = bps.county_permits("20000")
        assert "balanced" in mid["note"].lower()
        low = bps.county_permits("30000")
        assert "limited" in low["note"].lower() or "support prices" in low["note"].lower()
    finally:
        bps._CACHE = None


def test_bps_degrades_gracefully_when_no_data():
    bps._CACHE = {}  # simulate "file never built"
    try:
        assert bps.has_data() is False
        assert bps.county_permits("06037") is None
        assert bps.county_permits(None) is None
    finally:
        bps._CACHE = None


# ---------------------------------------------------------------------------
# OpenFEMA National Risk Index (county)
# ---------------------------------------------------------------------------

def test_nri_worse_picks_higher_risk():
    assert nri._worse("Very Low", "Relatively High") == "Relatively High"
    assert nri._worse(None, "Very Low") == "Very Low"
    assert nri._worse("Relatively Moderate", None) == "Relatively Moderate"
    assert nri._worse(None, None) is None


def test_nri_county_risk_lookup_and_padding():
    nri._CACHE = {
        "06037": {"wildfire": "Relatively High", "flood": "Very Low",
                  "earthquake": "Relatively High", "overall": "Relatively High",
                  "county": "Los Angeles", "state": "CA"},
    }
    try:
        # integer-ish / unpadded FIPS should still resolve via zfill(5)
        r = nri.county_risk("6037")
        assert r and r["wildfire"] == "Relatively High"
        assert nri.has_data() is True
    finally:
        nri._CACHE = None


def test_nri_degrades_gracefully_when_no_data():
    nri._CACHE = {}
    try:
        assert nri.has_data() is False
        assert nri.county_risk("06037") is None
        assert nri.county_risk(None) is None
    finally:
        nri._CACHE = None


# ---------------------------------------------------------------------------
# risk.py county fallback — fills blanks, never overwrites a tract value
# ---------------------------------------------------------------------------

def test_risk_merge_fills_only_missing_fields(monkeypatch=None):
    # Tract query found wildfire but NOT earthquake/overall; county has them.
    nri._CACHE = {"06037": {"wildfire": "Very Low", "flood": "Relatively High",
                            "earthquake": "Relatively High",
                            "overall": "Relatively High", "county": "LA", "state": "CA"}}
    # Avoid any network in _county_fips by patching it to a fixed FIPS.
    orig_fips = risk._county_fips
    risk._county_fips = lambda lat, lon: "06037"
    try:
        raw = {"flood_zone": None, "wildfire": "Relatively Moderate",
               "earthquake": None, "overall": None}
        merged = risk._merge_county_fallback(dict(raw), 34.05, -118.24)
        # wildfire was already set by the tract layer -> NOT overwritten
        assert merged["wildfire"] == "Relatively Moderate"
        # earthquake/overall were blank -> filled from county
        assert merged["earthquake"] == "Relatively High"
        assert merged["overall"] == "Relatively High"
        # no specific flood zone -> county flood rating offered as a soft signal
        assert merged.get("county_flood") == "Relatively High"
    finally:
        risk._county_fips = orig_fips
        nri._CACHE = None


def test_risk_merge_noop_without_county_data():
    nri._CACHE = {}  # county table not built yet
    try:
        raw = {"flood_zone": None, "wildfire": None, "earthquake": None, "overall": None}
        merged = risk._merge_county_fallback(dict(raw), 34.05, -118.24)
        assert merged == raw  # nothing added, nothing crashed
    finally:
        nri._CACHE = None


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        fn()
        passed += 1
        print(f"  ok  {fn.__name__}")
    print(f"\n{passed}/{len(fns)} free-source tests passed.")


if __name__ == "__main__":
    _run_all()

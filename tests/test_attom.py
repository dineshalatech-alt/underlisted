"""
Tests for the ATTOM data source (src/data_sources/attom.py).

PURE-logic tests — no API calls, no network. They lock in the parts that must
stay correct no matter what ATTOM returns: address parsing, cache keys, numeric
coercion, AVM mapping, and pulling the latest sale out of sale history.

Run from the project root:
    .venv/Scripts/python.exe -m pytest tests/test_attom.py -q
or without pytest:
    .venv/Scripts/python.exe tests/test_attom.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_sources import attom  # noqa: E402
from src.models import Listing, ValueEstimate  # noqa: E402


def _listing(**kw) -> Listing:
    base = dict(
        id="x", address="4529 Winona Court, Denver, CO 80212",
        city="Denver", state="CO", zip_code="80212",
    )
    base.update(kw)
    return Listing(**base)


# --- Address parsing -------------------------------------------------------
def test_address_pair_splits_street_and_city_state():
    assert attom._address_pair(_listing()) == ("4529 Winona Court", "Denver, CO")


def test_address_pair_uses_text_before_first_comma_for_street():
    L = _listing(address="12 Main St, Apt 3, Austin, TX 78701", city="Austin", state="TX")
    assert attom._address_pair(L) == ("12 Main St", "Austin, TX")


def test_address_pair_none_without_city_state():
    assert attom._address_pair(_listing(city="", state="")) is None


def test_address_pair_none_without_street():
    assert attom._address_pair(_listing(address="")) is None


# --- Cache keys ------------------------------------------------------------
def test_cache_key_is_normalized_and_namespaced():
    assert attom._cache_key(_listing(), "value") == "attom:value:4529 winona court denver, co"


def test_cache_key_kinds_differ():
    L = _listing()
    assert attom._cache_key(L, "value") != attom._cache_key(L, "salehistory")


def test_cache_key_none_when_unidentifiable():
    assert attom._cache_key(_listing(address="", city="", state=""), "value") is None


# --- Numeric coercion ------------------------------------------------------
def test_num_handles_strings_and_blanks():
    assert attom._num("525000") == 525000.0
    assert attom._num(None) is None
    assert attom._num("") is None
    assert attom._num("abc") is None


def test_num_treats_zero_or_negative_as_missing():
    # ATTOM uses 0 to mean "no value"; we don't want a $0 AVM polluting the score.
    assert attom._num(0) is None
    assert attom._num(-10) is None


# --- AVM mapping -----------------------------------------------------------
def test_map_avm_pulls_value_and_range():
    data = {"property": [{"avm": {"amount": {"value": 525000, "low": 500000, "high": 560000}}}]}
    v = attom._map_avm(data)
    assert isinstance(v, ValueEstimate)
    assert (v.avm, v.value_low, v.value_high) == (525000.0, 500000.0, 560000.0)


def test_map_avm_empty_is_safe():
    v = attom._map_avm({})
    assert v.avm is None and v.value_low is None and v.value_high is None


# --- Latest sale extraction ------------------------------------------------
def test_extract_last_sale_picks_most_recent():
    data = {"property": [{"salehistory": [
        {"amount": {"saleamt": 450000, "salerecdate": "2018-05-01"}},
        {"amount": {"saleamt": 710000, "salerecdate": "2023-10-23"}},
        {"amount": {"saleamt": 600000, "salerecdate": "2021-02-10"}},
    ]}]}
    best = attom._extract_last_sale(data)
    assert best == {"amount": 710000.0, "date": "2023-10-23"}


def test_extract_last_sale_skips_blank_amounts():
    data = {"property": [{"salehistory": [
        {"amount": {"saleamt": 0, "salerecdate": "2024-01-01"}},
        {"amount": {"saleamt": 320000, "salerecdate": "2019-09-09"}},
    ]}]}
    assert attom._extract_last_sale(data) == {"amount": 320000.0, "date": "2019-09-09"}


def test_extract_last_sale_none_when_no_history():
    assert attom._extract_last_sale({"property": [{}]}) is None
    assert attom._extract_last_sale({}) is None


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        fn()
        passed += 1
        print(f"  ok  {fn.__name__}")
    print(f"\n{passed}/{len(fns)} attom tests passed.")


if __name__ == "__main__":
    _run_all()

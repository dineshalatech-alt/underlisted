"""
Tests for the "Call / Email the listing agent" feature added 2026-06-14.

Covers:
  * src/data_sources/rentcast.py: raw_to_listing maps listingAgent / listingOffice
    (name/phone/email/website) and mlsNumber/mlsName from the raw RentCast record.
  * src/models.py: listing_contact() picks the best contact with a graceful
    fallback chain: agent -> brokerage office -> neutral "Ask a local agent".

PURE-logic, NO network, NO API calls (the agent data rides along inside the
listing payload we already cache — zero new RentCast calls).

Run from the project root:
    .venv/Scripts/python.exe -m pytest tests/test_agent_contact.py -q
or without pytest:
    .venv/Scripts/python.exe tests/test_agent_contact.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_sources import rentcast  # noqa: E402
from src.models import listing_contact  # noqa: E402


# --- A real-shaped RentCast sale-listing record (trimmed) --------------------
_RAW_WITH_AGENT = {
    "id": "123-Main-St,Austin,TX-78701",
    "formattedAddress": "123 Main St, Austin, TX 78701",
    "city": "Austin",
    "state": "TX",
    "zipCode": "78701",
    "price": 425000,
    "bedrooms": 3,
    "bathrooms": 2,
    "squareFootage": 1800,
    "status": "Active",
    "daysOnMarket": 12,
    "mlsName": "Unlock MLS",
    "mlsNumber": "AUS-998877",
    "listingAgent": {
        "name": "Jane Doe",
        "phone": "(512) 555-0142",
        "email": "jane@example-realty.com",
        "website": "https://janedoe-homes.com",
    },
    "listingOffice": {
        "name": "Example Realty Group",
        "phone": "(512) 555-0100",
        "email": "office@example-realty.com",
        "website": "example-realty.com",
    },
}


def test_raw_to_listing_maps_agent_fields():
    l = rentcast.raw_to_listing(_RAW_WITH_AGENT)
    assert l.agent_name == "Jane Doe"
    assert l.agent_phone == "(512) 555-0142"
    assert l.agent_email == "jane@example-realty.com"
    assert l.agent_website == "https://janedoe-homes.com"
    assert l.office_name == "Example Realty Group"
    assert l.office_phone == "(512) 555-0100"
    assert l.mls_number == "AUS-998877"
    assert l.mls_name == "Unlock MLS"


def test_listing_contact_prefers_agent():
    l = rentcast.raw_to_listing(_RAW_WITH_AGENT)
    c = listing_contact(l)
    assert c["kind"] == "agent"
    assert c["name"] == "Jane Doe"
    assert c["phone"] == "(512) 555-0142"
    assert c["email"] == "jane@example-realty.com"


def test_falls_back_to_office_when_agent_missing():
    raw = dict(_RAW_WITH_AGENT)
    raw.pop("listingAgent")
    l = rentcast.raw_to_listing(raw)
    assert l.agent_name is None
    c = listing_contact(l)
    assert c["kind"] == "office"
    assert c["name"] == "Example Realty Group"
    assert c["phone"] == "(512) 555-0100"


def test_neutral_fallback_when_no_contact_at_all():
    raw = {
        "id": "x",
        "formattedAddress": "9 Nowhere Rd, Smalltown, KS 66002",
        "city": "Smalltown",
        "state": "KS",
        "zipCode": "66002",
        "price": 150000,
        "mlsNumber": "KS-12345",
    }
    l = rentcast.raw_to_listing(raw)
    assert l.agent_name is None and l.office_name is None
    c = listing_contact(l)
    assert c["kind"] == "neutral"
    assert c["name"] == "Ask a local agent"
    assert c["phone"] is None and c["email"] is None
    assert c["mls_number"] == "KS-12345"  # neutral line can still cite the MLS #


def test_blank_strings_treated_as_missing():
    raw = dict(_RAW_WITH_AGENT)
    raw["listingAgent"] = {"name": "  ", "phone": "", "email": None, "website": ""}
    l = rentcast.raw_to_listing(raw)
    # All agent fields blank -> none mapped -> should fall back to the office.
    assert l.agent_name is None and l.agent_phone is None
    c = listing_contact(l)
    assert c["kind"] == "office"


def test_non_dict_blocks_dont_crash():
    raw = dict(_RAW_WITH_AGENT)
    raw["listingAgent"] = "not a dict"
    raw["listingOffice"] = None
    l = rentcast.raw_to_listing(raw)
    assert l.agent_name is None and l.office_name is None
    c = listing_contact(l)
    assert c["kind"] == "neutral"


def test_old_listing_without_any_contact_keys_is_safe():
    # Simulates a listing cached BEFORE this feature existed (no agent/office keys).
    raw = {
        "id": "old-1",
        "formattedAddress": "1 Old Rd, Town, OH 44101",
        "city": "Town",
        "state": "OH",
        "zipCode": "44101",
        "price": 99000,
    }
    l = rentcast.raw_to_listing(raw)
    assert l.agent_name is None
    assert l.mls_number is None
    c = listing_contact(l)
    assert c["kind"] == "neutral"  # never crashes, always usable


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        fn()
        passed += 1
        print(f"  ok  {fn.__name__}")
    print(f"\n{passed}/{len(fns)} agent-contact tests passed.")


if __name__ == "__main__":
    _run_all()

"""
Display data for the UI — uses REAL cached listings first; falls back to clearly
marked SAMPLE listings if the cache is empty. Makes ZERO API calls.

For each listing it returns a small view-model: the listing, a value estimate, a
rent figure (and whether that rent is a sample placeholder), and the Deal Score.
The Deal Score for real listings is computed from CACHED estimates only, so it
matches the real numbers; sample rent is shown for design but flagged.

Foreclosures (bank-owned / REO) are loaded from the foreclosure source and shown
as a lighter card (bid vs estimated value), since that data has no beds/baths/rent.
Until the live foreclosure feed is connected, a couple of clearly-marked DEMO
foreclosures are shown so the feature is visible — still zero API calls.
"""

from __future__ import annotations

from config.settings import settings
from src.cache import db
from src.data_sources import attom as attom_src
from src.data_sources import foreclosure, rentcast, risk
from src.models import Listing, RentEstimate, RiskFlags, ValueEstimate
from src.scoring import deal_score

# --- Realistic SAMPLE listings (used only if the cache is empty) ---
_SAMPLE = [
    (Listing(id="S1", address="1420 Larkspur Ave, Sacramento, CA 95815",
             city="Sacramento", state="CA", zip_code="95815", list_price=329000,
             beds=3, baths=2, sqft=1240, year_built=1958,
             property_type="Single Family", status="Active", days_on_market=64),
     385000, 2350),
    (Listing(id="S2", address="208 Pacific St, Stockton, CA 95204",
             city="Stockton", state="CA", zip_code="95204", list_price=289000,
             beds=4, baths=2, sqft=1560, year_built=1949,
             property_type="Single Family", status="Active", days_on_market=120),
     352000, 2200),
    (Listing(id="S3", address="77 Riverside Dr, Modesto, CA 95351",
             city="Modesto", state="CA", zip_code="95351", list_price=415000,
             beds=3, baths=2, sqft=1410, year_built=1972,
             property_type="Single Family", status="Active", days_on_market=22),
     430000, 2500),
    (Listing(id="S4", address="912 Tennessee St, Vallejo, CA 94590",
             city="Vallejo", state="CA", zip_code="94590", list_price=465000,
             beds=2, baths=1, sqft=980, year_built=1923,
             property_type="Single Family", status="Active", days_on_market=8),
     455000, 2600),
    (Listing(id="S5", address="3551 Oakhill Dr, Antioch, CA 94509",
             city="Antioch", state="CA", zip_code="94509", list_price=520000,
             beds=4, baths=3, sqft=2010, year_built=2004,
             property_type="Single Family", status="Active", days_on_market=41),
     560000, 2900),
    (Listing(id="S6", address="615 38th St, Oakland, CA 94609",
             city="Oakland", state="CA", zip_code="94609", list_price=735000,
             beds=3, baths=2, sqft=1480, year_built=1936,
             property_type="Single Family", status="Active", days_on_market=15),
     742000, 3400),
]

# --- DEMO foreclosures (shown only until the live foreclosure feed is connected) --
# Note the missing beds/baths/sqft — that's realistic for foreclosure/auction data.
_SAMPLE_FC = [
    Listing(id="FC:DEMO1", address="4112 E 131st St, Cleveland, OH 44120",
            city="Cleveland", state="OH", zip_code="44120", list_price=78000,
            property_type="Foreclosure", status="Foreclosure (auction)",
            est_value=110000),
    Listing(id="FC:DEMO2", address="915 Sycamore Dr SE, Atlanta, GA 30315",
            city="Atlanta", state="GA", zip_code="30315", list_price=165000,
            property_type="Foreclosure", status="Bank-owned (REO)",
            est_value=205000),
]


def _sample_rent(price) -> int:
    """A plausible monthly rent placeholder (~0.6% of price), rounded."""
    return int(round((price or 0) * 0.006 / 10) * 10)


def _foreclosure_row(listing: Listing, *, demo: bool) -> dict:
    """Build a view-model row for a bank-owned / foreclosure listing.

    Foreclosure data has no rent and no beds/baths — the deal signal is purely the
    bid vs the lender's estimated value, so the Deal Score uses value only.
    """
    avm = listing.est_value
    val = ValueEstimate(avm=avm,
                        value_low=int(avm * 0.92) if avm else None,
                        value_high=int(avm * 1.08) if avm else None)
    score = deal_score.compute(listing, val, RentEstimate())  # value-only
    return dict(listing=listing, value=val, rent=0, rent_sample=False,
                value_sample=False, score=score, sample=demo, risk=RiskFlags(),
                foreclosure=True, demo_foreclosure=demo)


def attom_second_opinion(row: dict) -> dict:
    """Lazily fetch ATTOM's independent AVM + last sale for ONE opened home and
    re-score with the blended value. Called from the detail view ONLY — never for
    the feed — so we make at most a couple of ATTOM calls when a buyer actually
    opens a property, and only if ATTOM is configured.

    Cost-safe by design:
      * If no ATTOM key, or this is a sample/demo/foreclosure row, do nothing.
      * Cache-first: a repeat view of the same home is a free cache hit.
      * Honors the per-user monthly cap (a fresh call counts; over the cap we fall
        back to cache_only so we never bill past the limit).

    Returns the row augmented with: attom_value, attom_last_sale (both optional),
    and a re-blended score when ATTOM added a second opinion. Safe to call every
    render — it short-circuits on cache hits.
    """
    if not getattr(settings, "has_attom", False):
        return row
    if row.get("sample") or row.get("foreclosure"):
        return row  # sample/demo/foreclosure homes don't get billable ATTOM calls

    listing = row["listing"]
    # Respect the per-user soft cap: over the cap, serve cache only (no new bill).
    # Mirrors how RentCast lookups are gated — same cap, same accounting.
    try:
        used = db.user_lookup_count(settings.current_user_id)
        cache_only = used >= settings.monthly_lookup_cap
    except Exception:
        cache_only = False

    try:
        attom_val = attom_src.get_value_estimate(listing, cache_only=cache_only)
    except Exception:
        attom_val = ValueEstimate()
    try:
        last_sale = attom_src.get_last_sale(listing, cache_only=cache_only)
    except Exception:
        last_sale = None

    row = dict(row)
    if attom_val and attom_val.avm:
        row["attom_value"] = attom_val
        # Re-score with the blended (RentCast + ATTOM) value.
        row["score"] = deal_score.compute(
            listing, row["value"], RentEstimate(monthly_rent=row.get("rent") or None),
            row.get("risk"), attom=attom_val)
    if last_sale:
        row["attom_last_sale"] = last_sale
    return row


def display_rows() -> tuple[list[dict], bool]:
    """Return (rows, is_sample_mode). Each row: listing, value, rent, rent_sample,
    value_sample, score, sample, foreclosure, demo_foreclosure."""
    cached = rentcast.load_cached_listings()
    sample_mode = not cached
    rows: list[dict] = []

    # --- Regular for-sale listings (real cached, or sample if empty) ---
    if sample_mode:
        for listing, avm, rent in _SAMPLE:
            val = ValueEstimate(avm=avm, value_low=int(avm * 0.92),
                                value_high=int(avm * 1.08),
                                comps=[{"x": 1}] * 12)
            score = deal_score.compute(listing, val, RentEstimate(monthly_rent=rent))
            rows.append(dict(listing=listing, value=val, rent=rent, rent_sample=True,
                             value_sample=True, score=score, sample=True, risk=RiskFlags(),
                             foreclosure=False, demo_foreclosure=False))
    else:
        for listing in cached:
            val = rentcast.get_value_estimate(listing, cache_only=True)    # real (cached)
            rent_c = rentcast.get_rent_estimate(listing, cache_only=True)  # usually empty
            risk_f = risk.get_risk(listing, cache_only=True)               # cached FEMA risk
            score = deal_score.compute(listing, val, rent_c, risk_f)       # honest, real
            if rent_c.monthly_rent:
                rent_display, rent_sample = rent_c.monthly_rent, False
            else:
                rent_display, rent_sample = _sample_rent(listing.list_price), True
            value_sample = val.avm is None
            if value_sample:  # very unlikely (we cached value), but keep visuals complete
                val = ValueEstimate(avm=int((listing.list_price or 0) * 1.03))
            rows.append(dict(listing=listing, value=val, rent=rent_display,
                             rent_sample=rent_sample, value_sample=value_sample,
                             score=score, sample=False, risk=risk_f,
                             foreclosure=False, demo_foreclosure=False))

    # --- Foreclosures: real if synced, else clearly-marked DEMO ones ---
    fc_cached = foreclosure.load_cached_listings()
    if fc_cached:
        for listing in fc_cached:
            rows.append(_foreclosure_row(listing, demo=False))
    else:
        for listing in _SAMPLE_FC:
            rows.append(_foreclosure_row(listing, demo=True))

    return rows, sample_mode

"""
Display data for the UI — uses REAL cached listings first; falls back to clearly
marked SAMPLE listings if the cache is empty. Makes ZERO API calls.

For each listing it returns a small view-model: the listing, a value estimate, a
rent figure (and whether that rent is a sample placeholder), and the Deal Score.
The Deal Score for real listings is computed from CACHED estimates only, so it
matches the real numbers; sample rent is shown for design but flagged.
"""

from __future__ import annotations

from src.data_sources import rentcast
from src.models import Listing, RentEstimate, ValueEstimate
from src.scoring import deal_score

# --- Realistic SAMPLE California listings (used only if the cache is empty) ---
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


def _sample_rent(price) -> int:
    """A plausible monthly rent placeholder (~0.6% of price), rounded."""
    return int(round((price or 0) * 0.006 / 10) * 10)


def display_rows() -> tuple[list[dict], bool]:
    """Return (rows, is_sample_mode). Each row: listing, value, rent, rent_sample,
    value_sample, score, sample."""
    cached = rentcast.load_cached_listings()
    sample_mode = not cached
    rows: list[dict] = []

    if sample_mode:
        for listing, avm, rent in _SAMPLE:
            val = ValueEstimate(avm=avm, value_low=int(avm * 0.92),
                                value_high=int(avm * 1.08),
                                comps=[{"x": 1}] * 12)
            score = deal_score.compute(listing, val, RentEstimate(monthly_rent=rent))
            rows.append(dict(listing=listing, value=val, rent=rent, rent_sample=True,
                             value_sample=True, score=score, sample=True))
        return rows, True

    for listing in cached:
        val = rentcast.get_value_estimate(listing, cache_only=True)      # real (cached)
        rent_c = rentcast.get_rent_estimate(listing, cache_only=True)    # usually empty
        score = deal_score.compute(listing, val, rent_c)                 # honest, real
        if rent_c.monthly_rent:
            rent_display, rent_sample = rent_c.monthly_rent, False
        else:
            rent_display, rent_sample = _sample_rent(listing.list_price), True
        value_sample = val.avm is None
        if value_sample:  # very unlikely (we cached value), but keep visuals complete
            val = ValueEstimate(avm=int((listing.list_price or 0) * 1.03))
        rows.append(dict(listing=listing, value=val, rent=rent_display,
                         rent_sample=rent_sample, value_sample=value_sample,
                         score=score, sample=False))
    return rows, False

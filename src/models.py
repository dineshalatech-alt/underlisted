"""
The shape of the data the app passes around.

These are plain "data containers" (dataclasses). They describe what a listing,
a rent estimate, a value estimate, and a finished scored deal look like — so
every module agrees on the same fields. No logic lives here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Listing:
    """A single for-sale home, as returned by RentCast sale listings."""

    id: str                          # RentCast listing id (our cache key)
    address: str
    city: str
    state: str
    zip_code: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    list_price: Optional[float] = None
    beds: Optional[float] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    year_built: Optional[int] = None
    property_type: Optional[str] = None
    status: Optional[str] = None
    days_on_market: Optional[int] = None

    # Foreclosure/REO only: the lender's estimated value (Data Hub / Redfin-
    # derived). Regular RentCast listings leave this None and use the AVM instead.
    est_value: Optional[float] = None

    last_seen_run: Optional[str] = None   # ISO timestamp of last sync
    previous_price: Optional[float] = None  # for price-drop detection

    # --- Listing-agent contact (from RentCast listingAgent / listingOffice) ---
    # RentCast's terms allow showing these to our end users so the BUYER can call
    # or email the listing agent themselves. We never auto-send. All optional:
    # older cached listings (and homes with no agent block) simply leave them None.
    agent_name: Optional[str] = None
    agent_phone: Optional[str] = None
    agent_email: Optional[str] = None
    agent_website: Optional[str] = None
    office_name: Optional[str] = None
    office_phone: Optional[str] = None
    office_email: Optional[str] = None
    office_website: Optional[str] = None
    mls_number: Optional[str] = None       # e.g. for "Ask a local agent · MLS #..."
    mls_name: Optional[str] = None


def listing_contact(listing: "Listing") -> dict:
    """Pick the best contact to show the BUYER, with a graceful fallback chain.

    Order: real listing agent -> brokerage office -> a neutral
    "Ask a local agent" line (optionally with the MLS number). Always returns a
    usable block so the UI never shows an empty/broken contact box.

    Returns a dict: {kind, name, phone, email, website, mls_number}
      kind = "agent" | "office" | "neutral"
    The phone/email/website may be None even for agent/office; the UI shows only
    the buttons it actually has.
    """
    if listing.agent_name or listing.agent_phone or listing.agent_email:
        return {
            "kind": "agent",
            "name": listing.agent_name or "Listing agent",
            "phone": listing.agent_phone,
            "email": listing.agent_email,
            "website": listing.agent_website,
            "mls_number": listing.mls_number,
        }
    if listing.office_name or listing.office_phone or listing.office_email:
        return {
            "kind": "office",
            "name": listing.office_name or "Listing brokerage",
            "phone": listing.office_phone,
            "email": listing.office_email,
            "website": listing.office_website,
            "mls_number": listing.mls_number,
        }
    return {
        "kind": "neutral",
        "name": "Ask a local agent",
        "phone": None,
        "email": None,
        "website": None,
        "mls_number": listing.mls_number,
    }


@dataclass
class RentEstimate:
    monthly_rent: Optional[float] = None
    rent_low: Optional[float] = None
    rent_high: Optional[float] = None
    comps: list = field(default_factory=list)   # raw rent comparables
    source: Optional[str] = None                # e.g. "RentCast" or "HUD Fair Market Rent (area)"
    area: Optional[str] = None                  # set when rent is an area benchmark, not per-home


@dataclass
class ValueEstimate:
    avm: Optional[float] = None          # estimated current value
    value_low: Optional[float] = None
    value_high: Optional[float] = None
    comps: list = field(default_factory=list)   # raw sale comparables


@dataclass
class RiskFlags:
    fire_zone: Optional[str] = None      # e.g. "High", "Moderate", "None", "Unknown"
    flood_zone: Optional[str] = None     # e.g. "AE", "X", "Unknown"
    quake_zone: Optional[str] = None     # earthquake risk rating (FEMA NRI)
    overall_risk: Optional[str] = None   # FEMA NRI overall natural-hazard rating
    insurance_note: Optional[str] = None


@dataclass
class ScoreBreakdown:
    """The 'why it scored X' detail, so the score is transparent."""

    total: int = 0
    value_discount_points: float = 0.0
    rent_yield_points: float = 0.0
    days_on_market_points: float = 0.0
    risk_points: float = 0.0
    notes: list = field(default_factory=list)


@dataclass
class Deal:
    """A listing plus everything we computed about it — the unit the UI shows."""

    listing: Listing
    rent: RentEstimate = field(default_factory=RentEstimate)
    value: ValueEstimate = field(default_factory=ValueEstimate)
    risk: RiskFlags = field(default_factory=RiskFlags)
    score: ScoreBreakdown = field(default_factory=ScoreBreakdown)

    photo_url: Optional[str] = None      # Street View URL (the real photo)

    # --- Simple, objective metrics (computed in scoring/financing) ---
    gross_yield_pct: Optional[float] = None
    meets_one_percent_rule: Optional[bool] = None
    cap_rate_pct: Optional[float] = None
    value_vs_list_pct: Optional[float] = None   # +above / -below estimated value

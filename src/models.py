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

    last_seen_run: Optional[str] = None   # ISO timestamp of last sync
    previous_price: Optional[float] = None  # for price-drop detection


@dataclass
class RentEstimate:
    monthly_rent: Optional[float] = None
    rent_low: Optional[float] = None
    rent_high: Optional[float] = None
    comps: list = field(default_factory=list)   # raw rent comparables


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

"""
The Deal Score (0-100) — the heart of the product.

It answers one question with a single number: how good a deal is this, mostly
based on how far BELOW its estimated value it's listed, plus rent yield, with
days-on-market and (later) risk as secondary signals.

Design rules:
  * Weights and scales are ALL editable in config/scoring_weights.yaml.
  * Fully transparent: returns a per-factor breakdown so the UI can show
    "why it scored X."
  * NO remodel/flip math. NO demographic / "neighborhood quality" inputs —
    only price, estimated value, rent, days-on-market, and risk (Fair Housing).
  * Honest with missing data: if an input isn't cached (e.g. rent not loaded
    yet), that factor is EXCLUDED and the score is rescaled over the factors we
    do have — and the breakdown says so, so the number is never misleading.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from config.settings import settings
from src.models import Listing, RentEstimate, RiskFlags, ValueEstimate


@dataclass
class Factor:
    key: str
    label: str
    detail: str          # plain-language description of the input
    points: float        # points earned
    weight: float        # max points this factor can contribute
    included: bool       # False = no data, excluded from the score


@dataclass
class Score:
    total: int                       # 0-100
    threshold: int                   # "good deal" cutoff
    is_good_deal: bool
    factors: list = field(default_factory=list)

    @property
    def used_factors(self) -> list:
        return [f for f in self.factors if f.included]

    @property
    def missing_factors(self) -> list:
        return [f for f in self.factors if not f.included]


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _scaled(value: float, zero_at: float, full_at: float) -> float:
    """0.0 at `zero_at`, 1.0 at `full_at`, linear in between, clamped."""
    if full_at == zero_at:
        return 0.0
    return _clamp01((value - zero_at) / (full_at - zero_at))


def blended_avm(value: Optional[ValueEstimate],
                attom: Optional[ValueEstimate]) -> tuple[Optional[float], str]:
    """Combine RentCast's AVM with ATTOM's into one trusted value figure.

    Two independent estimates that AGREE are more trustworthy than one, so when
    both are present we use their average. When only one is present we use it;
    when neither is present we return None and the score rescales as before.

    Returns (value, source_label) where source_label is plain English for the UI
    ("average of two estimates" / "one estimate"). This is the SINGLE place the
    blend is decided, so the deal detail and the Deal Score never disagree.
    """
    rc = value.avm if value else None
    at = attom.avm if attom else None
    if rc and at:
        return (rc + at) / 2.0, "average of two independent estimates"
    if rc:
        return rc, "one estimate"
    if at:
        return at, "one estimate"
    return None, "no estimate"


def compute(listing: Listing, value: Optional[ValueEstimate],
            rent: Optional[RentEstimate], risk: Optional[RiskFlags] = None,
            attom: Optional[ValueEstimate] = None) -> Score:
    sc = settings.scoring
    w = sc.get("weights", {})
    s = sc.get("scales", {})
    rp = sc.get("risk_penalty", {})
    threshold = int(sc.get("good_deal_threshold", 70))
    factors: list[Factor] = []

    price = listing.list_price

    # --- 1) Below estimated value (the big one) ---------------------------
    # Use a BLENDED value: when ATTOM's independent AVM is also available we
    # average the two (two estimates that agree are more trustworthy). When
    # ATTOM is absent this is exactly the old RentCast-only behaviour.
    w_vd = float(w.get("value_discount", 50))
    avm, blend_src = blended_avm(value, attom)
    if price and avm:
        vd_pct = (avm - price) / avm * 100  # + = below value (good)
        norm = _scaled(vd_pct,
                       float(s.get("value_discount_zero_points_at_pct", 0)),
                       float(s.get("value_discount_full_points_at_pct", 12)))
        side = "below" if vd_pct >= 0 else "above"
        extra = " · two independent estimates agree" if "average" in blend_src else ""
        factors.append(Factor("value_discount", "Below estimated value",
                              f"Listed {abs(vd_pct):.0f}% {side} estimated value{extra}",
                              w_vd * norm, w_vd, True))
    else:
        factors.append(Factor("value_discount", "Below estimated value",
                              "No value estimate cached", 0.0, w_vd, False))

    # --- 2) Rent yield ----------------------------------------------------
    w_ry = float(w.get("rent_yield", 30))
    monthly_rent = rent.monthly_rent if rent else None
    if price and monthly_rent:
        gy = monthly_rent * 12 / price * 100
        norm = _scaled(gy,
                       float(s.get("rent_yield_zero_points_at_pct", 4)),
                       float(s.get("rent_yield_full_points_at_pct", 9)))
        factors.append(Factor("rent_yield", "Rent yield",
                              f"{gy:.1f}% gross yield (yearly rent ÷ price)",
                              w_ry * norm, w_ry, True))
    else:
        factors.append(Factor("rent_yield", "Rent yield",
                              "Rent not loaded yet — opens with the listing",
                              0.0, w_ry, False))

    # --- 3) Days on market (secondary) ------------------------------------
    w_dom = float(w.get("days_on_market", 12))
    dom = listing.days_on_market
    if dom is not None:
        norm = _scaled(float(dom),
                       float(s.get("days_on_market_zero_points_at", 0)),
                       float(s.get("days_on_market_full_points_at", 90)))
        factors.append(Factor("days_on_market", "Days on market",
                              f"{dom} days listed (longer = more room to negotiate)",
                              w_dom * norm, w_dom, True))
    else:
        factors.append(Factor("days_on_market", "Days on market",
                              "Unknown", 0.0, w_dom, False))

    # --- 4) Risk (secondary; full points until risk data is wired) --------
    w_risk = float(w.get("risk", 8))
    penalty = 0.0
    detail = "No fire/flood data yet — full points for now"
    if risk and (risk.fire_zone or risk.flood_zone):
        fire = (risk.fire_zone or "").lower()
        flood = (risk.flood_zone or "").lower()
        if fire == "high":
            penalty = max(penalty, float(rp.get("high_fire", 1.0)))
        elif fire == "moderate":
            penalty = max(penalty, float(rp.get("moderate_fire", 0.5)))
        if flood in ("ae", "a", "high"):
            penalty = max(penalty, float(rp.get("high_flood", 1.0)))
        elif flood == "moderate":
            penalty = max(penalty, float(rp.get("moderate_flood", 0.5)))
        detail = f"fire: {risk.fire_zone or '—'}, flood: {risk.flood_zone or '—'}"
    factors.append(Factor("risk", "Risk", detail,
                          w_risk * (1 - penalty), w_risk, True))

    # --- Combine: rescale over the factors we actually have ---------------
    used = [f for f in factors if f.included]
    sum_w = sum(f.weight for f in used) or 1.0
    sum_p = sum(f.points for f in used)
    total = int(round(100 * sum_p / sum_w))
    total = max(0, min(100, total))

    return Score(total=total, threshold=threshold,
                 is_good_deal=total >= threshold, factors=factors)

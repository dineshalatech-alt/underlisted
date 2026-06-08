"""
Objective rent & value metrics — the simple, transparent yardsticks.

These are plain arithmetic on numbers we already have (price, estimated rent,
estimated value). No opinions, no protected-class signals — just the math, so
each number can be shown with its formula. The Deal Score (a later phase) builds
on top of these.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.models import Listing, RentEstimate, ValueEstimate


@dataclass
class Metrics:
    gross_yield_pct: Optional[float] = None      # annual rent / price * 100
    meets_one_percent_rule: Optional[bool] = None
    cap_rate_pct: Optional[float] = None         # NOI / price * 100
    value_vs_list_pct: Optional[float] = None    # +above / -below estimated value
    annual_rent: Optional[float] = None
    annual_noi: Optional[float] = None           # rent minus assumed expenses


def _pos(x) -> Optional[float]:
    """Return a positive float or None (guards against zero/None/garbage)."""
    try:
        x = float(x)
        return x if x > 0 else None
    except (TypeError, ValueError):
        return None


def gross_yield_pct(price, monthly_rent) -> Optional[float]:
    price, rent = _pos(price), _pos(monthly_rent)
    if price is None or rent is None:
        return None
    return (rent * 12) / price * 100


def meets_one_percent_rule(price, monthly_rent) -> Optional[bool]:
    """The '1% rule': monthly rent should be at least 1% of the price."""
    price, rent = _pos(price), _pos(monthly_rent)
    if price is None or rent is None:
        return None
    return rent >= 0.01 * price


def cap_rate_pct(price, monthly_rent, operating_expense_pct_of_rent: float) -> Optional[float]:
    """
    Rough cap rate = net operating income / price.
    NOI = annual rent minus an assumed % of rent for expenses (taxes, insurance,
    vacancy, maintenance, management) — the assumption comes from financing.yaml.
    """
    price, rent = _pos(price), _pos(monthly_rent)
    if price is None or rent is None:
        return None
    annual_rent = rent * 12
    noi = annual_rent * (1 - operating_expense_pct_of_rent / 100.0)
    return noi / price * 100


def value_vs_list_pct(list_price, avm) -> Optional[float]:
    """
    How the LIST price compares to the estimated value (AVM), as a percent.
      positive  -> listed ABOVE estimated value (paying a premium)
      negative  -> listed BELOW estimated value (potential deal)
    """
    list_price, avm = _pos(list_price), _pos(avm)
    if list_price is None or avm is None:
        return None
    return (list_price - avm) / avm * 100


def compute(listing: Listing, value: ValueEstimate, rent: RentEstimate,
            financing_cfg: dict) -> Metrics:
    """Build all metrics for one property from its price + cached estimates."""
    price = listing.list_price
    monthly_rent = rent.monthly_rent if rent else None
    expense_pct = float(financing_cfg.get("operating_expense_pct_of_rent", 40))

    annual_rent = (_pos(monthly_rent) * 12) if _pos(monthly_rent) else None
    noi = (annual_rent * (1 - expense_pct / 100.0)) if annual_rent else None

    return Metrics(
        gross_yield_pct=gross_yield_pct(price, monthly_rent),
        meets_one_percent_rule=meets_one_percent_rule(price, monthly_rent),
        cap_rate_pct=cap_rate_pct(price, monthly_rent, expense_pct),
        value_vs_list_pct=value_vs_list_pct(price, value.avm if value else None),
        annual_rent=annual_rent,
        annual_noi=noi,
    )

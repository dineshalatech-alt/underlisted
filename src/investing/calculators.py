"""
Investor tools — the free "run the numbers" calculators.

PURE arithmetic. NO RentCast, NO billable API calls. Everything runs on the
numbers the user types plus our existing cost engine (afford.monthly_costs +
financing.cash_needed) and config/investing.yaml.

Two beginner-friendly calculators:

  1) rental()  — Buy & hold. Given a price and the monthly rent, what's the
     monthly cash flow, the cap rate, and the cash-on-cash return? Plus the
     quick "1% rule" sanity check.

  2) flip()    — Fix & flip. Given the purchase price, repair budget and the
     after-repair value (ARV), what's the projected profit and ROI, and does
     the deal pass the classic "70% rule"?

Design rules (same as afford.py):
  * Costs that vary (tax, insurance, HOA, upkeep) come from
    afford.monthly_costs so the two tools never disagree. They arrive as
    low–high RANGES, so cash flow / returns are honest ranges too.
  * We judge the verdict against the MIDPOINT — never rosy, never scary.
  * Nothing here logs, prints or stores the user's numbers.
  * All assumptions live in config/investing.yaml (no magic numbers).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from config.settings import settings
from src.affordability.afford import Range, monthly_costs

# Cost items from afford.monthly_costs that are real operating expenses for a
# landlord (PMI and the loan payment are handled separately).
_OPERATING_KEYS = ("tax", "insurance", "hoa", "maintenance")


# ---------------------------------------------------------------------------
# 1) Buy & hold — rental cash flow
# ---------------------------------------------------------------------------
@dataclass
class RentalResult:
    monthly_rent: float
    monthly_pi: float            # loan principal + interest (a point)
    operating: Range             # monthly operating costs incl. vacancy + mgmt
    cash_flow: Range             # monthly money in your pocket after everything
    noi_annual: Range            # net operating income (before the mortgage)
    cap_rate: Range              # NOI / price, %
    cash_invested: float         # down payment + closing costs
    cash_on_cash: Range          # yearly cash flow / cash invested, %
    one_pct_rule: bool           # rent >= 1% of price?
    band: str                    # "green" | "amber" | "red"
    headline: str
    reasons: list = field(default_factory=list)


def rental(price: float, monthly_rent: float, *,
           credit_band: str = "740+", hoa_monthly: Optional[float] = None,
           risk=None) -> RentalResult:
    """Buy-and-hold cash flow for THIS home. NO API calls.

    Reuses afford.monthly_costs(occupancy="investment") for the operating
    costs and the loan payment, then layers on the landlord-only costs
    (vacancy + management) from config/investing.yaml.
    """
    price = float(price or 0)
    rent = float(monthly_rent or 0)
    cfg = settings.investing.get("rental", {})
    vacancy_pct = float(cfg.get("vacancy_pct", 5))
    mgmt_pct = float(cfg.get("management_pct", 8))
    healthy = float(cfg.get("healthy_monthly_cashflow", 100))

    mc = monthly_costs(price, occupancy="investment", credit_band=credit_band,
                       hoa_monthly=hoa_monthly, risk=risk)

    # Operating costs that vary -> sum their ranges.
    op_lo = op_hi = 0.0
    for it in mc.items:
        if it.key in _OPERATING_KEYS:
            op_lo += it.monthly.low
            op_hi += it.monthly.high
    # Landlord-only costs scale with rent and are the same at both ends.
    vacancy = rent * vacancy_pct / 100
    management = rent * mgmt_pct / 100
    operating = Range(op_lo + vacancy + management, op_hi + vacancy + management)

    # Net operating income = rent minus operating costs (the mortgage is NOT
    # part of NOI). Higher operating costs -> lower NOI, so the ends flip.
    noi_lo = rent - operating.high
    noi_hi = rent - operating.low
    noi_annual = Range(noi_lo * 12, noi_hi * 12)

    pi = mc.principal_interest
    cash_flow = Range(noi_lo - pi, noi_hi - pi)

    cap_rate = (Range(noi_annual.low / price * 100, noi_annual.high / price * 100)
                if price > 0 else Range(0, 0))

    cash_invested = getattr(mc.cash_needed, "cash_to_close", 0.0)
    cash_on_cash = (Range(cash_flow.low * 12 / cash_invested * 100,
                          cash_flow.high * 12 / cash_invested * 100)
                    if cash_invested > 0 else Range(0, 0))

    one_pct = rent >= price * 0.01 if price > 0 else False

    reasons: list[str] = []
    mid = cash_flow.mid
    if mid >= healthy:
        band, headline = "green", "Positive cash flow."
        reasons.append(f"After every cost, this home would put roughly "
                       f"${cash_flow.low:,.0f}–${cash_flow.high:,.0f} in your pocket "
                       "each month.")
    elif mid >= 0:
        band, headline = "amber", "About breaks even."
        reasons.append(f"Cash flow lands near zero (about "
                       f"${cash_flow.low:,.0f}–${cash_flow.high:,.0f}/mo). Thin margin — "
                       "one repair or empty month can tip it negative.")
    else:
        band, headline = "red", "Loses money each month."
        reasons.append(f"The rent doesn't cover the costs — about "
                       f"${cash_flow.low:,.0f}–${cash_flow.high:,.0f}/mo. You'd pay to "
                       "hold it.")

    reasons.append(f"Cash-on-cash return: about {cash_on_cash.low:.1f}–"
                   f"{cash_on_cash.high:.1f}% a year on the "
                   f"${cash_invested:,.0f} cash you'd put in.")
    reasons.append(("Passes the quick 1% rule (rent ≥ 1% of price)."
                    if one_pct else
                    "Below the 1% rule of thumb (rent under 1% of price) — common in "
                    "pricier areas, but watch the cash flow."))

    return RentalResult(
        monthly_rent=rent, monthly_pi=pi, operating=operating, cash_flow=cash_flow,
        noi_annual=noi_annual, cap_rate=cap_rate, cash_invested=cash_invested,
        cash_on_cash=cash_on_cash, one_pct_rule=one_pct, band=band,
        headline=headline, reasons=reasons)


# ---------------------------------------------------------------------------
# 2) Fix & flip — profit + the 70% rule
# ---------------------------------------------------------------------------
@dataclass
class FlipResult:
    arv: float                   # after-repair value (what it's worth fixed up)
    purchase: float
    repairs: float
    hold_months: int
    max_offer: float             # the 70% rule ceiling
    selling_costs: float         # agent + closing when you sell
    holding_costs: float         # taxes/insurance/etc while you hold
    profit: float                # bottom-line projected profit
    cash_in: float               # purchase + repairs + holding
    roi_pct: float               # profit / cash_in, %
    margin_pct: float            # profit / ARV, %
    within_rule: bool            # is the purchase at/under the 70% ceiling?
    band: str                    # "green" | "amber" | "red"
    headline: str
    reasons: list = field(default_factory=list)


def flip(arv: float, purchase: float, repairs: float, *,
         hold_months: Optional[int] = None) -> FlipResult:
    """Fix-&-flip math for one deal. NO API calls.

    The "70% rule": don't pay more than 70% of the after-repair value minus
    the repair budget. Profit = ARV − purchase − repairs − holding − selling.
    """
    arv = float(arv or 0)
    purchase = float(purchase or 0)
    repairs = float(repairs or 0)
    cfg = settings.investing.get("flip", {})
    rule_pct = float(cfg.get("rule_of_thumb_pct", 70))
    selling_pct = float(cfg.get("selling_costs_pct", 8))
    holding_annual_pct = float(cfg.get("holding_costs_annual_pct", 6))
    months = int(hold_months if hold_months is not None
                 else cfg.get("default_hold_months", 5))

    max_offer = arv * rule_pct / 100 - repairs
    selling_costs = arv * selling_pct / 100
    holding_costs = purchase * holding_annual_pct / 100 / 12 * months
    profit = arv - purchase - repairs - holding_costs - selling_costs

    cash_in = purchase + repairs + holding_costs
    roi_pct = profit / cash_in * 100 if cash_in > 0 else 0.0
    margin_pct = profit / arv * 100 if arv > 0 else 0.0
    within_rule = purchase <= max_offer

    reasons: list[str] = []
    if profit <= 0:
        band, headline = "red", "Projected to lose money."
        reasons.append(f"After repairs, holding and selling costs, you'd be down "
                       f"about ${abs(profit):,.0f}.")
    elif within_rule:
        band, headline = "green", "Passes the 70% rule with a profit."
        reasons.append(f"Projected profit: about ${profit:,.0f} "
                       f"({roi_pct:.0f}% on the ${cash_in:,.0f} you'd put in).")
    else:
        band, headline = "amber", "Profitable, but you're paying over the 70% rule."
        reasons.append(f"Projected profit: about ${profit:,.0f}, but you'd be paying "
                       f"${purchase - max_offer:,.0f} over the safe ceiling — thinner "
                       "cushion if anything goes wrong.")

    reasons.append(f"70% rule says don't pay more than about ${max_offer:,.0f} "
                   f"(70% of the ${arv:,.0f} after-repair value, minus "
                   f"${repairs:,.0f} repairs).")
    reasons.append(f"Includes ~${selling_costs:,.0f} to sell and ~${holding_costs:,.0f} "
                   f"to hold it for {months} months.")

    return FlipResult(
        arv=arv, purchase=purchase, repairs=repairs, hold_months=months,
        max_offer=max_offer, selling_costs=selling_costs, holding_costs=holding_costs,
        profit=profit, cash_in=cash_in, roi_pct=roi_pct, margin_pct=margin_pct,
        within_rule=within_rule, band=band, headline=headline, reasons=reasons)

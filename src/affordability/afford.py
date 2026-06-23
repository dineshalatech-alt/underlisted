"""
"Can I Afford It?" — the affordability moat.

PURE arithmetic. NO RentCast, NO billable API calls — it runs entirely on the
list price, our existing config, and the FEMA risk flags we already cache.

Two jobs:
  1) monthly_costs()  — the TRUE monthly cost of owning THIS home, broken into
     the surprise costs first-time buyers forget (tax, insurance, PMI, HOA),
     each shown as an honest labelled RANGE (low–high), never false precision.
  2) verdict()        — given the buyer's income / cash / debts, a plain
     green / amber / red answer plus "you'd have about $X left each month."

Design rules:
  * Every estimate is a RANGE. We expose .low / .mid / .high and let the UI
    decide what to show. The verdict uses the MIDPOINT so it's neither rosy
    nor scary.
  * Insurance HIGH end is bumped when FEMA flags real fire/flood risk — that's
    how our insurance-risk moat shows up in real dollars.
  * Personal inputs (income/cash/debts) are arguments only. Nothing here logs,
    prints, or stores them — that's the caller's contract too.
  * All assumptions live in config/affordability.yaml (no magic numbers).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from config.settings import settings
from src.financing import cash_needed


@dataclass
class Range:
    """A low–high estimate. mid is the honest middle we judge against."""

    low: float
    high: float

    @property
    def mid(self) -> float:
        return (self.low + self.high) / 2


@dataclass
class CostItem:
    key: str
    label: str
    monthly: Range
    note: str = ""           # plain-language "why" / caveat
    counts_in_payment: bool = True   # is it part of the lender-payment math?


@dataclass
class MonthlyCosts:
    """The true monthly cost of owning this home, as labelled ranges."""

    principal_interest: float            # fixed P&I from cash_needed (a point, not a range)
    items: list = field(default_factory=list)   # the surprise-cost CostItems
    cash_needed: object = None           # the underlying CashNeeded (down/closing/etc.)

    def _sum(self, counts_only: bool) -> Range:
        lo = hi = self.principal_interest
        for it in self.items:
            if counts_only and not it.counts_in_payment:
                continue
            lo += it.monthly.low
            hi += it.monthly.high
        return Range(lo, hi)

    @property
    def housing_payment(self) -> Range:
        """PITI + PMI + HOA — what a lender counts (the 'house payment')."""
        return self._sum(counts_only=True)

    @property
    def all_in(self) -> Range:
        """Everything including maintenance — the real cost of living here."""
        return self._sum(counts_only=False)


@dataclass
class CreditImpact:
    """What the buyer's credit score means for THIS home, in real dollars.

    All figures isolate the RATE effect of the score: we hold the loan amount
    fixed and only vary the interest rate by credit band, so the message is a
    clean 'your score costs/saves you $X a month'. Pure math, 0 API calls.
    """

    current_band: str
    current_rate: float
    current_payment: float            # P&I at the buyer's band
    is_best: bool                     # already in the top (740+) band?
    best_band: str
    best_rate: float
    best_payment: float
    monthly_saving_to_best: float     # >= 0; what top credit would save vs now
    next_band: Optional[str]          # the next band UP (better), or None if best
    next_rate: Optional[float]
    next_payment: Optional[float]
    monthly_saving_to_next: float     # >= 0; saving from a one-band improvement
    lifetime_saving_to_next: float    # that monthly saving over the full loan term


def credit_impact(price: float, *, occupancy: str = "live_in",
                  loan_type: str = "conventional",
                  credit_band: str = "740+") -> CreditImpact:
    """Translate a credit-score band into 'here's what it costs / could save you'.

    We compute the monthly principal+interest on the SAME loan at three rates:
    the buyer's band, the top band (740+), and the next band up. Isolating the
    rate keeps the story honest and simple ('improve one band, save $X/mo').
    No RentCast, no billable calls.
    """
    bands = cash_needed.CREDIT_BANDS
    bumps = settings.financing.get("rate_bumps_by_credit", {})
    term = int(settings.financing.get("loan_term_years", 30))

    cn = cash_needed.compute(price, occupancy=occupancy, loan_type=loan_type,
                             credit_band=credit_band)
    loan = cn.loan_amount
    cur_rate = cn.interest_rate
    cur_pay = cn.monthly_payment
    # Back out the occupancy base rate (the bump for this band is baked into cur_rate).
    base_rate = cur_rate - float(bumps.get(credit_band, 0))

    def rate_for(b: str) -> float:
        return base_rate + float(bumps.get(b, 0))

    def pay_for(b: str) -> float:
        return cash_needed._pmt(loan, rate_for(b), term)

    best_band = bands[0]
    best_rate = rate_for(best_band)
    best_pay = pay_for(best_band)

    idx = bands.index(credit_band) if credit_band in bands else 0
    is_best = idx == 0
    next_band = bands[idx - 1] if idx > 0 else None
    next_rate = rate_for(next_band) if next_band else None
    next_pay = pay_for(next_band) if next_band else None

    saving_best = max(0.0, cur_pay - best_pay)
    saving_next = max(0.0, cur_pay - next_pay) if next_pay is not None else 0.0

    return CreditImpact(
        current_band=credit_band, current_rate=cur_rate, current_payment=cur_pay,
        is_best=is_best, best_band=best_band, best_rate=best_rate, best_payment=best_pay,
        monthly_saving_to_best=saving_best,
        next_band=next_band, next_rate=next_rate, next_payment=next_pay,
        monthly_saving_to_next=saving_next,
        lifetime_saving_to_next=saving_next * term * 12,
    )


@dataclass
class Verdict:
    band: str                 # "green" | "amber" | "red"
    headline: str             # plain one-liner
    leftover: Range           # money left each month after housing + debts
    front_dti: Range          # housing payment as % of gross income
    total_dti: Range          # housing + other debts as % of gross income
    cash_ok: Optional[bool]   # do they have enough cash to close? (None if unknown)
    cash_gap: float           # how much cash short (0 if fine / unknown)
    reasons: list = field(default_factory=list)


def _rng(cfg: dict, lo_key: str = "low", hi_key: str = "high") -> tuple[float, float]:
    return float(cfg.get(lo_key, 0)), float(cfg.get(hi_key, 0))


def _fire_flood_bump(risk) -> tuple[float, list[str]]:
    """Extra insurance % (added to both ends) from FEMA fire/flood flags."""
    a = settings.affordability.get("insurance_risk_bump_pct", {})
    bump = 0.0
    notes: list[str] = []
    if risk is not None:
        fire = (getattr(risk, "fire_zone", "") or "").lower()
        flood = (getattr(risk, "flood_zone", "") or "").lower()
        if fire == "high":
            bump += float(a.get("high_fire", 0))
            notes.append("high wildfire risk")
        elif fire == "moderate":
            bump += float(a.get("moderate_fire", 0))
            notes.append("some wildfire risk")
        # flood_zone is normalised to "High" by risk.py for FEMA SFHA zones
        if flood in ("high", "ae", "a", "ve", "v"):
            bump += float(a.get("high_flood", 0))
            notes.append("a FEMA flood zone")
    return bump, notes


def monthly_costs(price: float, *, occupancy: str = "live_in",
                  loan_type: str = "conventional", credit_band: str = "740+",
                  risk=None, hoa_monthly: Optional[float] = None) -> MonthlyCosts:
    """
    The true monthly cost of THIS home as labelled ranges. NO API calls.

    `risk` is an optional RiskFlags (already cached, free) — when it flags
    fire/flood we widen the insurance estimate so the cost is honest.
    `hoa_monthly` overrides the default HOA range when the buyer knows it.
    """
    price = float(price or 0)
    cfg = settings.affordability
    cn = cash_needed.compute(price, occupancy=occupancy, loan_type=loan_type,
                             credit_band=credit_band)

    items: list[CostItem] = []

    # --- Property tax (yearly % of price -> monthly) ---
    t_lo, t_hi = _rng(cfg.get("property_tax_pct", {}))
    items.append(CostItem(
        "tax", "Property tax",
        Range(price * t_lo / 100 / 12, price * t_hi / 100 / 12),
        note="Varies a lot by county. Check the exact rate for this address."))

    # --- Homeowners insurance (yearly % of price -> monthly), risk-bumped ---
    i_lo, i_hi = _rng(cfg.get("home_insurance_pct", {}))
    bump, risk_notes = _fire_flood_bump(risk)
    ins_note = "Typical homeowners policy."
    if bump:
        ins_note = ("Higher because this home is in " + " and ".join(risk_notes)
                    + " — insurance here costs more, or can be hard to get.")
    items.append(CostItem(
        "insurance", "Home insurance",
        Range(price * i_lo / 100 / 12, price * (i_hi + bump) / 100 / 12),
        note=ins_note))

    # --- PMI (only when down payment < threshold) ---
    pmi_thresh = float(cfg.get("pmi_required_below_down_pct", 20))
    if cn.down_payment_pct < pmi_thresh:
        p_lo, p_hi = _rng(cfg.get("pmi_pct", {}))
        items.append(CostItem(
            "pmi", "Mortgage insurance (PMI)",
            Range(cn.loan_amount * p_lo / 100 / 12,
                  cn.loan_amount * p_hi / 100 / 12),
            note=(f"You put {cn.down_payment_pct:.0f}% down (under {pmi_thresh:.0f}%), "
                  "so lenders add this. It usually drops off once you reach 20% equity.")))

    # --- HOA (flat monthly range, or the buyer's known number) ---
    if hoa_monthly is not None:
        items.append(CostItem(
            "hoa", "HOA dues", Range(float(hoa_monthly), float(hoa_monthly)),
            note="The amount you entered for this home."))
    else:
        h_lo, h_hi = _rng(cfg.get("hoa_monthly", {}))
        items.append(CostItem(
            "hoa", "HOA dues", Range(h_lo, h_hi),
            note="Condos/planned communities charge this; many houses charge $0. "
                 "Check the listing."))

    # --- Maintenance (real, but NOT part of the lender payment) ---
    m_lo, m_hi = _rng(cfg.get("maintenance_pct", {}))
    items.append(CostItem(
        "maintenance", "Upkeep & repairs",
        Range(price * m_lo / 100 / 12, price * m_hi / 100 / 12),
        note="Roof, water heater, the surprises. Budget for it even though no "
             "lender bills you.", counts_in_payment=False))

    return MonthlyCosts(principal_interest=cn.monthly_payment, items=items,
                        cash_needed=cn)


def verdict(price: float, *, gross_monthly_income: float,
            cash_available: Optional[float] = None,
            monthly_debts: float = 0.0, occupancy: str = "live_in",
            loan_type: str = "conventional", credit_band: str = "740+",
            risk=None, hoa_monthly: Optional[float] = None) -> Verdict:
    """
    Plain green / amber / red answer for THIS buyer + THIS home. NO API calls.

    We judge against the MIDPOINT of the monthly housing range (PITI + PMI +
    HOA) so the verdict is neither rosy nor scary, using standard lender DTI
    guidance from config. We also surface money left over and any cash-to-close
    gap. None of these inputs are stored or logged here.
    """
    mc = monthly_costs(price, occupancy=occupancy, loan_type=loan_type,
                       credit_band=credit_band, risk=risk, hoa_monthly=hoa_monthly)
    v = settings.affordability.get("verdict", {})
    comf_front = float(v.get("comfortable_front_dti_pct", 28))
    str_front = float(v.get("stretch_front_dti_pct", 36))
    comf_total = float(v.get("comfortable_total_dti_pct", 36))
    str_total = float(v.get("stretch_total_dti_pct", 43))

    income = float(gross_monthly_income or 0)
    debts = float(monthly_debts or 0)
    house = mc.housing_payment  # a Range

    def dti(amount_lo, amount_hi) -> Range:
        if income <= 0:
            return Range(0.0, 0.0)
        return Range(amount_lo / income * 100, amount_hi / income * 100)

    front = dti(house.low, house.high)
    total = dti(house.low + debts, house.high + debts)

    # Money left each month after the housing payment AND their other debts.
    leftover = Range(income - house.high - debts, income - house.low - debts)

    reasons: list[str] = []
    if income <= 0:
        band = "amber"
        headline = "Enter your monthly income to see if this home fits your budget."
        return Verdict(band, headline, leftover, front, total, None, 0.0,
                       ["No income entered yet."])

    # Verdict from the MIDPOINT of front- and total-DTI; worst of the two wins.
    fm, tm = front.mid, total.mid

    def band_for(value, comf, stretch) -> str:
        if value <= comf:
            return "green"
        if value <= stretch:
            return "amber"
        return "red"

    bands = [band_for(fm, comf_front, str_front),
             band_for(tm, comf_total, str_total)]
    order = {"green": 0, "amber": 1, "red": 2}
    band = max(bands, key=lambda b: order[b])

    # Cash-to-close check (if they told us their cash).
    cash_ok: Optional[bool] = None
    cash_gap = 0.0
    need = getattr(mc.cash_needed, "total", 0.0)
    if cash_available is not None:
        cash_ok = float(cash_available) >= need
        if not cash_ok:
            cash_gap = need - float(cash_available)
            # Not enough cash to close is a hard blocker -> at least amber.
            if band == "green":
                band = "amber"
            reasons.append(f"You're about ${cash_gap:,.0f} short on the cash needed "
                           "to close.")
        else:
            reasons.append("You have enough cash to cover the down payment, closing "
                           "costs, and reserves.")

    # Plain headline + reason.
    # Floor BOTH ends at $0: a deeply over-budget buyer can have a negative
    # high end too, and "$0–$-2,240 left" reads as broken/dishonest math.
    left_lo = max(0.0, leftover.low)
    left_hi = max(0.0, leftover.high)

    def _left_phrase() -> str:
        """'$X–$Y left' — collapses to a single '$0' when nothing is left over."""
        if left_hi <= 0:
            return "$0 left each month"
        return f"${left_lo:,.0f}–${left_hi:,.0f} left each month"

    if band == "green":
        headline = "Looks affordable for you."
        reasons.insert(0, "After the house payment and your other debts, you'd have "
                       f"roughly {_left_phrase()}.")
    elif band == "amber":
        headline = "A stretch — doable, but tight."
        reasons.insert(0, f"The payment runs about {front.mid:.0f}% of your income "
                       f"(comfortable is under {comf_front:.0f}%). You'd have around "
                       f"{_left_phrase()}.")
    else:
        headline = "Over budget — this one's a stretch too far."
        reasons.insert(0, f"The payment is about {front.mid:.0f}% of your income, above "
                       f"the {str_front:.0f}% lenders usually allow. You'd have only "
                       f"around {_left_phrase()}.")

    if debts > 0:
        reasons.append(f"Your other monthly debts (${debts:,.0f}) push your total up to "
                       f"about {total.mid:.0f}% of income.")

    return Verdict(band, headline, leftover, front, total, cash_ok, cash_gap, reasons)

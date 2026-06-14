"""
"How much cash you really need" — beginner-first money math.

Pure arithmetic from the list price + config/financing.yaml. NO API calls.
Leads with ONE plain number (total cash needed), then a friendly breakdown:
money that LEAVES your account (down payment + closing costs = cash to close) and
money you KEEP (reserves). All figures are ESTIMATES — not a loan offer.
"""

from __future__ import annotations

from dataclasses import dataclass

from config.settings import settings
from src.data_sources import mortgage_rates

CREDIT_BANDS = ["740+", "680-739", "620-679", "580-619", "<580"]


@dataclass
class CashNeeded:
    total: float                 # the big headline number
    down_payment: float
    down_payment_pct: float
    closing_low: float
    closing_high: float
    closing_mid: float
    cash_to_close: float
    reserves: float
    reserves_months: int
    monthly_payment: float       # principal + interest (PITI is higher)
    interest_rate: float
    loan_amount: float


def _pmt(principal: float, annual_rate_pct: float, years: int) -> float:
    """Standard monthly principal+interest payment."""
    r = annual_rate_pct / 100 / 12
    n = years * 12
    if r == 0:
        return principal / n
    return principal * r / (1 - (1 + r) ** (-n))


def compute(price: float, *, occupancy: str = "live_in",
            loan_type: str = "conventional", credit_band: str = "740+") -> CashNeeded:
    """
    occupancy: 'live_in' | 'investment'
    loan_type (live-in only): 'conventional' | 'fha' | 'va'
    credit_band: one of CREDIT_BANDS
    """
    f = settings.financing
    dp_cfg = f.get("down_payment_pct", {})
    rates = f.get("interest_rates", {})
    bumps = f.get("rate_bumps_by_credit", {})
    closing = f.get("closing_costs_pct", {})
    reserves_cfg = f.get("reserves_months", {})
    term = int(f.get("loan_term_years", 30))

    # Base rates: start from the typed config, then overlay the LIVE 30-yr rate if
    # the worker has fetched it (Freddie Mac / FRED). Reading the cached rate does
    # NO network call, so this stays safe on page load. The investment premium
    # (the gap the owner set between the two rates) is preserved on top of live.
    cfg_primary = float(rates.get("primary_residence", 6.6))
    cfg_investment = float(rates.get("investment", 7.3))
    live30 = mortgage_rates.current_30yr_rate()
    if live30:
        premium = cfg_investment - cfg_primary
        cfg_primary, cfg_investment = live30, live30 + premium

    # Down payment % + base rate by occupancy/loan type.
    if occupancy == "investment":
        dp_pct = float(dp_cfg.get("investment", {}).get("default", 20))
        base_rate = cfg_investment
        months = int(reserves_cfg.get("investment", 6))
    else:
        live = dp_cfg.get("live_in", {})
        if loan_type == "fha":
            dp_pct = float(live.get("fha_low_credit", 10) if credit_band == "<580"
                           else live.get("fha", 3.5))
        elif loan_type == "va":
            dp_pct = float(live.get("va", 0))
        else:
            dp_pct = float(live.get("conventional", 3))
        base_rate = cfg_primary
        months = int(reserves_cfg.get("live_in", 0))

    rate = base_rate + float(bumps.get(credit_band, 0))

    down = price * dp_pct / 100
    loan = price - down
    closing_low = price * float(closing.get("low", 2)) / 100
    closing_high = price * float(closing.get("high", 5)) / 100
    closing_mid = (closing_low + closing_high) / 2
    monthly = _pmt(loan, rate, term)
    reserves = months * monthly
    cash_to_close = down + closing_mid
    total = cash_to_close + reserves

    return CashNeeded(
        total=total, down_payment=down, down_payment_pct=dp_pct,
        closing_low=closing_low, closing_high=closing_high, closing_mid=closing_mid,
        cash_to_close=cash_to_close, reserves=reserves, reserves_months=months,
        monthly_payment=monthly, interest_rate=rate, loan_amount=loan,
    )

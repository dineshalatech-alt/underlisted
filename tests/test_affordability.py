"""
Tests for the affordability moat (src/affordability/afford.py).

These are PURE-logic tests — no API calls, no network. They lock in the
behaviour first-time buyers depend on: honest ranges, a sane green/amber/red
verdict, the cash-to-close gate, and the FEMA insurance-risk bump.

Run from the project root:
    .venv/Scripts/python.exe -m pytest tests/test_affordability.py -q
or without pytest:
    .venv/Scripts/python.exe tests/test_affordability.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.affordability import afford  # noqa: E402


class _Risk:
    """Stand-in for RiskFlags with just the fields afford.py reads."""

    def __init__(self, fire_zone=None, flood_zone=None):
        self.fire_zone = fire_zone
        self.flood_zone = flood_zone


def test_ranges_are_low_to_high_never_false_precision():
    mc = afford.monthly_costs(400_000)
    for it in mc.items:
        assert it.monthly.low <= it.monthly.high, f"{it.key} range is inverted"
    hp = mc.housing_payment
    assert hp.low <= hp.high
    # mid sits between the two ends
    assert hp.low <= hp.mid <= hp.high


def test_principal_interest_is_in_the_payment():
    mc = afford.monthly_costs(400_000)
    assert mc.principal_interest > 0
    # housing payment must be at least the loan payment plus some tax/insurance
    assert mc.housing_payment.low >= mc.principal_interest


def test_pmi_only_when_down_under_20pct():
    # 3% conventional -> PMI present
    low_down = afford.monthly_costs(400_000, loan_type="conventional",
                                    credit_band="740+")
    assert any(it.key == "pmi" for it in low_down.items)
    # 20% investment -> no PMI
    inv = afford.monthly_costs(400_000, occupancy="investment")
    assert not any(it.key == "pmi" for it in inv.items)


def test_flood_zone_raises_insurance_high_end():
    base = afford.monthly_costs(400_000, risk=_Risk())
    flooded = afford.monthly_costs(400_000, risk=_Risk(flood_zone="High"))
    base_ins = next(i for i in base.items if i.key == "insurance").monthly.high
    flood_ins = next(i for i in flooded.items if i.key == "insurance").monthly.high
    assert flood_ins > base_ins, "FEMA flood flag should raise insurance estimate"


def test_high_fire_raises_insurance_and_notes_it():
    fire = afford.monthly_costs(400_000, risk=_Risk(fire_zone="High"))
    ins = next(i for i in fire.items if i.key == "insurance")
    assert "wildfire" in ins.note.lower()


def test_verdict_green_for_affordable_buyer():
    # Cheap home, high income -> comfortably green
    v = afford.verdict(150_000, gross_monthly_income=12_000, cash_available=200_000)
    assert v.band == "green"
    assert v.leftover.high > 0


def test_verdict_red_for_overstretched_buyer():
    # Expensive home, low income -> red
    v = afford.verdict(900_000, gross_monthly_income=3_500)
    assert v.band == "red"


def test_cash_gap_blocks_green():
    # Could afford the payment, but nowhere near enough cash to close.
    v = afford.verdict(400_000, gross_monthly_income=20_000, cash_available=1_000)
    assert v.cash_ok is False
    assert v.cash_gap > 0
    assert v.band in ("amber", "red")  # cash gap must downgrade from green


def test_no_income_returns_amber_prompt():
    v = afford.verdict(400_000, gross_monthly_income=0)
    assert v.band == "amber"
    assert v.cash_ok is None


def test_debts_lower_the_leftover():
    no_debt = afford.verdict(300_000, gross_monthly_income=8_000, monthly_debts=0)
    with_debt = afford.verdict(300_000, gross_monthly_income=8_000, monthly_debts=1_500)
    assert with_debt.leftover.high < no_debt.leftover.high


def test_credit_impact_top_band_is_best_and_saves_nothing():
    ci = afford.credit_impact(400_000, credit_band="740+")
    assert ci.is_best is True
    assert ci.monthly_saving_to_best == 0.0
    assert ci.next_band is None
    assert ci.monthly_saving_to_next == 0.0


def test_credit_impact_weaker_band_costs_more_per_month():
    ci = afford.credit_impact(400_000, credit_band="620-679")
    assert ci.is_best is False
    # A weaker score must pay a higher rate -> a positive saving vs top credit.
    assert ci.current_rate > ci.best_rate
    assert ci.monthly_saving_to_best > 0
    assert ci.current_payment > ci.best_payment


def test_credit_impact_next_band_up_is_better_and_bounded_by_best():
    ci = afford.credit_impact(400_000, credit_band="620-679")
    assert ci.next_band == "680-739"          # one band up from 620-679
    assert ci.next_rate is not None and ci.next_rate < ci.current_rate
    # A one-band improvement can't save more than reaching top credit.
    assert 0 < ci.monthly_saving_to_next <= ci.monthly_saving_to_best + 1e-6
    # Lifetime saving = the monthly saving across every payment of the term.
    assert ci.lifetime_saving_to_next > ci.monthly_saving_to_next


def test_credit_impact_payment_matches_cash_needed_engine():
    # The 'current payment' must agree with the real cash_needed math (same loan).
    from src.financing import cash_needed
    cn = cash_needed.compute(350_000, credit_band="580-619")
    ci = afford.credit_impact(350_000, credit_band="580-619")
    assert abs(ci.current_payment - cn.monthly_payment) < 0.01
    assert abs(ci.current_rate - cn.interest_rate) < 1e-9


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        fn()
        passed += 1
        print(f"  ok  {fn.__name__}")
    print(f"\n{passed}/{len(fns)} affordability tests passed.")


if __name__ == "__main__":
    _run_all()

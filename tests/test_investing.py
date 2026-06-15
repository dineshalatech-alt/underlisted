"""
Tests for the free Investor Tools (src/investing/calculators.py).

PURE-logic tests — no API calls, no network. They lock in the math beginner
investors will trust: honest ranges, a sane green/amber/red verdict, the 1%
rule, and the fix-&-flip 70% rule.

Run from the project root:
    .venv/Scripts/python.exe -m pytest tests/test_investing.py -q
or without pytest:
    .venv/Scripts/python.exe tests/test_investing.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.investing import calculators as calc  # noqa: E402


# --- Rental (buy & hold) ---------------------------------------------------
def test_rental_ranges_are_low_to_high():
    r = calc.rental(300_000, 2_500)
    assert r.operating.low <= r.operating.high
    assert r.cash_flow.low <= r.cash_flow.high
    assert r.cap_rate.low <= r.cap_rate.high
    assert r.cash_on_cash.low <= r.cash_on_cash.high


def test_rental_high_rent_is_green_cash_flow():
    # Cheap home, strong rent -> clearly positive cash flow.
    r = calc.rental(150_000, 2_200)
    assert r.band == "green"
    assert r.cash_flow.mid > 0


def test_rental_low_rent_loses_money():
    # Expensive home, weak rent -> negative cash flow.
    r = calc.rental(800_000, 1_500)
    assert r.band == "red"
    assert r.cash_flow.mid < 0


def test_rental_one_percent_rule():
    assert calc.rental(200_000, 2_000).one_pct_rule is True   # exactly 1%
    assert calc.rental(200_000, 1_500).one_pct_rule is False  # under 1%


def test_rental_more_rent_means_more_cash_flow():
    low = calc.rental(300_000, 2_000)
    high = calc.rental(300_000, 3_000)
    assert high.cash_flow.mid > low.cash_flow.mid


def test_rental_cash_invested_is_positive():
    # 20% down + closing on an investment loan -> real cash in the deal.
    r = calc.rental(300_000, 2_500)
    assert r.cash_invested > 0


# --- Flip ------------------------------------------------------------------
def test_flip_seventy_percent_rule_ceiling():
    # ARV 300k, 40k repairs -> max offer = 300k*0.70 - 40k = 170k.
    f = calc.flip(arv=300_000, purchase=160_000, repairs=40_000)
    assert round(f.max_offer) == 170_000
    assert f.within_rule is True


def test_flip_good_deal_is_green():
    f = calc.flip(arv=300_000, purchase=150_000, repairs=40_000)
    assert f.band == "green"
    assert f.profit > 0


def test_flip_overpaying_is_amber():
    # Still profitable, but purchase is above the 70% ceiling.
    f = calc.flip(arv=300_000, purchase=185_000, repairs=40_000)
    assert f.within_rule is False
    assert f.band == "amber"
    assert f.profit > 0


def test_flip_losing_deal_is_red():
    f = calc.flip(arv=300_000, purchase=270_000, repairs=40_000)
    assert f.band == "red"
    assert f.profit < 0


def test_flip_more_repairs_lower_profit():
    light = calc.flip(arv=300_000, purchase=150_000, repairs=20_000)
    heavy = calc.flip(arv=300_000, purchase=150_000, repairs=80_000)
    assert heavy.profit < light.profit


def test_flip_longer_hold_costs_more():
    quick = calc.flip(arv=300_000, purchase=150_000, repairs=40_000, hold_months=3)
    slow = calc.flip(arv=300_000, purchase=150_000, repairs=40_000, hold_months=12)
    assert slow.holding_costs > quick.holding_costs
    assert slow.profit < quick.profit


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        fn()
        passed += 1
        print(f"  ok  {fn.__name__}")
    print(f"\n{passed}/{len(fns)} investing tests passed.")


if __name__ == "__main__":
    _run_all()

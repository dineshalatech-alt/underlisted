"""
Tests for blending ATTOM's independent AVM into the Deal Score.

PURE-logic tests — no API calls, no network. They lock in the rule that:
  * when BOTH RentCast and ATTOM give a value, the score uses their average;
  * when only one is present, that one is used;
  * when neither is present, the value-discount factor is excluded and the score
    rescales over the remaining factors (so adding ATTOM never breaks old scores).

Run from the project root:
    .venv/Scripts/python.exe -m pytest tests/test_attom_blend.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models import Listing, RentEstimate, ValueEstimate  # noqa: E402
from src.scoring import deal_score  # noqa: E402


def _listing(price=300_000):
    return Listing(id="x", address="1 Main St, Austin, TX 78701", city="Austin",
                   state="TX", zip_code="78701", list_price=price, days_on_market=30)


# --- blended_avm helper ----------------------------------------------------

def test_blend_averages_when_both_present():
    val, src = deal_score.blended_avm(ValueEstimate(avm=400_000),
                                      ValueEstimate(avm=300_000))
    assert val == 350_000
    assert "average" in src


def test_blend_uses_rentcast_when_attom_missing():
    val, src = deal_score.blended_avm(ValueEstimate(avm=400_000), None)
    assert val == 400_000
    assert src == "one estimate"


def test_blend_uses_attom_when_rentcast_missing():
    val, src = deal_score.blended_avm(None, ValueEstimate(avm=320_000))
    assert val == 320_000
    assert src == "one estimate"


def test_blend_none_when_neither_present():
    val, src = deal_score.blended_avm(None, None)
    assert val is None
    assert src == "no estimate"


def test_blend_ignores_empty_attom_avm():
    val, src = deal_score.blended_avm(ValueEstimate(avm=400_000), ValueEstimate())
    assert val == 400_000
    assert src == "one estimate"


# --- compute() with the attom keyword --------------------------------------

def test_compute_without_attom_matches_old_behaviour():
    l = _listing()
    base = deal_score.compute(l, ValueEstimate(avm=400_000),
                              RentEstimate(monthly_rent=2_000))
    # passing attom=None must be identical
    same = deal_score.compute(l, ValueEstimate(avm=400_000),
                              RentEstimate(monthly_rent=2_000), attom=None)
    assert base.total == same.total


def test_compute_blends_when_attom_present():
    l = _listing(price=300_000)
    # RentCast says 400k; ATTOM agrees-ish at 360k -> blend 380k.
    rc_only = deal_score.compute(l, ValueEstimate(avm=400_000),
                                 RentEstimate(monthly_rent=2_000))
    blended = deal_score.compute(l, ValueEstimate(avm=400_000),
                                 RentEstimate(monthly_rent=2_000),
                                 attom=ValueEstimate(avm=360_000))
    # blended value (380k) is lower than 400k -> smaller discount -> <= rc_only
    assert blended.total <= rc_only.total
    vd = next(f for f in blended.factors if f.key == "value_discount")
    assert vd.included
    assert "agree" in vd.detail


def test_compute_rescales_when_no_value_at_all():
    l = _listing()
    sc = deal_score.compute(l, None, RentEstimate(monthly_rent=2_000), attom=None)
    vd = next(f for f in sc.factors if f.key == "value_discount")
    assert not vd.included          # excluded, not zero-weighted into the score
    assert 0 <= sc.total <= 100     # still a valid rescaled score


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        fn()
        passed += 1
        print(f"  ok  {fn.__name__}")
    print(f"\n{passed}/{len(fns)} attom-blend tests passed.")


if __name__ == "__main__":
    _run_all()

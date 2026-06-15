"""
Free Investor Tools — run the numbers on any home, no signup.

Two beginner-friendly calculators, both PURE math (zero API calls):
  • Buy & Hold — monthly cash flow, cap rate, cash-on-cash return, 1% rule.
  • Fix & Flip — projected profit, ROI, and the classic 70% rule (ARV).

This is top-of-funnel free material: anyone can play with it, and it shows off
our plain-English style. The math lives in src/investing/calculators.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402

from app.assets.theme import (APP_CSS, PRIMARY_GREEN, AMBER, RED, MUTED,  # noqa: E402
                              DEEP_GREEN)
from app.icons import TABLER_CSS, ic  # noqa: E402
from app.helpers import money, favicon_path  # noqa: E402
from src.investing import calculators as calc  # noqa: E402
from src import glossary  # noqa: E402  (shared plain-English term wording)

st.set_page_config(page_title="Free investor calculators", page_icon=favicon_path(),
                   layout="centered")
st.markdown(APP_CSS + TABLER_CSS, unsafe_allow_html=True)

_BAND = {
    "green": (PRIMARY_GREEN, "#E1F5EE", "check"),
    "amber": (AMBER, "#FBE9C7", "shield"),
    "red":   (RED, "#FBE9E4", "shield"),
}


def _rng_money(r) -> str:
    if abs(r.high - r.low) < 1:
        return money(r.low)
    return f"{money(r.low)}–{money(r.high)}"


def _explain(key: str, label: str = "What does this mean?") -> None:
    """A small, tap-to-open 'What does this mean?' tip — same wording as the
    website's learn page and the deal screen (one source of truth: glossary)."""
    with st.popover(label):
        st.markdown(glossary.app_tip(key))


def _explain_row(keys: list) -> None:
    """A tidy row of term tooltips under a set of metrics."""
    cols = st.columns(len(keys))
    for col, (key, label) in zip(cols, keys):
        with col:
            _explain(key, label)


def _verdict(band: str, headline: str, reasons: list) -> None:
    color, bg, icon = _BAND.get(band, _BAND["amber"])
    bullets = "".join(f"<li style='margin:3px 0'>{r}</li>" for r in reasons)
    st.markdown(
        f"<div style='background:{bg};border:1px solid {color}33;border-radius:14px;"
        f"padding:14px 16px;margin:10px 0'>"
        f"<div style='font-size:1.25rem;font-weight:850;color:{color}'>"
        f"{ic(icon,22,color)} {headline}</div>"
        f"<ul style='color:#475467;margin:8px 0 0;padding-left:20px'>{bullets}</ul>"
        f"</div>", unsafe_allow_html=True)


st.markdown(f"## {ic('calc',26,PRIMARY_GREEN)} Free investor calculators",
            unsafe_allow_html=True)
st.caption("Run the numbers on any home in plain English — no signup. "
           "Estimates only, a screening tool, not advice.")
st.markdown(f"<div style='margin:-4px 0 6px'>New to these numbers? "
            f"<a href='{glossary.LEARN_URL_PUBLIC}' target='_blank' "
            f"style='color:{PRIMARY_GREEN};font-weight:700'>Read the 1-minute guide →"
            f"</a></div>", unsafe_allow_html=True)

hold_tab, flip_tab = st.tabs(["🏠  Buy & Hold (rental)", "🔨  Fix & Flip"])

# ---------------------------------------------------------------------------
# Buy & Hold
# ---------------------------------------------------------------------------
with hold_tab:
    st.markdown("**Will this rental make money each month?**")
    c1, c2 = st.columns(2)
    price = c1.number_input("Purchase price", min_value=0, value=300_000,
                            step=5_000, key="r_price")
    rent = c2.number_input("Expected monthly rent", min_value=0, value=2_400,
                           step=50, key="r_rent")
    c3, c4 = st.columns(2)
    hoa = c3.number_input("HOA dues ($/mo, 0 if none)", min_value=0, value=0,
                          step=25, key="r_hoa")
    credit = c4.selectbox("Your credit score", ["740+", "680-739", "620-679",
                          "580-619", "<580"], key="r_credit")

    if price > 0 and rent > 0:
        r = calc.rental(price, rent, credit_band=credit,
                        hoa_monthly=float(hoa))
        _verdict(r.band, r.headline, r.reasons)

        m1, m2, m3 = st.columns(3)
        m1.metric("Monthly cash flow", _rng_money(r.cash_flow))
        m2.metric("Cap rate", f"{r.cap_rate.low:.1f}–{r.cap_rate.high:.1f}%")
        m3.metric("Cash-on-cash", f"{r.cash_on_cash.low:.1f}–{r.cash_on_cash.high:.1f}%")
        _explain_row([("cash-flow", "What is cash flow?"),
                      ("cap-rate", "What is cap rate?"),
                      ("cash-on-cash", "What is cash-on-cash?")])
        if not r.one_pct_rule:
            _explain("one-percent-rule", "Below the 1% rule — what's that?")

        with st.expander("How we got there"):
            st.markdown(
                f"- **Rent:** {money(r.monthly_rent)}/mo\n"
                f"- **Loan payment (P&I):** {money(r.monthly_pi)}/mo\n"
                f"- **Operating costs** (tax, insurance, HOA, upkeep, vacancy, "
                f"management): {_rng_money(r.operating)}/mo\n"
                f"- **Cash you'd put in** (20% down + closing): {money(r.cash_invested)}\n\n"
                "Operating-cost ranges come from the same engine as our "
                "“Can I Afford It?” tool, so the two never disagree.")
    else:
        st.info("Enter a price and expected rent to see the numbers.")

# ---------------------------------------------------------------------------
# Fix & Flip
# ---------------------------------------------------------------------------
with flip_tab:
    st.markdown("**Is there profit in fixing this one up?**")
    c1, c2 = st.columns(2)
    arv = c1.number_input("After-repair value (ARV)", min_value=0, value=300_000,
                          step=5_000, key="f_arv",
                          help="What the home will be worth once it's fixed up. "
                               "Base it on recently SOLD, already-renovated homes nearby.")
    st.caption("Tip: the best ARV comes from what similar fixed-up homes recently "
               "SOLD for. Open any home in **Browse Deals** to see its real last "
               "sale price and an independent value estimate.")
    purchase = c2.number_input("Purchase price", min_value=0, value=160_000,
                               step=5_000, key="f_purchase")
    c3, c4 = st.columns(2)
    repairs = c3.number_input("Repair budget", min_value=0, value=40_000,
                              step=2_500, key="f_repairs")
    months = c4.number_input("Months to finish & sell", min_value=1, value=5,
                             step=1, key="f_months")

    if arv > 0 and purchase > 0:
        f = calc.flip(arv, purchase, repairs, hold_months=int(months))
        _verdict(f.band, f.headline, f.reasons)

        m1, m2, m3 = st.columns(3)
        m1.metric("Projected profit", money(f.profit))
        m2.metric("Return (ROI)", f"{f.roi_pct:.0f}%")
        m3.metric("70% rule max offer", money(f.max_offer))
        _explain_row([("arv", "What is ARV?"),
                      ("seventy-rule", "What is the 70% rule?"),
                      ("flip-costs", "Holding & selling costs?")])

        with st.expander("How we got there"):
            st.markdown(
                f"- **After-repair value (ARV):** {money(f.arv)}\n"
                f"- **− Purchase price:** {money(f.purchase)}\n"
                f"- **− Repairs:** {money(f.repairs)}\n"
                f"- **− Holding costs** ({f.hold_months} months): {money(f.holding_costs)}\n"
                f"- **− Selling costs** (agent + closing): {money(f.selling_costs)}\n"
                f"- **= Profit:** **{money(f.profit)}**\n\n"
                f"The **70% rule** says don't pay more than {money(f.max_offer)} "
                "(70% of ARV, minus repairs) to keep a safe cushion.")
    else:
        st.info("Enter an after-repair value and purchase price to see the numbers.")

st.divider()
st.markdown(
    f"<div style='color:{MUTED};font-size:.9rem'>These are estimates to screen deals "
    "fast — not financial advice. Want this calculated automatically on real "
    f"under-priced homes? <b style='color:{DEEP_GREEN}'>Browse Deals</b> does it for "
    "every listing.</div>", unsafe_allow_html=True)

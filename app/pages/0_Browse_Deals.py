"""
Browse Deals — the polished California feed + detail screen.

Pure visual pass: NO API calls. Uses real cached listings (or clearly-marked
SAMPLE listings if the cache is empty). Photos are grey placeholders with a house
icon. Icons come from the Tabler set (app/icons.py).
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402

from config.settings import settings  # noqa: E402
from src import metrics  # noqa: E402
from src.financing import cash_needed  # noqa: E402
from app.assets.theme import (APP_CSS, DEEP_GREEN, PRIMARY_GREEN, LIGHT_FILL,  # noqa: E402
                              MUTED, score_color)
from app.icons import TABLER_CSS, ic  # noqa: E402
from app.helpers import (money, number, dom_label, gmaps_link, pct,  # noqa: E402
                         favicon_path)
from app import sample_data  # noqa: E402

st.set_page_config(page_title="Browse Deals", page_icon=favicon_path(),
                   layout="centered")

FEED_CSS = f"""
<style>
  html, body, [class*="css"] {{ font-size: 17px; }}
  .stButton button {{ padding:.7rem 1rem; font-size:1.05rem; font-weight:600;
                      border-radius:12px; }}
  .price {{ font-size:2.0rem; font-weight:850; color:{DEEP_GREEN}; line-height:1.1; }}
  .addr {{ font-size:1.12rem; font-weight:700; color:#1F2933; }}
  .facts {{ font-size:1.04rem; color:#475467; }}
  .facts .ti {{ color:{PRIMARY_GREEN}; margin-right:3px; }}
  .scorewrap {{ display:flex; align-items:center; gap:12px; margin:2px 0 8px; }}
  .scorenum {{ font-size:1.7rem; font-weight:850; color:#fff; border-radius:14px;
               padding:8px 16px; min-width:70px; text-align:center; }}
  .scorelabel {{ font-size:1.15rem; font-weight:800; }}
  .whybar {{ display:flex; height:18px; width:100%; border-radius:9px;
             overflow:hidden; margin:8px 0; }}
  .dot {{ display:inline-block; width:11px; height:11px; border-radius:3px;
          margin-right:7px; }}
  .sampletag {{ background:#FBE9C7; color:#9a6700; font-size:.78rem; font-weight:700;
                padding:1px 8px; border-radius:999px; }}
  .photo {{ height:200px; border-radius:14px; background:{LIGHT_FILL};
            display:flex; align-items:center; justify-content:center; }}
  .cashbig {{ font-size:1.9rem; font-weight:850; color:{DEEP_GREEN}; }}
</style>
"""
st.markdown(APP_CSS + TABLER_CSS + FEED_CSS, unsafe_allow_html=True)

st.session_state.setdefault("open_id", None)

FACTOR_COLORS = {"value_discount": "#1D9E75", "rent_yield": "#2E86C1",
                 "days_on_market": "#8E44AD", "risk": "#F39C12"}


def _label(score) -> str:
    if score.total >= score.threshold:
        return "Great deal"
    if score.total >= 45:
        return "Worth a look"
    return "Below average"


def _score_badge(score) -> str:
    c = score_color(score.total)
    return (f"<div class='scorewrap'>"
            f"<span class='scorenum' style='background:{c}'>{score.total}</span>"
            f"<span class='scorelabel' style='color:{c}'>{ic('score',20,c)} "
            f"{_label(score)}<br><span style='font-weight:400;color:{MUTED};"
            f"font-size:.8rem'>Deal score · 0–100</span></span></div>")


def _why_bar(score) -> str:
    used = [f for f in score.used_factors if f.points > 0]
    tot = sum(f.points for f in used) or 1
    segs = "".join(f"<div style='width:{f.points/tot*100:.1f}%;"
                   f"background:{FACTOR_COLORS.get(f.key, MUTED)}'></div>" for f in used)
    return f"<div class='whybar'>{segs}</div>"


def _photo_placeholder() -> str:
    return f"<div class='photo'>{ic('home', 46, MUTED)}</div>"


def _facts_html(l) -> str:
    return (f"<div class='facts'>{ic('beds')} {number(l.beds)} bd &nbsp; "
            f"{ic('baths')} {number(l.baths)} ba &nbsp; "
            f"{ic('sqft')} {number(l.sqft)} sqft &nbsp; "
            f"{ic('year')} {number(l.year_built)}</div>")


# ===========================================================================
# DETAIL
# ===========================================================================
def render_detail(row) -> None:
    l = row["listing"]
    val, rent, score = row["value"], row["rent"], row["score"]

    if st.button("← Back to listings", key="back"):
        st.session_state.open_id = None
        st.rerun()

    st.markdown(_photo_placeholder(), unsafe_allow_html=True)
    st.caption("Photo — street view (preview placeholder)")

    st.markdown(f"<div class='price'>{money(l.list_price)}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='addr'>{l.address or '—'}</div>", unsafe_allow_html=True)
    st.markdown(_facts_html(l), unsafe_allow_html=True)
    st.markdown(f"<div class='facts'>{ic('clock')} {dom_label(l.days_on_market)} &nbsp; "
                f"{ic('location')} {l.city} {l.zip_code}</div>", unsafe_allow_html=True)
    link = gmaps_link(l.address)
    if link:
        st.markdown(f"<a href='{link}' target='_blank'>{ic('location')} "
                    "Open in Google Maps</a>", unsafe_allow_html=True)

    st.divider()
    # --- Deal Score + why ---
    st.markdown(_score_badge(score), unsafe_allow_html=True)
    with st.popover("What's the deal score?"):
        st.write("A 0–100 rating of how good a deal this looks — mostly how far "
                 "below its estimated value it's listed, plus rent yield. Higher "
                 "= better. It's a screening guide, not a guarantee.")
    st.markdown(f"##### Why it scored {score.total}")
    st.markdown(_why_bar(score), unsafe_allow_html=True)
    for f in score.factors:
        color = FACTOR_COLORS.get(f.key, MUTED)
        if f.included:
            st.markdown(f"<span class='dot' style='background:{color}'></span>"
                        f"**{f.label}** — {f.detail} &nbsp; "
                        f"<span class='muted'>{f.points:.0f}/{f.weight:.0f} pts</span>",
                        unsafe_allow_html=True)
        else:
            st.markdown(f"<span class='dot' style='background:#D0D5DD'></span>"
                        f"<span class='muted'>{f.label} — {f.detail} "
                        "(not counted yet)</span>", unsafe_allow_html=True)

    st.divider()
    # --- Value & rent (plain) ---
    vsample = " <span class='sampletag'>sample</span>" if row["value_sample"] else ""
    if val.avm:
        diff = (val.avm or 0) - (l.list_price or 0)
        word = "below" if diff > 0 else ("above" if diff < 0 else "right at")
        st.markdown(f"{ic('value',20,PRIMARY_GREEN)} Estimated value: "
                    f"**{money(val.avm)}**{vsample} — listed **{money(abs(diff))} "
                    f"{word}** value.", unsafe_allow_html=True)
        if val.value_low and val.value_high:
            st.caption(f"Value range {money(val.value_low)}–{money(val.value_high)} · "
                       f"{len(val.comps or [])} comparable sales")
        with st.popover("What's 'estimated value'?"):
            st.write("A computer estimate (an 'AVM') of the home's worth from recent "
                     "nearby sales. A guide, not an appraisal.")
    rsample = " <span class='sampletag'>sample</span>" if row["rent_sample"] else ""
    st.markdown(f"{ic('rent',20,PRIMARY_GREEN)} Estimated rent: "
                f"**{money(rent)}/mo**{rsample}", unsafe_allow_html=True)
    with st.popover("What's 'estimated rent'?"):
        st.write("A computer estimate of monthly rent from similar nearby rentals. "
                 "Actual rent varies.")

    st.divider()
    # --- How much cash you really need ---
    st.markdown(f"#### {ic('key',22,DEEP_GREEN)} How much cash you really need",
                unsafe_allow_html=True)
    plan = st.radio("Your plan", ["I'll live in it", "I'll rent it out"],
                    horizontal=True, key=f"plan_{l.id}")
    occupancy = "investment" if "rent" in plan else "live_in"
    loan_type = "conventional"
    cc = st.columns(2)
    if occupancy == "live_in":
        loan_type = cc[0].selectbox("Loan type", ["conventional", "fha", "va"],
                                    format_func=str.upper, key=f"lt_{l.id}")
    band = cc[1].selectbox("Your credit score", cash_needed.CREDIT_BANDS,
                           key=f"cb_{l.id}")

    cn = cash_needed.compute(l.list_price or 0, occupancy=occupancy,
                             loan_type=loan_type, credit_band=band)

    st.markdown(f"<div class='cashbig'>To buy this home, you'd need about "
                f"{money(cn.total)} in cash.</div>", unsafe_allow_html=True)
    st.caption("An estimate — not a loan offer.")

    def line(icon, label, amount, sub, help_text):
        a, b = st.columns([3, 2])
        with a.popover(f"{label}"):
            st.write(help_text)
        b.markdown(f"{ic(icon,18,PRIMARY_GREEN)} **{amount}**"
                   + (f" <span class='muted'>· {sub}</span>" if sub else ""),
                   unsafe_allow_html=True)

    st.markdown("**Money that leaves your account**")
    line("down", "Down payment", money(cn.down_payment),
         f"{cn.down_payment_pct:.1f}% upfront", "The chunk you pay upfront.")
    line("closing", "Closing costs",
         f"{money(cn.closing_low)}–{money(cn.closing_high)}", "one-time fees",
         "One-time fees to finalize: escrow, title, appraisal, lender fees "
         "(usually 2–5%).")
    st.markdown(f"= {ic('wallet',18,DEEP_GREEN)} **Cash to close: "
                f"{money(cn.cash_to_close)}**", unsafe_allow_html=True)
    st.markdown("**Money you keep (don't spend)**")
    line("reserves", "Reserves", money(cn.reserves),
         f"{cn.reserves_months} months", "Cash the lender wants you to keep in "
         "the bank after buying. You don't spend it.")
    st.markdown(f"= {ic('key',18,DEEP_GREEN)} **Grand total cash needed: "
                f"{money(cn.total)}**", unsafe_allow_html=True)

    with st.expander("Full breakdown (for power users)"):
        m = metrics.compute(l, val, type("R", (), {"monthly_rent": rent})(),
                            settings.financing)
        c = st.columns(3)
        c[0].metric("Monthly payment", money(cn.monthly_payment),
                    help="Principal + interest. Taxes/insurance (PITI) add more.")
        c[1].metric("Est. rate", pct(cn.interest_rate),
                    help="Estimated by credit band; update in financing.yaml.")
        c[2].metric("Loan amount", money(cn.loan_amount))
        c2 = st.columns(3)
        c2[0].metric("Gross yield", pct(m.gross_yield_pct),
                     help="Yearly rent ÷ price.")
        one = "Yes" if m.meets_one_percent_rule else "No"
        c2[1].metric("1% rule", one, help="Monthly rent ≥ 1% of price?")
        c2[2].metric("Cap rate", pct(m.cap_rate_pct),
                     help="Rough yearly return after assumed expenses.")
        st.caption("DTI note: lenders also check your debt-to-income ratio — your "
                   "monthly debts vs. income. Ask a lender for your number.")

    st.divider()
    st.caption("All figures are ESTIMATES to help you screen homes — not advice, an "
               "appraisal, or a loan offer. Verify with a licensed lender and agent.")


# ===========================================================================
# FEED
# ===========================================================================
def render_feed(rows, sample_mode) -> None:
    logo_title = f"{settings.active_state_name} deals"
    st.markdown(f"<div class='app-header'>{ic('home',20)} {logo_title}"
                "<span style='font-weight:400;opacity:.85'> · best deals first"
                "</span></div>", unsafe_allow_html=True)

    if sample_mode:
        st.warning("Showing SAMPLE listings for design preview — no live data used.",
                   icon="🎨")

    with st.expander(f"Filter"):
        names = settings.city_names()
        cities = st.multiselect("City", names, default=names)
        good_only = st.toggle("Good deals only (score ≥ "
                              f"{settings.scoring.get('good_deal_threshold',70)})")

    shown = [r for r in rows
             if (not cities or r["listing"].city in cities)
             and (not good_only or r["score"].is_good_deal)]
    shown.sort(key=lambda r: -r["score"].total)
    st.markdown(f"<div class='facts' style='margin:6px 0'>{ic('search')} "
                f"{len(shown)} home(s)</div>", unsafe_allow_html=True)

    for r in shown:
        l, score = r["listing"], r["score"]
        with st.container(border=True):
            st.markdown(_photo_placeholder(), unsafe_allow_html=True)
            st.markdown(_score_badge(score), unsafe_allow_html=True)
            st.markdown(f"<div class='price'>{money(l.list_price)}</div>",
                        unsafe_allow_html=True)
            st.markdown(f"<div class='addr'>{ic('location',16,MUTED)} "
                        f"{l.address or '—'}</div>", unsafe_allow_html=True)
            st.markdown(_facts_html(l), unsafe_allow_html=True)
            rs = " <span class='sampletag'>sample</span>" if r["rent_sample"] else ""
            st.markdown(f"<div class='facts'>{ic('rent')} ~{money(r['rent'])}/mo rent{rs}"
                        f"</div>", unsafe_allow_html=True)
            if st.button("See details", key=f"o_{l.id}", use_container_width=True,
                         type="primary"):
                st.session_state.open_id = l.id
                st.rerun()

    st.divider()
    st.caption("Deal scores are ESTIMATES — a screening tool, not financial advice. "
               "California only for now.")


# ---- Router ----
rows, sample_mode = sample_data.display_rows()
by_id = {r["listing"].id: r for r in rows}
if st.session_state.open_id and st.session_state.open_id in by_id:
    render_detail(by_id[st.session_state.open_id])
else:
    render_feed(rows, sample_mode)

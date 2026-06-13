"""
Underlisted — marketing / landing page (the front door). Nationwide (U.S.).

This is the entry screen at http://localhost:8501. The actual app (the deal feed)
is the "Browse Deals" page. Pure visual — no API calls.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402

from app.assets.theme import DEEP_GREEN, PRIMARY_GREEN, LIGHT_FILL, AMBER  # noqa: E402
from app.icons import TABLER_CSS, ic  # noqa: E402
from app.helpers import logo_data_uri, favicon_path  # noqa: E402

st.set_page_config(page_title="Underlisted", page_icon=favicon_path(),
                   layout="centered")

LOGO = logo_data_uri()

st.markdown(TABLER_CSS + f"""
<style>
  #MainMenu, footer {{visibility:hidden;}}
  .block-container {{ padding-top: 2rem; }}
  .hero {{
      background: linear-gradient(135deg, {DEEP_GREEN} 0%, {PRIMARY_GREEN} 100%);
      border-radius: 24px; padding: 40px 28px; text-align:center; color:#fff;
      box-shadow: 0 12px 30px rgba(15,110,86,.25);
  }}
  .hero h1 {{ color:#fff; font-size:2.5rem; font-weight:850; margin:.4rem 0; line-height:1.1; }}
  .hero p {{ color:#EAFBF4; font-size:1.2rem; margin:.2rem auto; max-width:34rem; }}
  .pricepill {{ display:inline-block; background:rgba(255,255,255,.18);
      border:1px solid rgba(255,255,255,.35); color:#fff; padding:8px 16px;
      border-radius:999px; font-weight:700; margin-top:14px; font-size:1.05rem; }}
  .feat {{ background:#fff; border:1px solid #E4E7EC; border-radius:16px;
      padding:20px; height:100%; }}
  .feat h3 {{ margin:.3rem 0; font-size:1.15rem; }}
  .feat .muted {{ font-size:.98rem; }}
  .pricecard {{ background:{LIGHT_FILL}; border:2px solid {PRIMARY_GREEN};
      border-radius:20px; padding:26px; text-align:center; }}
  .big {{ font-size:2.4rem; font-weight:850; color:{DEEP_GREEN}; }}
  .stButton button {{ border-radius:12px; font-weight:700; padding:.7rem 1rem; font-size:1.05rem; }}
</style>
""", unsafe_allow_html=True)

# ---- HERO ----
st.markdown(f"""
<div class="hero">
  <img src="{LOGO}" width="76" style="border-radius:18px"/>
  <h1>Find under-priced U.S. homes in seconds</h1>
  <p>A beginner-friendly deal finder. See a clear 0–100 deal score, the real rent
     and value, and exactly how much cash you'd need — in plain English.</p>
  <div class="pricepill">$12.99/mo for your first 12 months, then $29.99 · cancel anytime</div>
  <!-- pricing: $12.99 intro (12 mo) -> $29.99 standard -> rising to $44.99 later -->
</div>
""", unsafe_allow_html=True)

st.write("")
c1, c2 = st.columns(2)
if c1.button("Start 3-day free trial", type="primary", use_container_width=True):
    st.switch_page("pages/0_Browse_Deals.py")
if c2.button("Browse deals", use_container_width=True):
    st.switch_page("pages/0_Browse_Deals.py")
st.caption("No charge today — this is a preview. Card required when billing is "
           "switched on later.")

st.write("")
st.markdown("### Why people use it")
f1, f2, f3 = st.columns(3)
f1.markdown(f"<div class='feat'>{ic('score',26,PRIMARY_GREEN)}<h3>Instant deal score</h3>"
            "<div class='muted'>Every home gets a 0–100 score so you spot the good "
            "ones at a glance — green means a great deal.</div></div>",
            unsafe_allow_html=True)
f2.markdown(f"<div class='feat'>{ic('value',26,PRIMARY_GREEN)}<h3>Real rent & value</h3>"
            "<div class='muted'>See estimated value and rent, and whether a home is "
            "listed below what it's worth — with the comparables behind it.</div></div>",
            unsafe_allow_html=True)
f3.markdown(f"<div class='feat'>{ic('wallet',26,PRIMARY_GREEN)}<h3>Know your cash</h3>"
            "<div class='muted'>One plain number for the cash you'd really need — "
            "down payment, closing costs, and reserves, explained.</div></div>",
            unsafe_allow_html=True)

st.write("")
st.markdown("### How it works")
s1, s2, s3 = st.columns(3)
s1.markdown(f"{ic('search',22,PRIMARY_GREEN)} **1. Browse** the nationwide feed.",
            unsafe_allow_html=True)
s2.markdown(f"{ic('gauge' if False else 'score',22,PRIMARY_GREEN)} **2. Scan scores** "
            "— green = great deal.", unsafe_allow_html=True)
s3.markdown(f"{ic('wallet',22,PRIMARY_GREEN)} **3. Tap a home** for the full plain-"
            "English breakdown.", unsafe_allow_html=True)

st.write("")
st.markdown(f"""
<div class="pricecard">
  <div style="font-weight:700;font-size:1.1rem">Simple pricing</div>
  <div class="big">$12.99<span style="font-size:1.1rem;font-weight:600">/mo</span></div>
  <div class="muted">for your first 12 months, then $29.99/mo</div>
  <div style="margin-top:6px;color:{AMBER};font-weight:700">Lock in $12.99/mo for a year — the price is rising to $44.99 soon.</div>
  <div style="margin-top:8px">{ic('check',18,PRIMARY_GREEN)} 3-day free trial &nbsp;
     {ic('check',18,PRIMARY_GREEN)} cancel anytime &nbsp;
     {ic('check',18,PRIMARY_GREEN)} Nationwide listings</div>
</div>
""", unsafe_allow_html=True)

st.write("")
if st.button("Start 3-day free trial  →", type="primary", use_container_width=True):
    st.switch_page("pages/0_Browse_Deals.py")

st.divider()
st.caption("Estimates only — a screening tool, not investment advice or a loan "
           "offer. Fair Housing: scoring never uses demographic or 'neighborhood "
           "quality' signals. Now nationwide across the U.S.")

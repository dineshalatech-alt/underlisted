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

from config.settings import settings  # noqa: E402
from app.assets.theme import (  # noqa: E402
    CORAL, CORAL_DEEP, GOLD, CREAM, WARM_FILL, COCOA, INK, MUTED,
    GREEN_GOOD, AMBER,
)
from app.icons import TABLER_CSS, ic  # noqa: E402
from app.helpers import logo_data_uri, favicon_path  # noqa: E402

# Your Payhip subscription link (set it in config/cache.yaml -> checkout_url).
# When present, the landing page shows a real "Subscribe" button; otherwise it
# shows the free preview button only.
CHECKOUT_URL = (settings.cache.get("checkout_url") or "").strip()

st.set_page_config(page_title="Underlisted", page_icon=favicon_path(),
                   layout="centered")

LOGO = logo_data_uri()

st.markdown(TABLER_CSS + f"""
<style>
  #MainMenu, footer {{visibility:hidden;}}
  .stApp {{ background:{CREAM}; }}
  .block-container {{ padding-top: 1.2rem; }}

  /* ---- HERO with looping video background ---- */
  .hero {{
      position:relative; overflow:hidden;
      border-radius:28px; padding:52px 28px 46px; text-align:center;
      color:#fff; isolation:isolate;
      box-shadow: 0 22px 50px rgba(46,42,38,.28);
  }}
  .hero video.bg, .hero img.bg {{
      position:absolute; inset:0; width:100%; height:100%;
      object-fit:cover; z-index:-2;
  }}
  .hero .scrim {{
      position:absolute; inset:0; z-index:-1;
      background: linear-gradient(180deg, rgba(46,42,38,.45) 0%, rgba(46,42,38,.62) 55%, rgba(226,81,63,.55) 100%);
  }}
  .hero .logo-badge {{
      display:inline-flex; align-items:center; justify-content:center;
      width:72px; height:72px; border-radius:20px; margin-bottom:8px;
      background:rgba(255,255,255,.16); backdrop-filter:blur(4px);
      border:1px solid rgba(255,255,255,.35);
  }}
  .hero h1 {{ color:#fff; font-size:2.6rem; font-weight:850; margin:.5rem 0 .3rem;
      line-height:1.08; letter-spacing:-.5px; text-shadow:0 2px 18px rgba(0,0,0,.35); }}
  .hero p {{ color:#FFF3EE; font-size:1.18rem; margin:.2rem auto; max-width:34rem;
      text-shadow:0 1px 10px rgba(0,0,0,.3); }}
  .pricepill {{ display:inline-block; background:rgba(255,255,255,.20);
      border:1px solid rgba(255,255,255,.45); color:#fff; padding:9px 18px;
      border-radius:999px; font-weight:700; margin-top:18px; font-size:1.05rem;
      backdrop-filter:blur(3px); }}

  /* ---- Feature cards ---- */
  .feat {{ background:#fff; border:1px solid {WARM_FILL}; border-radius:18px;
      padding:22px; height:100%; box-shadow:0 6px 18px rgba(46,42,38,.06);
      transition:transform .15s ease, box-shadow .15s ease; }}
  .feat:hover {{ transform:translateY(-3px); box-shadow:0 12px 26px rgba(46,42,38,.10); }}
  .feat h3 {{ margin:.5rem 0 .3rem; font-size:1.15rem; color:{INK}; }}
  .feat .muted {{ font-size:.98rem; color:{MUTED}; }}

  /* ---- Pricing card ---- */
  .pricecard {{ background:#fff; border:2px solid {CORAL};
      border-radius:22px; padding:28px; text-align:center;
      box-shadow:0 14px 34px rgba(255,107,92,.16); }}
  .big {{ font-size:2.6rem; font-weight:850; color:{CORAL_DEEP}; }}

  /* ---- Buttons ---- */
  .stButton button {{ border-radius:14px; font-weight:750; padding:.78rem 1rem;
      font-size:1.06rem; }}
  .stButton button[kind="primary"] {{ box-shadow:0 8px 20px rgba(255,107,92,.32); }}
  h3 {{ color:{INK}; }}
</style>
""", unsafe_allow_html=True)

# ---- HERO (video background + warm scrim) ----
st.markdown(f"""
<div class="hero">
  <video class="bg" autoplay loop muted playsinline poster="/app/static/hero_poster.jpg">
    <source src="/app/static/hero.mp4" type="video/mp4"/>
  </video>
  <div class="scrim"></div>
  <div class="logo-badge"><img src="{LOGO}" width="48" style="border-radius:12px"/></div>
  <h1>Find under-priced U.S. homes in seconds</h1>
  <p>A beginner-friendly deal finder. See a clear 0–100 deal score, the real rent
     and value, and exactly how much cash you'd need — in plain English.</p>
  <div class="pricepill">$12.99/mo for your first 12 months, then $29.99 · cancel anytime</div>
  <!-- pricing: $12.99 intro (12 mo) -> $29.99 standard -> rising to $44.99 later -->
</div>
""", unsafe_allow_html=True)

st.write("")
c1, c2 = st.columns(2)
if CHECKOUT_URL:
    c1.link_button("Subscribe — lock in $12.99/mo", CHECKOUT_URL,
                   type="primary", use_container_width=True)
else:
    if c1.button("Start 3-day free trial", type="primary", use_container_width=True):
        st.switch_page("pages/0_Browse_Deals.py")
if c2.button("Browse deals (free preview)", use_container_width=True):
    st.switch_page("pages/0_Browse_Deals.py")
if CHECKOUT_URL:
    st.caption("Secure checkout by Payhip · cancel anytime. Browse the preview "
               "free, subscribe to lock in the founding price.")
else:
    st.caption("No charge today — this is a preview. Card required when billing is "
               "switched on later.")

st.write("")
st.markdown("### Why people use it")
f1, f2, f3 = st.columns(3)
f1.markdown(f"<div class='feat'>{ic('score',26,CORAL)}<h3>Instant deal score</h3>"
            "<div class='muted'>Every home gets a 0–100 score so you spot the good "
            "ones at a glance — green means a great deal.</div></div>",
            unsafe_allow_html=True)
f2.markdown(f"<div class='feat'>{ic('value',26,CORAL)}<h3>Real rent & value</h3>"
            "<div class='muted'>See estimated value and rent, and whether a home is "
            "listed below what it's worth — with the comparables behind it.</div></div>",
            unsafe_allow_html=True)
f3.markdown(f"<div class='feat'>{ic('wallet',26,CORAL)}<h3>Know your cash</h3>"
            "<div class='muted'>One plain number for the cash you'd really need — "
            "down payment, closing costs, and reserves, explained.</div></div>",
            unsafe_allow_html=True)

st.write("")
st.markdown("### How it works")
s1, s2, s3 = st.columns(3)
s1.markdown(f"{ic('search',22,CORAL)} **1. Browse** the nationwide feed.",
            unsafe_allow_html=True)
s2.markdown(f"{ic('gauge' if False else 'score',22,CORAL)} **2. Scan scores** "
            "— green = great deal.", unsafe_allow_html=True)
s3.markdown(f"{ic('wallet',22,CORAL)} **3. Tap a home** for the full plain-"
            "English breakdown.", unsafe_allow_html=True)

st.write("")
st.markdown(f"""
<div class="pricecard">
  <div style="font-weight:700;font-size:1.1rem">Simple pricing</div>
  <div class="big">$12.99<span style="font-size:1.1rem;font-weight:600">/mo</span></div>
  <div class="muted">for your first 12 months, then $29.99/mo</div>
  <div style="margin-top:6px;color:{AMBER};font-weight:700">Lock in $12.99/mo for a year — the price is rising to $44.99 soon.</div>
  <div style="margin-top:8px">{ic('check',18,CORAL)} 3-day free trial &nbsp;
     {ic('check',18,CORAL)} cancel anytime &nbsp;
     {ic('check',18,CORAL)} Nationwide listings</div>
</div>
""", unsafe_allow_html=True)

st.write("")
if CHECKOUT_URL:
    st.link_button("Subscribe — lock in $12.99/mo  →", CHECKOUT_URL,
                   type="primary", use_container_width=True)
else:
    if st.button("Start 3-day free trial  →", type="primary", use_container_width=True):
        st.switch_page("pages/0_Browse_Deals.py")

st.divider()
st.caption("Estimates only — a screening tool, not investment advice or a loan "
           "offer. Fair Housing: scoring never uses demographic or 'neighborhood "
           "quality' signals. Now nationwide across the U.S.")

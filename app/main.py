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
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,700;9..40,800;9..40,900&display=swap');
  #MainMenu, footer {{visibility:hidden;}}
  /* DM Sans everywhere (Apple-style) */
  html, body, .stApp, .stApp *, button, input, textarea {{
      font-family:'DM Sans', system-ui, -apple-system, "Segoe UI", sans-serif !important;
      -webkit-font-smoothing:antialiased;
  }}
  /* Black base + a faint engraved dollar-bill pattern in gold */
  .stApp {{
      background-color:#000;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='260' height='130' viewBox='0 0 260 130'%3E%3Cg fill='none' stroke='%23E8B948' stroke-opacity='0.10' stroke-width='1.4'%3E%3Crect x='10' y='10' width='240' height='110' rx='10'/%3E%3Crect x='17' y='17' width='226' height='96' rx='8'/%3E%3Cellipse cx='130' cy='65' rx='44' ry='30'/%3E%3Ccircle cx='40' cy='65' r='16'/%3E%3Ccircle cx='220' cy='65' r='16'/%3E%3C/g%3E%3Cg fill='%23E8B948' fill-opacity='0.12' font-family='Georgia,serif' font-weight='bold' text-anchor='middle'%3E%3Ctext x='130' y='77' font-size='34'%3E%24%3C/text%3E%3Ctext x='40' y='71' font-size='18'%3E%24%3C/text%3E%3Ctext x='220' y='71' font-size='18'%3E%24%3C/text%3E%3C/g%3E%3C/svg%3E");
      background-size: 240px 120px;
  }}
  /* Off-white text on black */
  .stApp, .stApp p, .stApp li, .stApp span, .stMarkdown {{ color:#F5F5F7; }}
  [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] *, small {{ color:#9A9AA0 !important; }}
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
      background: linear-gradient(180deg, rgba(0,0,0,.35) 0%, rgba(0,0,0,.55) 55%, rgba(0,0,0,.92) 100%);
  }}
  .hero {{ border:1px solid rgba(232,185,72,.22); }}
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

  /* ---- Feature cards (dark glass) ---- */
  .feat {{ background:linear-gradient(180deg,#16140F 0%,#0E0D0A 100%);
      border:1px solid rgba(232,185,72,.18); border-radius:18px;
      padding:22px; height:100%; box-shadow:0 10px 26px rgba(0,0,0,.5);
      transition:transform .15s ease, box-shadow .15s ease, border-color .15s ease; }}
  .feat:hover {{ transform:translateY(-3px); border-color:rgba(232,185,72,.45);
      box-shadow:0 16px 34px rgba(0,0,0,.6); }}
  .feat h3 {{ margin:.5rem 0 .3rem; font-size:1.15rem; color:#F5F5F7; }}
  .feat .muted {{ font-size:.98rem; color:#A1A1A6; }}

  /* ---- "Why Us" section pieces ---- */
  /* The frame band: a calm, premium pull-quote */
  .frameband {{
      margin: 6px auto 4px; max-width: 40rem; text-align:center;
      padding: 22px 26px; border-radius:16px;
      background: linear-gradient(180deg, rgba(232,185,72,.06) 0%, rgba(232,185,72,.02) 100%);
      border:1px solid rgba(232,185,72,.20);
  }}
  .frameband p {{ font-size:1.12rem; line-height:1.6; color:#E8E8EC; margin:0; }}
  .frameband b {{ color:#F4DE8A; font-weight:800; }}

  .section-eyebrow {{ text-align:center; letter-spacing:3px; font-size:.76rem;
      font-weight:800; text-transform:uppercase; color:#C99A2E; margin:0 0 4px; }}
  .section-title {{ text-align:center; font-size:1.9rem; font-weight:850;
      color:#F5F5F7; letter-spacing:-.5px; margin:.1rem 0 .2rem; }}

  /* Benefit card number badge */
  .feat .num {{ display:inline-flex; align-items:center; justify-content:center;
      width:34px; height:34px; border-radius:10px; font-weight:850; font-size:1rem;
      color:#5B430C; margin-bottom:6px;
      background: linear-gradient(135deg,#E8B948 0%,#FBEFB0 40%,#D9A93A 100%);
      box-shadow:0 4px 12px rgba(201,154,46,.3); }}

  /* The bold contrast statement */
  .contrast {{
      margin: 8px auto; max-width: 42rem; text-align:center;
      padding: 30px 26px; border-radius:20px;
      background: linear-gradient(180deg,#16140F 0%,#0B0A07 100%);
      border:1px solid rgba(232,185,72,.30);
      box-shadow:0 16px 40px rgba(0,0,0,.55);
  }}
  .contrast .dim {{ color:#8C8C92; font-size:1.18rem; font-weight:600; line-height:1.5; }}
  .contrast .lead {{ color:#F5F5F7; font-size:1.42rem; font-weight:850; line-height:1.4;
      letter-spacing:-.3px; display:block; margin-top:6px; }}
  .contrast .lead b {{ color:#F4DE8A; }}

  /* Trust strip */
  .trust {{ text-align:center; margin: 4px auto 0; max-width: 42rem;
      font-size:.95rem; color:#A1A1A6; }}
  .trust span {{ white-space:nowrap; }}
  .trust .dot {{ color:#C99A2E; margin:0 10px; font-weight:800; }}

  /* ---- Pricing card ---- */
  .pricecard {{ background:#fff; border:2px solid {CORAL};
      border-radius:22px; padding:28px; text-align:center;
      box-shadow:0 14px 34px rgba(255,107,92,.16); }}
  .big {{ font-size:2.6rem; font-weight:850; color:{CORAL_DEEP}; }}

  /* ---- Buttons: all golden ---- */
  .stButton > button, .stLinkButton > a, .stDownloadButton > button {{
      background: linear-gradient(135deg,#E8B948 0%,#FBEFB0 26%,#D9A93A 55%,#F4DE8A 80%,#C99A2E 100%) !important;
      color:#5B430C !important; border:1px solid #C99A2E !important;
      border-radius:14px !important; font-weight:800 !important;
      padding:.78rem 1rem !important; font-size:1.06rem !important;
      box-shadow:0 8px 20px rgba(201,154,46,.35) !important;
      transition:filter .15s ease, transform .15s ease;
  }}
  .stButton > button *, .stLinkButton > a * {{ color:#5B430C !important; }}
  .stButton > button:hover, .stLinkButton > a:hover, .stDownloadButton > button:hover {{
      filter:brightness(1.06); transform:translateY(-1px); border-color:#B8860B !important;
  }}
  .stApp h1, .stApp h2, .stApp h3 {{ color:#F5F5F7; letter-spacing:-.3px; }}

  /* ---- Gold foil text + shimmer sweep ---- */
  .gold-foil {{
      background: linear-gradient(95deg,#B8860B 0%,#F7E08A 22%,#FFF6C8 42%,#E6B645 60%,#B8860B 100%);
      background-size: 200% auto;
      -webkit-background-clip:text; background-clip:text;
      -webkit-text-fill-color:transparent; color:transparent;
      animation: gshine 4.5s linear infinite; font-weight:850;
  }}
  @keyframes gshine {{ to {{ background-position: 200% center; }} }}

  /* ---- "Founding member" banknote / dollar-bill motif ---- */
  .note {{
      color:#3A2C08;  /* light card on black -> keep its own text dark */
      position:relative; border-radius:18px; padding:32px 26px 24px; text-align:center;
      background:
        radial-gradient(circle at 12% 16%, rgba(31,174,122,.07), transparent 42%),
        radial-gradient(circle at 88% 84%, rgba(31,174,122,.07), transparent 42%),
        linear-gradient(180deg,#FFFEF9 0%,#FBF6E9 100%);
      border:2px solid #D9B44A;
      box-shadow: 0 16px 40px rgba(160,120,20,.18), inset 0 0 0 1px #FFFDF8,
                  inset 0 0 0 6px rgba(217,180,74,.16);
  }}
  .note::before {{  /* fine engraving / guilloché frame */
      content:""; position:absolute; inset:9px; border-radius:12px; pointer-events:none;
      border:1.5px solid rgba(184,134,11,.42);
      background-image: repeating-linear-gradient(45deg, rgba(184,134,11,.05) 0 2px, transparent 2px 7px);
  }}
  .note > * {{ position:relative; z-index:1; }}
  .note .seal {{
      position:absolute; width:50px; height:50px; border-radius:50%; z-index:2;
      display:flex; align-items:center; justify-content:center;
      font-weight:850; font-size:1.15rem; color:#8A5E0E;
      background: radial-gradient(circle at 35% 30%, #FBF0B8, #E3B53D 68%, #B8860B);
      border:2px solid #C99A2E; box-shadow:0 2px 6px rgba(160,120,20,.4);
  }}
  .note .seal.tl {{ top:-16px; left:-16px; }}
  .note .seal.br {{ bottom:-16px; right:-16px; }}
  .note .eyebrow {{ letter-spacing:3px; font-size:.78rem; font-weight:800; color:#9A6B12;
      text-transform:uppercase; }}
  .note .strike {{ color:{MUTED}; text-decoration:line-through; text-decoration-color:#C0392B;
      text-decoration-thickness:2px; font-size:1.45rem; font-weight:700; }}
  .note .now {{ font-size:3.3rem; line-height:1; margin:.12rem 0; }}
  .note .per {{ font-size:1.05rem; font-weight:800; color:#9A6B12; }}
  .note .serial {{ margin-top:12px; font-family:'Courier New',monospace; letter-spacing:1px;
      font-size:.76rem; color:#9A6B12; border-top:1px dashed rgba(184,134,11,.5); padding-top:9px; }}
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
  <div class="pricepill">⭐ Early-bird: <s style="opacity:.65">$99.99</s>&nbsp; <b>$18.99</b>/mo · cancel anytime</div>
  <!-- pricing (landing only): anchor $99.99/mo struck -> early-bird $18.99/mo -->
</div>
""", unsafe_allow_html=True)

st.write("")
c1, c2 = st.columns(2)
if CHECKOUT_URL:
    c1.link_button("Subscribe — lock in $18.99/mo", CHECKOUT_URL,
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
st.write("")

# ---- WHY UNDERLISTED (content section — no selling logic) ----
# The frame: a home is the biggest purchase of your life.
st.markdown("""
<div class="frameband">
  <p>For most people, a home is the <b>biggest financial decision they'll ever make</b> —
  yet they decide on a gut feeling and a mortgage calculator.
  Underlisted gives you the full picture first.</p>
</div>
""", unsafe_allow_html=True)

st.write("")
st.markdown('<div class="section-eyebrow">Why Underlisted</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">The whole picture, in plain English</div>',
            unsafe_allow_html=True)
st.write("")

# Row 1 — three cards
w1, w2, w3 = st.columns(3)
w1.markdown(
    f"<div class='feat'><div class='num'>1</div>{ic('home',24,GOLD)}"
    "<h3>The biggest decision of your life</h3>"
    "<div class='muted'>You'll likely spend more on this than anything else you ever buy. "
    "We help you get it right — before you commit, not after.</div></div>",
    unsafe_allow_html=True)
w2.markdown(
    f"<div class='feat'><div class='num'>2</div>{ic('score',24,GOLD)}"
    "<h3>Is it a good deal?</h3>"
    "<div class='muted'>One plain-English <b>Deal Score, 0–100</b>. Green means good. "
    "No spreadsheets, no jargon — just an honest answer on the price.</div></div>",
    unsafe_allow_html=True)
w3.markdown(
    f"<div class='feat'><div class='num'>3</div>{ic('wallet',24,GOLD)}"
    "<h3>Can you actually afford it?</h3>"
    "<div class='muted'>See your <b>true monthly cost</b>, the <b>real cash</b> you'll need "
    "up front, and <b>how much you'd have left over</b> each month. The question no one "
    "else answers.</div></div>",
    unsafe_allow_html=True)

st.write("")
# Row 2 — two cards, centered under the three above
sp1, w4, w5, sp2 = st.columns([0.5, 1, 1, 0.5])
w4.markdown(
    f"<div class='feat'><div class='num'>4</div>{ic('shield',24,GOLD)}"
    "<h3>What could surprise you?</h3>"
    "<div class='muted'>We flag <b>fire &amp; flood insurance risk</b> and other "
    "budget-busters <i>before</i> they cost you thousands.</div></div>",
    unsafe_allow_html=True)
w5.markdown(
    f"<div class='feat'><div class='num'>5</div>{ic('star',24,GOLD)}"
    "<h3>Built for you — not investors</h3>"
    "<div class='muted'>Other tools are made for flippers and full of jargon "
    "(cap rate, IRR, BRRRR). We just tell you, simply, in words anyone can "
    "understand.</div></div>",
    unsafe_allow_html=True)

st.write("")
st.write("")
# The bold contrast line
st.markdown("""
<div class="contrast">
  <span class="dim">Zillow shows you homes. Investor tools make you do the math.</span>
  <span class="lead">Underlisted just tells you which homes are
  <b>actually good</b> — and whether you can afford them.</span>
</div>
""", unsafe_allow_html=True)

st.write("")
# Trust strip
st.markdown("""
<div class="trust">
  <span>Nationwide</span><span class="dot">·</span>
  <span>Licensed data (no scraping)</span><span class="dot">·</span>
  <span>Fire/flood risk built in</span><span class="dot">·</span>
  <span>Plain English, always</span>
</div>
""", unsafe_allow_html=True)

st.write("")
st.write("")
st.markdown(
    "<div class='section-title' style='font-size:1.5rem'>Before the biggest purchase "
    "of your life — know the deal, the cost, and the risk.</div>",
    unsafe_allow_html=True)

st.write("")
st.markdown(f"""
<div class="note">
  <div class="seal tl">$</div>
  <div class="seal br">$</div>
  <div class="eyebrow">★ Founding-member rate ★</div>
  <div class="strike">$99.99/mo</div>
  <div class="now"><span class="gold-foil">$18.99</span><span class="per">/mo</span></div>
  <div class="eyebrow" style="letter-spacing:1.5px">Early-bird price — locked in for life</div>
  <div style="margin-top:12px">{ic('check',18,CORAL)} 3-day free trial &nbsp;
     {ic('check',18,CORAL)} cancel anytime &nbsp;
     {ic('check',18,CORAL)} Nationwide listings</div>
  <div class="serial">No. UL&mdash;001899 · FOUNDING MEMBER · UNDERLISTED</div>
</div>
""", unsafe_allow_html=True)

st.write("")
if CHECKOUT_URL:
    st.link_button("Subscribe — lock in $18.99/mo  →", CHECKOUT_URL,
                   type="primary", use_container_width=True)
else:
    if st.button("Start 3-day free trial  →", type="primary", use_container_width=True):
        st.switch_page("pages/0_Browse_Deals.py")

st.divider()
st.caption("Estimates only — a screening tool, not investment advice or a loan "
           "offer. Fair Housing: scoring never uses demographic or 'neighborhood "
           "quality' signals. Now nationwide across the U.S.")

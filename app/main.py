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
  /* ---- Decorative gold-coin cursor (inline SVG, ~30px, hotspot centered) ----
     A small embossed gold coin: radial gold face, milled rim, raised "$".
     Applied app-wide as the default. Clickable things keep the same coin but
     we DON'T override text inputs/areas -> they keep a real text caret so
     typing/targeting stays usable. Falls back to auto if data URI unsupported. */
  .stApp {{
      cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='30' height='30' viewBox='0 0 30 30'%3E%3Cdefs%3E%3CradialGradient id='g' cx='38%25' cy='32%25' r='75%25'%3E%3Cstop offset='0%25' stop-color='%23FFF6C8'/%3E%3Cstop offset='28%25' stop-color='%23F4DE8A'/%3E%3Cstop offset='55%25' stop-color='%23E8B948'/%3E%3Cstop offset='80%25' stop-color='%23D9A93A'/%3E%3Cstop offset='100%25' stop-color='%23B8860B'/%3E%3C/radialGradient%3E%3C/defs%3E%3Ccircle cx='15' cy='15' r='13.5' fill='url(%23g)' stroke='%23B8860B' stroke-width='1.5'/%3E%3Ccircle cx='15' cy='15' r='10.5' fill='none' stroke='%237A5407' stroke-opacity='0.35' stroke-width='0.8' stroke-dasharray='1.4 1.4'/%3E%3Ctext x='15' y='20' font-family='Georgia,serif' font-size='15' font-weight='bold' fill='%237A5407' text-anchor='middle'%3E%24%3C/text%3E%3C/svg%3E") 15 15, auto;
  }}
  /* Clickable controls keep the coin (signals "spend / act") */
  .stApp a, .stApp button, .stButton > button, .stLinkButton > a,
  .stDownloadButton > button, .stApp [role="button"], .stApp summary,
  label, .stCheckbox, .stRadio {{
      cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='30' height='30' viewBox='0 0 30 30'%3E%3Cdefs%3E%3CradialGradient id='g' cx='38%25' cy='32%25' r='75%25'%3E%3Cstop offset='0%25' stop-color='%23FFF6C8'/%3E%3Cstop offset='28%25' stop-color='%23F4DE8A'/%3E%3Cstop offset='55%25' stop-color='%23E8B948'/%3E%3Cstop offset='80%25' stop-color='%23D9A93A'/%3E%3Cstop offset='100%25' stop-color='%23B8860B'/%3E%3C/radialGradient%3E%3C/defs%3E%3Ccircle cx='15' cy='15' r='13.5' fill='url(%23g)' stroke='%23B8860B' stroke-width='1.5'/%3E%3Ccircle cx='15' cy='15' r='10.5' fill='none' stroke='%237A5407' stroke-opacity='0.35' stroke-width='0.8' stroke-dasharray='1.4 1.4'/%3E%3Ctext x='15' y='20' font-family='Georgia,serif' font-size='15' font-weight='bold' fill='%237A5407' text-anchor='middle'%3E%24%3C/text%3E%3C/svg%3E") 15 15, pointer !important;
  }}
  /* Text fields keep a real caret so they stay easy to target/type in */
  .stApp input[type="text"], .stApp input[type="number"], .stApp input[type="email"],
  .stApp input[type="search"], .stApp input[type="password"], .stApp textarea {{
      cursor: text !important;
  }}
  /* Deep luxury-green base on a soft radial vignette (lighter emerald center ->
     darker toward edges) for depth. Currency-pattern overlays removed — the
     background is now clean green so content reads calm and premium. */
  .stApp {{
      background-color:#0B3D2E;
      background-image:
        radial-gradient(140% 120% at 50% 18%, #0F4A37 0%, #0B3D2E 46%, #082C20 100%);
      background-size: cover;
      background-position: center;
      background-attachment: fixed;
  }}
  /* Off-white text on green */
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
      background: linear-gradient(180deg, rgba(6,34,25,.32) 0%, rgba(7,40,29,.58) 55%, rgba(5,28,20,.94) 100%);
  }}
  .hero {{ border:1px solid rgba(232,185,72,.30); }}
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

  /* ---- Feature cards (dark-emerald glass) ---- */
  .feat {{ background:linear-gradient(180deg,#0E4A37 0%,#082C20 100%);
      border:1px solid rgba(232,185,72,.22); border-radius:18px;
      padding:22px; height:100%; box-shadow:0 10px 26px rgba(0,0,0,.45);
      transition:transform .15s ease, box-shadow .15s ease, border-color .15s ease; }}
  .feat:hover {{ transform:translateY(-3px); border-color:rgba(232,185,72,.50);
      box-shadow:0 16px 34px rgba(0,0,0,.55); }}
  .feat h3 {{ margin:.5rem 0 .3rem; font-size:1.15rem; color:#F5F5F7; }}
  .feat .muted {{ font-size:.98rem; color:#A1A1A6; }}

  /* ---- "Why Us" section pieces ---- */
  /* The frame band: a calm, premium pull-quote */
  .frameband {{
      margin: 6px auto 4px; max-width: 40rem; text-align:center;
      padding: 22px 26px; border-radius:16px;
      background: linear-gradient(180deg, rgba(232,185,72,.10) 0%, rgba(8,44,32,.30) 100%);
      border:1px solid rgba(232,185,72,.26);
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
      background: linear-gradient(180deg,#0E4A37 0%,#072419 100%);
      border:1px solid rgba(232,185,72,.34);
      box-shadow:0 16px 40px rgba(0,0,0,.5);
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
  /* Primary CTA = "act now": gold face kept, wrapped in a premium red urgency
     ring + soft pulsing glow so it reads as the urgent action. Visual only —
     no text/behavior/pricing change. */
  .stButton > button[kind="primary"], .stLinkButton > a[kind="primary"] {{
      border:2px solid #D7263D !important;
      box-shadow:0 8px 20px rgba(201,154,46,.35),
                 0 0 0 4px rgba(215,38,61,.20),
                 0 10px 28px rgba(165,20,39,.45) !important;
      animation: ctaglow 2.8s ease-in-out infinite;
  }}
  .stButton > button[kind="primary"]:hover, .stLinkButton > a[kind="primary"]:hover {{
      border-color:#A51427 !important;
  }}
  @keyframes ctaglow {{
      0%,100% {{ box-shadow:0 8px 20px rgba(201,154,46,.35),
                            0 0 0 4px rgba(215,38,61,.18),
                            0 10px 28px rgba(165,20,39,.38); }}
      50%     {{ box-shadow:0 8px 20px rgba(201,154,46,.35),
                            0 0 0 5px rgba(215,38,61,.34),
                            0 12px 34px rgba(215,38,61,.55); }}
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

  /* ---- Urgency / scarcity: a premium red on top of the green+gold ----
     Truthful scarcity only (limited early access + founding price). Red is an
     ACCENT, never the page. Strong-but-luxe red #D7263D / deeper #A51427. */
  .urgency {{
      display:inline-flex; align-items:center; gap:8px;
      margin-top:16px; padding:9px 18px; border-radius:999px;
      font-weight:800; font-size:.98rem; letter-spacing:.2px; color:#FFF1F2;
      background:linear-gradient(135deg,#D7263D 0%,#A51427 100%);
      border:1px solid rgba(255,210,214,.45);
      box-shadow:0 8px 22px rgba(165,20,39,.40), inset 0 1px 0 rgba(255,255,255,.25);
      animation: urgpulse 2.8s ease-in-out infinite;
  }}
  .urgency .dotred {{
      width:9px; height:9px; border-radius:50%; background:#FFE2E5;
      box-shadow:0 0 0 0 rgba(255,226,229,.7);
      animation: urgblink 2.8s ease-in-out infinite;
  }}
  @keyframes urgpulse {{
      0%,100% {{ box-shadow:0 8px 22px rgba(165,20,39,.40), inset 0 1px 0 rgba(255,255,255,.25); }}
      50%     {{ box-shadow:0 8px 30px rgba(215,38,61,.70), inset 0 1px 0 rgba(255,255,255,.25); }}
  }}
  @keyframes urgblink {{
      0%,100% {{ opacity:.55; box-shadow:0 0 0 0 rgba(255,226,229,.0); }}
      50%     {{ opacity:1;   box-shadow:0 0 0 4px rgba(255,226,229,.25); }}
  }}
  /* A thin red scarcity ribbon used near the founding-member card */
  .scarcity-ribbon {{
      text-align:center; margin: 0 auto 10px; max-width: 42rem;
      font-weight:800; font-size:.95rem; letter-spacing:.3px; color:#FFD7DC;
      padding:8px 16px; border-radius:12px;
      background:linear-gradient(180deg, rgba(215,38,61,.20) 0%, rgba(165,20,39,.12) 100%);
      border:1px solid rgba(215,38,61,.55);
  }}

  /* Respect reduced-motion: hold everything still, no sweeps/pulses */
  @media (prefers-reduced-motion: reduce) {{
      .gold-foil, .urgency, .urgency .dotred,
      .stButton > button[kind="primary"], .stLinkButton > a[kind="primary"] {{
          animation: none !important;
      }}
  }}
  /* Mobile: let content breathe */
  @media (max-width: 640px) {{
      .urgency {{ font-size:.9rem; padding:8px 14px; }}
  }}

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
  <div><span class="urgency"><span class="dotred"></span>⏳ Early access is limited — founding price ends before it rises to $44.99/mo</span></div>
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
# Red scarcity ribbon above the founding-member card (truthful: founding price
# rising to $44.99, limited early access — no fake counters/timers).
st.markdown("""
<div class="scarcity-ribbon">🔒 Founding price won't last — it's set to rise to $44.99/mo. Lock yours in now.</div>
""", unsafe_allow_html=True)
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

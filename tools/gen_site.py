"""
Static-site generator — the SEO + PR engine. (Ivory & Gold rebuild, Juliet.)

Reads our cached, scored listings (deal score, value discount, FEMA risk, FHFA
price trend) and writes plain STATIC HTML you can host anywhere:
  * site/index.html                  — the brand homepage (Deal Dial hero)
  * site/deals-in-<city>.html        — "Best home deals in <City>" (one per city)
  * site/report-underpriced.html     — "Most underpriced homes right now" (PR asset)
  * site/learn.html                  — free plain-English glossary (teaching page)
  * site/thanks.html                 — waitlist redirect / thank-you page

Why static HTML (not a Streamlit page): search engines index static pages with real
URLs + titles; a Streamlit app does not rank. Host these on any web host/CDN and they
become millions of search entry points over time. FREE to generate (no API calls).

──────────────────────────────────────────────────────────────────────────────
BRAND — "Ivory & Gold" (owner-approved 2026-06-18). Blueprint:
design_preview/site_cormorant_light.html.
  • Type: Cormorant Garamond (500–600) for headlines / section titles / big numbers
    and the gold *italic* accent word; Inter for ALL body, labels, fine print, money.
  • Palette: warm ivory #FBF7EF canvas · warm ink #1E1A16 text · refined gold #B8893A
    accent + hairline rules. Deal-score meaning colours readable on cream:
    good green #1A8F5A · amber #B5780A · red #C0392B.
  • Deal Dial with a gold halo is the hero signature (shared with the app).
EVERY page wears this same family: shared header/footer/nav, one <style>.

HARD RULES (do not break):
  • The Netlify `waitlist` <form> markup (name/method/data-netlify/honeypot/hidden
    form-name/bot-field/action/email-required) is preserved EXACTLY — appearance only.
  • No selling/Payhip logic lives here; never add or change pricing/checkout behaviour.
  • The Kling hero (site/assets/hero.mp4) keeps working — designed so the video OR an
    elegant still both read well behind the scrim.
  • Mobile-first; strong contrast (ink on ivory; gold is accent, never load-bearing text).

Run:  .venv\\Scripts\\python.exe tools\\gen_site.py
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Owner's Kling animation (the 3D USA map with glossy pins) — web-compressed to
# ~561KB + a 378KB JPG poster, shipped as the website hero. (Originals live at the
# project root; the compressed web assets live in design_preview/assets.)
HERO_VIDEO_SRC = ROOT / "design_preview" / "assets" / "hero.mp4"
HERO_POSTER_SRC = ROOT / "design_preview" / "assets" / "hero_usa_map.jpg"

# The dark cinematic homepage hero photo (real photoreal dusk house, Nano Banana).
# Lives in the share-hero preview; shipped to site/assets/hero_house.jpg at build.
HERO_HOUSE_SRC = ROOT / "design_preview" / "share_hero" / "assets" / "hero_house.jpg"

# Cinematic homepage hero VIDEO — a warm couple at their new home, golden hour.
# Trimmed + web-compressed (2.2MB, muted, 6s, 1280x720, +faststart) with a poster
# still for reduced-motion / slow-connection fallback. Shipped to site/assets/.
HERO_COUPLE_VIDEO_SRC = ROOT / "design_preview" / "share_hero" / "assets" / "hero_couple.mp4"
HERO_COUPLE_POSTER_SRC = ROOT / "design_preview" / "share_hero" / "assets" / "hero_couple_poster.jpg"

from app import sample_data            # noqa: E402  (no streamlit imported here)
from src.data_sources import market    # noqa: E402
from src import glossary                # noqa: E402  (shared term wording: app + site)

OUT = ROOT / "site"

# ── "Ivory & Gold" palette — ONE place per surface (mirrors the blueprint) ──
IVORY, IVORY2, SURFACE, SURFACE2 = "#FBF7EF", "#F6F0E4", "#FFFDF8", "#FCF8F0"
INK, INK_SOFT, MUTED, FAINT = "#1E1A16", "#3A332B", "#6B635A", "#938A7E"
# ── BRAND ACCENTS — recolored to match the new logo (forest GREEN + brick RED),
#    replacing the old "Ivory & Gold" gold (2026-06-21, Juliet). The CSS token
#    NAMES stay --gold* (referenced page-wide) but their VALUES are now the logo's
#    forest-green family, so the whole ivory body recolors from ONE place. Tuned to
#    stay readable on cream: --gold-2 is the deepest (body-text/links), --gold the
#    brand mid, --gold-bright the fill/on-dark green, --gold-deep the darkest.
GOLD, GOLD2, GOLD_BRIGHT, GOLD_DEEP = "#1A6A48", "#14533A", "#1F7A53", "#0E3A2A"
GOOD, OKAY, WEAK = "#1A8F5A", "#B5780A", "#C0392B"   # deal-score MEANING (readable on cream)
# Brick RED from the logo's roof — the secondary brand accent, reserved for the
# most load-bearing emphasis (not garish). Distinct from the brighter deal-score
# "walk away" WEAK red so the two never get confused.
BRICK_RED, BRICK_RED_DEEP = "#A8201C", "#8E1B18"

# ── LIVE DEAL COUNT — shown as "X homes tracked nationwide" on the homepage ──
# Honest, easy-to-update fallback. The real number lives in our CLOUD Postgres
# (the live worker has loaded ~6,959 real listings); that DB is NOT reachable from
# a plain build sandbox, so we keep a hand-set constant here AND try the DB at
# build time — whichever real count we can read wins (see live_deal_count()).
#
#   • To bump it by hand: change HOMES_TRACKED_FALLBACK below to the latest count
#     shown in Admin/Usage, then re-run gen_site.py.
#   • NOTE: the ~5,513 FREE HUD/USDA foreclosures are NOT in this number yet — they
#     join the count automatically once a worker run ingests them into `listings`.
HOMES_TRACKED_FALLBACK = 6_959   # last verified live count (2026-06-15 worker run)
ROUND_TO = 100                   # display rounds DOWN to a clean, defensible figure

# Live Streamlit app (the real product). The static site can't compute deals, so
# the "See deals near you" box ROUTES the visitor to the app's Browse Deals feed,
# carrying their typed ZIP/city as a query param (forward-compatible; harmless if
# the app doesn't read it yet). Source: CLAUDE.md §2.
APP_URL = "https://underlisted-gidalbx5x5vlaeuvqncwpp.streamlit.app"
APP_BROWSE_URL = f"{APP_URL}/Browse_Deals"


def live_deal_count() -> int:
    """Best real count of homes we've scored. Reads the cache if reachable at
    build time; otherwise falls back to the hand-set constant above. Always
    rounds DOWN to a clean number so the headline stat is never overstated."""
    n = HOMES_TRACKED_FALLBACK
    try:
        from src.cache import db  # lazy — no Streamlit, no billable calls
        with db.connect() as conn:
            got = conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
            # Trust the DB only when it has MORE than our verified cloud fallback.
            # (Offline builds read the tiny LOCAL dev sqlite, which would otherwise
            # understate the real cloud count of ~6,959. Whichever is larger wins.)
            if got and int(got) > n:
                n = int(got)
    except Exception:
        pass  # sandbox / no DB → keep the honest fallback
    return (n // ROUND_TO) * ROUND_TO if n >= ROUND_TO else n


def count_label(n: int) -> str:
    """Human, comma-grouped count, e.g. 6,900 -> '6,900+'."""
    return f"{n:,}+"


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-") or "area"


def money(v) -> str:
    return f"${v:,.0f}" if isinstance(v, (int, float)) and v else "—"


def _discount(row):
    v = row["value"].avm
    p = row["listing"].list_price
    if v and p:
        return (v - p) / v * 100
    return None


# ──────────────────────────────────────────────────────────────────────────────
# THE GOLD ICON FAMILY — one cohesive, best-class luxury line set (Juliet, 2026-06-20).
#
# Design system for the set (so any new icon stays in the family):
#   • Canvas: 24×24 viewBox, drawn inside a ~3–21 "live area" (optical margin).
#   • Style: thin line icons, stroke-width 1.5, round caps + round joins — the
#     thinner weight reads luxe/editorial, not chunky/generic-app.
#   • Each glyph is optically CENTERED and balanced; solid accents (a coin's
#     centre, a keyhole) use a tiny filled dot, never a heavy blob.
#   • MEANING first: a house is a house, a flame is fire-risk, water is flood-risk,
#     a coin is cash, a dial is the deal score. Obvious at a glance, always.
# Rendered in brand gold (#B8893A / #9C6F22) by the page's CSS `color`.
# ──────────────────────────────────────────────────────────────────────────────
ICON = {
    # — house: clean gabled roof + walls + a single slender door (the brand mark) —
    "home": '<path d="M3.6 11.3 12 4.2l8.4 7.1"/><path d="M5.4 9.9V20h13.2V9.9"/><path d="M10.2 20v-5.1h3.6V20"/>',
    # — navigation —
    "arrow": '<path d="M4.5 12h15"/><path d="M13 5.5 19.5 12 13 18.5"/>',
    "check": '<path d="M20 6.5 9.2 17.3 4 12.1"/>',
    # — insurance umbrella: a shield with a calm tick of protection inside —
    "shield": '<path d="M12 3.2 19 5.6v5.2c0 4.7-3 7.9-7 9.4-4-1.5-7-4.7-7-9.4V5.6z"/><path d="M9.2 11.6 11.3 13.7 15 9.6"/>',
    # — FIRE risk: a clean teardrop flame with an inner curl (insurance warning) —
    "fire": '<path d="M12.4 3.3c-.3 2.6-1.5 3.9-2.9 5.2-1.6 1.5-3 3.3-3 5.9a5.5 5.5 0 0 0 11 0c0-2-.8-3.4-1.8-4.6.1 1.6-.6 2.4-1.6 2.6.8-2.6-.2-5.4-1.7-6.4 0 1.7-.6 2.5-1.5 3.2.8-2.2.6-4.3 1.5-5.9z"/>',
    # — FLOOD risk: two calm water ripples (paired with fire on the risk panel) —
    "wave": '<path d="M3.5 14.4c1.8-2 3.6-2 5.4 0s3.6 2 5.4 0 3.6-2 5.4 0"/><path d="M3.5 9.4c1.8-2 3.6-2 5.4 0s3.6 2 5.4 0 3.6-2 5.4 0"/>',
    # — bank / true monthly cost: a small classical building with columns —
    "bank": '<path d="M12 3.4 20.5 7.6H3.5z"/><path d="M3.5 10.4h17"/><path d="M6.6 10.4V17M10.2 10.4V17M13.8 10.4V17M17.4 10.4V17"/><path d="M3.2 20.4h17.6"/>',
    # — coin / cash: a clean circle + a balanced dollar S —
    "coin": '<circle cx="12" cy="12" r="8.4"/><path d="M12 6.6v10.8"/><path d="M14.7 9.1a2.7 2.5 0 0 0-2.7-1.6 2.6 2.4 0 0 0 0 4.8 2.6 2.4 0 0 1 0 4.8 2.7 2.5 0 0 1-2.7-1.6"/>',
    # — trend up / "can I afford it" upside —
    "up": '<path d="M12 19.5V7.5"/><path d="M6.8 12.7 12 7.4l5.2 5.3"/>',
    # — deal gauge / score dial: arc + needle + hub —
    "gauge": '<path d="M4 13.5a8 8 0 0 1 16 0"/><path d="M12 13.5 17 9.2"/><circle cx="12" cy="13.5" r="1.2" fill="currentColor" stroke="none"/>',
    # — price tag (below value) —
    "tag": '<path d="M20.2 13.1 13.1 20.2a1.9 1.9 0 0 1-2.7 0l-6.8-6.8a1.9 1.9 0 0 1-.6-1.3V4.6a1.9 1.9 0 0 1 1.9-1.9h7.5a1.9 1.9 0 0 1 1.3.6l6.8 6.8a1.9 1.9 0 0 1 0 2.7z"/><circle cx="8" cy="8" r="1.15" fill="currentColor" stroke="none"/>',
    # — calculator / payoff time —
    "cal": '<rect x="4.5" y="3.5" width="15" height="17" rx="2.4"/><path d="M4.5 8.5h15"/><path d="M8 12h2M14 12h2M8 16h2M14 16h2"/>',
    # — open book / learn —
    "book": '<path d="M12 6.4C10.5 5.2 8.5 4.7 5 5v12c3.5-.3 5.5.2 7 1.4 1.5-1.2 3.5-1.7 7-1.4V5c-3.5-.3-5.5.2-7 1.4z"/><path d="M12 6.4V18.4"/>',
    # — padlock: refined shackle + a single elegant keyhole —
    "lock": '<rect x="4.8" y="10.6" width="14.4" height="9.8" rx="2.6"/><path d="M8 10.6V7.8a4 4 0 0 1 8 0v2.8"/><path d="M12 14.4v2.6"/><circle cx="12" cy="14.4" r="1.15" fill="currentColor" stroke="none"/>',
    # — sparkle: a refined 4-point shine with a tiny secondary glint —
    "sparkle": '<path d="M12 3.5c.3 3.4 1.6 4.7 5 5-3.4.3-4.7 1.6-5 5-.3-3.4-1.6-4.7-5-5 3.4-.3 4.7-1.6 5-5z"/><path d="M18.6 14.4c.15 1.4.7 1.95 2.1 2.1-1.4.15-1.95.7-2.1 2.1-.15-1.4-.7-1.95-2.1-2.1 1.4-.15 1.95-.7 2.1-2.1z"/>',
}


# MEANING colours — the owner finds all-gold icons hard to scan. Functional icons
# read by meaning; GOLD stays the luxury/section-header accent only (Juliet, 2026-06-20).
#   GREEN = the deal / good / savings / score / below-value / foreclosures-found
#   RED   = warnings (wildfire, flood, over-budget)
#   BLUE  = the money tools (true cost, cash needed, afford check, calculators)
#   GOLD  = accents, section-title eyebrows, dividers (the DEFAULT — pass no tone)
TONE_COLOR = {
    "good": GOOD,          # green  #1A8F5A
    "green": GOOD,
    "warn": WEAK,          # red    #C0392B
    "red": WEAK,
    "money": "#2C6FB0",    # blue (matches the value-dashboard blue lane)
    "blue": "#2C6FB0",
    "gold": GOLD,          # explicit gold (same as default)
}


def svg(name: str, *, w: int = 18, cls: str = "", tone: str = "") -> str:
    """A stroked inline SVG from the icon family.

    The whole family is thin-line (stroke-width 1.5), round-capped, 24×24 — a
    cohesive set. Colour comes from `currentColor`: by DEFAULT it inherits the
    surrounding CSS (gold in headers/dividers). Pass `tone=` ("good"/green,
    "warn"/red, "money"/blue) to paint a FUNCTIONAL icon by meaning so it reads
    instantly — without affecting any gold caller (which simply omits `tone`).
    """
    c = f" class='{cls}'" if cls else ""
    s = (f"<svg{c} width='{w}' height='{w}' viewBox='0 0 24 24' fill='none' "
         f"stroke='currentColor' stroke-width='1.5' stroke-linecap='round' "
         f"stroke-linejoin='round'>{ICON[name]}</svg>")
    color = TONE_COLOR.get(tone)
    if color:
        # an inline-flex span sets `color` so the SVG's currentColor follows the
        # MEANING, never the inherited gold. Scoped, self-contained, collision-free.
        return f"<span style='display:inline-flex;color:{color}'>{s}</span>"
    return s


def free_badge(*, big: bool = False) -> str:
    """ONE consistent, classy 'FREE' badge reused everywhere we give value away.
    A gold-ringed cream pill with a small good-green dot — reads as a quiet seal of
    'this part costs nothing', building goodwill before the subscribe ask. The
    `big` variant is used on page heroes; the default is for cards / strips."""
    cls = "freebadge big" if big else "freebadge"
    return (f"<span class='{cls}'><span class='fdot'></span>FREE</span>")


# ──────────────────────────────────────────────────────────────────────────────
# ONE shared stylesheet — the whole site is this family. Lifted from the approved
# blueprint (design_preview/site_cormorant_light.html) and extended to cover the
# city / report / learn page furniture (cards, glossary, hero-video scrim).
# ──────────────────────────────────────────────────────────────────────────────
FONTS = (
    "<link rel='preconnect' href='https://fonts.googleapis.com'>"
    "<link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>"
    "<link href='https://fonts.googleapis.com/css2?family=Cormorant+Garamond:"
    "ital,wght@0,500;0,600;1,500;1,600&family=Inter:wght@400;500;600;700&display=swap' "
    "rel='stylesheet'>"
)

CSS = f"""
<style>
 :root{{
   --ivory:{IVORY}; --ivory-2:{IVORY2}; --surface:{SURFACE}; --surface-2:{SURFACE2};
   --ink:{INK}; --ink-soft:{INK_SOFT}; --muted:{MUTED}; --faint:{FAINT};
   --hair:rgba(26,106,72,.26); --hair-soft:rgba(30,26,22,.10);
   --gold:{GOLD}; --gold-2:{GOLD2}; --gold-bright:{GOLD_BRIGHT}; --gold-deep:{GOLD_DEEP};
   --good:{GOOD}; --good-soft:rgba(26,143,90,.12);
   --okay:{OKAY}; --okay-soft:rgba(181,120,10,.13);
   --weak:{WEAK}; --weak-soft:rgba(192,57,43,.11);
   /* BRICK RED from the new logo's roof — the secondary brand accent, reserved for
      tasteful editorial / load-bearing emphasis only. Distinct from the brighter
      "walk away" deal-score red so the two never get confused. */
   --deep-red:{BRICK_RED};
   --deep-red-2:{BRICK_RED_DEEP};
   --r:16px; --r-lg:22px;
   --shadow:0 30px 64px -32px rgba(60,44,20,.30);
   --shadow-sm:0 14px 30px -18px rgba(60,44,20,.26);
   /* ── UNIFIED CARD SYSTEM (one designed surface across map tiles + tool cards) ──
      every card shares the same radius, hairline, soft elegant shadow, and the same
      deeper shadow on hover. Hover-lift is a single shared transform/duration. */
   --r-card:19px;
   --card-shadow:0 18px 44px -26px rgba(60,44,20,.32), 0 2px 8px -4px rgba(60,44,20,.14);
   --card-shadow-hover:0 30px 60px -28px rgba(60,44,20,.40), 0 4px 12px -5px rgba(60,44,20,.16);
   --lift:translateY(-3px);
   --ease-card:cubic-bezier(.22,.61,.36,1);
   /* modular vertical-rhythm scale for section padding (top/bottom) */
   --sp-1:clamp(40px,6vw,58px);   /* tight  */
   --sp-2:clamp(58px,8vw,82px);   /* normal */
   --sp-3:clamp(80px,11vw,118px); /* roomy  */
   --maxw:1140px;
 }}
 *{{box-sizing:border-box;-webkit-tap-highlight-color:transparent}}
 /* accessibility: a clean gold focus ring on every interactive element (keyboard
    users see exactly where they are; mouse users don't get a ring on click) */
 a:focus-visible,button:focus-visible,input:focus-visible,
 [tabindex]:focus-visible,.tool:focus-visible{{outline:2px solid var(--gold);
   outline-offset:3px;border-radius:6px}}
 /* respect reduced-motion: no hover-lift transforms, no smooth-scroll for those users */
 @media(prefers-reduced-motion:reduce){{
   html{{scroll-behavior:auto}}
   *{{transition-duration:.001ms!important;animation-duration:.001ms!important}}
 }}
 html{{scroll-behavior:smooth}}
 body{{margin:0;font-family:"Inter",-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
   color:var(--ink);line-height:1.6;-webkit-font-smoothing:antialiased;
   background:
     radial-gradient(1100px 620px at 84% -8%, rgba(26,106,72,.10), transparent 58%),
     radial-gradient(1000px 700px at 8% 4%, rgba(26,106,72,.06), transparent 56%),
     var(--ivory);}}
 .wrap{{max-width:var(--maxw);margin:0 auto;padding:0 24px}}
 @media(max-width:560px){{.wrap{{padding:0 18px}}}}
 .tnum{{font-feature-settings:"tnum" 1,"lnum" 1;font-variant-numeric:tabular-nums}}
 h1,h2,h3,h4,.display{{font-family:"Cormorant Garamond",Georgia,serif;color:var(--ink)}}
 em{{font-style:italic}}
 a{{color:var(--gold-2)}}

 /* ===== HEADER / NAV ===== */
 header{{position:sticky;top:0;z-index:50;background:rgba(251,247,239,.85);
   backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
   border-bottom:1px solid var(--hair)}}
 .bar{{display:flex;align-items:center;gap:16px;height:68px}}
 .logo{{display:flex;align-items:center;gap:11px;text-decoration:none;color:var(--ink)}}
 .logo .mark{{width:38px;height:38px;border-radius:11px;display:grid;place-items:center;
   background:linear-gradient(150deg,var(--gold-bright),var(--gold-deep));
   box-shadow:0 8px 18px -8px rgba(14,58,42,.5), inset 0 1px 0 rgba(255,255,255,.45)}}
 .logo .mark svg{{width:21px;height:21px;color:#FFFBF1}}
 .logo b{{font-family:"Inter";font-weight:700;font-size:1.16rem;letter-spacing:-.01em;color:var(--ink)}}
 .navlinks{{margin-left:auto;display:flex;align-items:center;gap:30px}}
 .navlinks a{{font-family:"Inter";text-decoration:none;color:var(--muted);font-weight:500;font-size:.93rem;transition:color .2s}}
 .navlinks a:hover,.navlinks a.here{{color:var(--ink)}}
 .navlinks a.here{{border-bottom:2px solid var(--gold);padding-bottom:3px}}
 .btn-top{{padding:10px 20px !important;border-radius:11px;color:#FFFBF1 !important;font-weight:600;
   background:linear-gradient(150deg,var(--gold-bright),var(--gold));
   box-shadow:0 12px 24px -12px rgba(14,58,42,.5)}}
 .btn-top:hover{{color:#FFFBF1 !important}}
 @media(max-width:760px){{.navlinks a:not(.btn-top){{display:none}}}}

 .rule{{height:1px;background:linear-gradient(90deg,transparent,var(--hair-soft) 50%,transparent)}}
 .rule.gold{{background:linear-gradient(90deg,transparent,rgba(26,106,72,.55) 50%,transparent)}}

 /* ===== buttons ===== */
 /* PRIMARY (gold) — one consistent treatment shared with .zipform button + .wl
    button: gold gradient, soft warm shadow, a 2px lift that deepens on hover and
    a gentle press on :active. SECONDARY (.btn-line / ghost) is the calm outline. */
 .btn-fill{{font-family:"Inter";display:inline-flex;align-items:center;gap:9px;text-decoration:none;
   padding:15px 28px;border-radius:13px;font-weight:600;font-size:1rem;color:#FFFBF1;
   background:linear-gradient(150deg,var(--gold-bright),var(--gold) 78%);
   box-shadow:0 18px 34px -16px rgba(14,58,42,.55), inset 0 1px 0 rgba(255,255,255,.4);
   transition:transform .18s var(--ease-card),box-shadow .18s var(--ease-card)}}
 .btn-fill:hover{{transform:translateY(-2px);box-shadow:0 24px 42px -16px rgba(14,58,42,.6), inset 0 1px 0 rgba(255,255,255,.45)}}
 .btn-fill:active{{transform:translateY(-1px) scale(.99)}}
 @media(prefers-reduced-motion:reduce){{.btn-fill:hover,.btn-fill:active{{transform:none}}}}
 .btn-fill svg{{width:18px;height:18px}}
 .btn-line{{font-family:"Inter";display:inline-flex;align-items:center;gap:8px;text-decoration:none;
   padding:15px 24px;border-radius:13px;font-weight:600;font-size:1rem;color:var(--ink);
   border:1px solid var(--hair);background:var(--surface);transition:border-color .2s,background .2s}}
 .btn-line:hover{{border-color:rgba(26,106,72,.6);background:var(--surface-2)}}
 .btn-line .ar{{color:var(--gold-2)}}

 /* ===== HERO (masthead) ===== */
 .masthead{{padding:74px 0 30px;text-align:center;position:relative}}
 .dateline{{display:inline-flex;align-items:center;gap:10px;font-family:"Inter";
   font-size:.72rem;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:var(--gold-2);
   border:1px solid var(--hair);border-radius:999px;padding:7px 16px;margin-bottom:26px;background:var(--surface)}}
 .dateline .dot{{width:7px;height:7px;border-radius:50%;background:var(--good);box-shadow:0 0 10px rgba(26,143,90,.7)}}
 .masthead h1{{font-weight:500;font-size:clamp(2.9rem,7vw,5.4rem);line-height:1.02;letter-spacing:.005em;margin:0 auto;max-width:14ch}}
 .masthead h1 em{{color:var(--gold);font-weight:600}}
 .lede{{font-family:"Inter";color:var(--muted);font-size:clamp(1.04rem,2.1vw,1.22rem);max-width:60ch;margin:24px auto 0;line-height:1.62}}
 .lede b{{color:var(--ink);font-weight:600}}
 .cta-row{{display:flex;flex-wrap:wrap;gap:14px;justify-content:center;margin-top:34px}}
 .trustrow{{display:flex;flex-wrap:wrap;gap:10px 26px;justify-content:center;margin-top:30px;
   font-family:"Inter";font-size:.86rem;color:var(--muted)}}
 .trustrow span{{display:inline-flex;align-items:center;gap:8px}}
 .trustrow svg{{width:16px;height:16px;color:var(--good)}}

 /* ===== HERO VIDEO (Kling map) — works as video OR elegant still ===== */
 .hero-video{{position:relative;overflow:hidden;border-radius:var(--r-lg);margin:46px auto 0;max-width:960px;
   min-height:300px;display:flex;align-items:flex-end;border:1px solid var(--hair);
   background:radial-gradient(120% 110% at 50% -10%, #FBF3E1, var(--surface) 72%);box-shadow:var(--shadow)}}
 .hero-video video{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0}}
 .hero-video .scrim{{position:absolute;inset:0;z-index:1;
   background:linear-gradient(180deg,rgba(20,14,4,.06) 0%,rgba(20,14,4,.30) 48%,rgba(20,14,4,.74) 100%)}}
 .hero-video .vcontent{{position:relative;z-index:2;padding:28px 30px;max-width:560px;color:#FFFDF8}}
 .hero-video .vcontent h3{{font-family:"Cormorant Garamond",serif;font-weight:600;color:#FFFDF8;
   font-size:clamp(1.5rem,4vw,2.2rem);line-height:1.1;margin:0;text-shadow:0 2px 16px rgba(0,0,0,.45)}}
 .hero-video .vcontent p{{font-family:"Inter";color:rgba(255,253,248,.92);margin:8px 0 0;font-size:.98rem;
   text-shadow:0 1px 10px rgba(0,0,0,.4)}}

 /* ===== THE DEAL DIAL — specimen plate ===== */
 .plate{{display:grid;grid-template-columns:1fr 1.15fr;gap:0;margin:54px auto 0;max-width:960px;
   background:var(--surface);border:1px solid var(--hair);border-radius:var(--r-lg);overflow:hidden;
   box-shadow:var(--shadow);text-align:left}}
 @media(max-width:780px){{.plate{{grid-template-columns:1fr}}}}
 .dial-side{{position:relative;padding:34px 30px 30px;display:flex;flex-direction:column;align-items:center;
   background:radial-gradient(120% 110% at 50% -4%, #FBF3E1, #FFFDF8 72%);border-right:1px solid var(--hair)}}
 @media(max-width:780px){{.dial-side{{border-right:0;border-bottom:1px solid var(--hair)}}}}
 .dial-side::before{{content:"";position:absolute;left:50%;top:40%;width:320px;height:320px;
   transform:translate(-50%,-50%);border-radius:50%;pointer-events:none;
   background:radial-gradient(circle, rgba(26,106,72,.20), rgba(26,106,72,.06) 46%, transparent 70%)}}
 .dial-side .tag{{position:relative;font-family:"Inter";font-size:.66rem;font-weight:600;
   letter-spacing:.22em;text-transform:uppercase;color:var(--gold-2);margin-bottom:16px}}
 .dial{{position:relative;width:240px;max-width:82%;margin:0 auto}}
 .dial svg{{width:100%;height:auto;filter:drop-shadow(0 6px 16px rgba(26,143,90,.18))}}
 .dial .center{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;padding-top:8%}}
 .dial .score{{font-family:"Cormorant Garamond",serif;font-weight:600;font-size:4.1rem;line-height:1;color:var(--ink)}}
 .dial .score .of{{font-family:"Inter";font-size:.95rem;color:var(--muted);font-weight:500}}
 .dial .verdict{{font-family:"Inter";margin-top:2px;font-weight:700;font-size:.78rem;letter-spacing:.14em;color:var(--good)}}
 .scale{{position:relative;display:flex;gap:16px;margin-top:18px;font-family:"Inter";font-size:.72rem;color:var(--muted)}}
 .scale span{{display:inline-flex;align-items:center;gap:6px}}
 .scale i{{width:9px;height:9px;border-radius:50%;display:inline-block}}
 .read-side{{padding:32px 32px 30px;background:var(--surface)}}
 .read-side .addr{{font-family:"Cormorant Garamond",serif;font-weight:600;font-size:1.85rem;line-height:1.1;color:var(--ink)}}
 .read-side .sub{{font-family:"Inter";color:var(--muted);font-size:.88rem;margin-top:3px}}
 .specrow{{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:14px 0;border-bottom:1px solid var(--hair-soft)}}
 .specrow:last-child{{border-bottom:0}}
 .specrow .k{{font-family:"Inter";display:inline-flex;align-items:center;gap:10px;color:var(--muted);font-size:.9rem}}
 .specrow .k svg{{width:17px;height:17px;color:var(--gold);opacity:.9}}
 .specrow .v{{font-family:"Cormorant Garamond",serif;font-weight:600;font-size:1.5rem;letter-spacing:.01em;color:var(--ink)}}
 .specrow .v.good{{color:var(--good)}} .specrow .v.okay{{color:var(--okay)}} .specrow .v.weak{{color:var(--weak)}}

 /* ===== SECTION FRAME ===== */
 /* one modular rhythm: every section breathes on --sp-2; stacked sections that
    would otherwise double up (e.g. free-tools -> waitlist) collapse the seam so
    there's no dead band between them. */
 .sec{{padding:var(--sp-2) 0}}
 /* the homepage free-tools section sits directly above the waitlist; their two
    full paddings used to stack into a dead band. Collapse the seam so it reads
    as ONE comfortable gap. (Scoped to these two IDs — other pages untouched.) */
 #early-access{{padding-top:0}}
 .sec-head{{text-align:center;max-width:760px;margin:0 auto 50px}}
 .kicker{{font-family:"Inter";font-size:.72rem;font-weight:600;letter-spacing:.22em;text-transform:uppercase;color:var(--gold-2);margin-bottom:16px}}
 .sec-head h2{{font-weight:500;font-size:clamp(2.1rem,4.6vw,3.3rem);line-height:1.08;letter-spacing:.005em;margin:0}}
 .sec-head h2 em{{color:var(--gold)}}
 .sec-head p{{font-family:"Inter";color:var(--muted);font-size:1.05rem;margin:16px auto 0;max-width:54ch}}

 /* ===== WHY — editorial numbered register ===== */
 .why-list{{max-width:880px;margin:0 auto}}
 .why-item{{display:grid;grid-template-columns:auto 50px 1fr auto;gap:20px 22px;align-items:start;
   padding:26px 6px;border-top:1px solid var(--hair-soft);transition:background .25s}}
 .why-item:last-child{{border-bottom:1px solid var(--hair-soft)}}
 .why-item:hover{{background:linear-gradient(90deg,rgba(26,106,72,.06),transparent 72%)}}
 @media(max-width:640px){{.why-item{{grid-template-columns:auto 1fr;gap:12px 16px}}}}
 .why-item .no{{font-family:"Cormorant Garamond",serif;font-style:italic;font-weight:600;font-size:1.9rem;color:var(--gold);line-height:1.1;padding-top:2px}}
 .why-item .ico{{width:50px;height:50px;border-radius:14px;flex:none;display:grid;place-items:center;
   background:linear-gradient(155deg,rgba(26,106,72,.16),rgba(26,106,72,.05));border:1px solid var(--hair)}}
 .why-item .ico svg{{width:25px;height:25px;color:var(--gold-2)}}
 @media(max-width:640px){{.why-item .ico{{display:none}}}}
 .why-item .txt h3{{font-weight:600;font-size:1.6rem;line-height:1.15;margin:0 0 5px;color:var(--ink)}}
 .why-item .txt p{{font-family:"Inter";color:var(--muted);font-size:.97rem;margin:0;max-width:54ch}}
 .why-item .seal{{align-self:center;font-family:"Inter";font-size:.72rem;font-weight:600;letter-spacing:.02em;
   color:var(--gold-2);background:rgba(26,106,72,.1);border:1px solid var(--hair);padding:6px 13px;border-radius:999px;white-space:nowrap}}
 @media(max-width:640px){{.why-item .seal{{display:none}}}}

 /* ===== WHAT YOU SEE — deal card on warm band ===== */
 .glance-wrap{{background:linear-gradient(180deg,var(--ivory-2),var(--ivory))}}
 .glance-card{{max-width:920px;margin:0 auto;background:var(--surface);border:1px solid var(--hair);
   border-radius:var(--r-lg);padding:clamp(24px,4vw,40px);box-shadow:var(--shadow);position:relative;overflow:hidden}}
 .glance-card::before{{content:"";position:absolute;left:0;right:0;top:0;height:3px;
   background:linear-gradient(90deg,var(--good),var(--okay) 50%,var(--weak))}}
 .glance-top{{display:flex;flex-wrap:wrap;align-items:center;gap:8px 16px;margin-bottom:26px;padding-bottom:20px;border-bottom:1px solid var(--hair-soft)}}
 .glance-top .addr{{font-family:"Cormorant Garamond",serif;font-weight:600;font-size:1.9rem;color:var(--ink)}}
 .glance-top .meta{{font-family:"Inter";color:var(--muted);font-size:.9rem}}
 .glance-top .chip{{margin-left:auto;font-family:"Inter";font-size:.78rem;font-weight:600;color:var(--good);
   background:var(--good-soft);border:1px solid rgba(26,143,90,.32);padding:6px 14px;border-radius:999px;display:inline-flex;align-items:center;gap:7px}}
 .glance-top .chip svg{{width:14px;height:14px}}
 .stat-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:26px}}
 @media(max-width:680px){{.stat-grid{{grid-template-columns:1fr 1fr;gap:26px 20px}}}}
 .stat .l{{font-family:"Inter";font-size:.8rem;color:var(--muted);margin-bottom:10px;display:flex;align-items:center;gap:7px}}
 .stat .l svg{{width:16px;height:16px;color:var(--gold);opacity:.9}}
 .stat .v{{font-family:"Cormorant Garamond",serif;font-weight:600;font-size:2.05rem;line-height:1;color:var(--ink)}}
 .stat .v.good{{color:var(--good)}} .stat .v.okay{{color:var(--okay)}} .stat .v.weak{{color:var(--weak)}}
 .stat .f{{font-family:"Inter";font-size:.76rem;color:var(--faint);margin-top:8px}}

 /* ===== FREE TOOLS ===== */
 .tools-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;max-width:960px;margin:0 auto}}
 @media(max-width:760px){{.tools-grid{{grid-template-columns:1fr 1fr}}}}
 .tool{{display:flex;flex-direction:column;align-items:center;justify-content:flex-start;
   text-decoration:none;color:inherit;background:var(--surface);border:1px solid var(--hair);
   border-radius:var(--r-card);padding:30px 22px;text-align:center;box-shadow:var(--card-shadow);
   transition:transform .18s var(--ease-card),box-shadow .18s var(--ease-card),border-color .18s}}
 .tool:hover{{transform:var(--lift);box-shadow:var(--card-shadow-hover);border-color:rgba(26,106,72,.5)}}
 @media(prefers-reduced-motion:reduce){{.tool:hover{{transform:none}}}}
 .tool .ico{{width:46px;height:46px;border-radius:13px;margin:0 auto 15px;display:grid;place-items:center;
   background:linear-gradient(155deg,rgba(26,106,72,.18),rgba(26,106,72,.05));border:1px solid var(--hair)}}
 .tool .ico svg{{width:24px;height:24px;color:var(--gold-2)}}
 /* illustrated raster icon variant (gold-ringed full-colour art): bigger, no tint
    frame, a soft drop-shadow for depth — premium without the line-icon chrome. */
 .tool .ico.illus,.hub-card .ico.illus{{background:transparent;border:0;overflow:visible}}
 .tool .ico.illus{{width:62px;height:62px;border-radius:0}}
 .tool .ico.illus img{{width:62px;height:62px;display:block;
   filter:drop-shadow(0 6px 13px rgba(60,44,20,.20))}}
 .hub-card .ico.illus{{width:66px;height:66px;border-radius:0}}
 .hub-card .ico.illus img{{width:66px;height:66px;display:block;
   filter:drop-shadow(0 6px 13px rgba(60,44,20,.20))}}
 .tool h4{{font-weight:600;font-size:1.28rem;margin:0 0 4px;line-height:1.15;color:var(--ink)}}
 .tool p{{font-family:"Inter";font-size:.84rem;color:var(--muted);line-height:1.5;margin:0}}
 .tool h4{{margin-top:2px}}
 .tool .free{{font-family:"Inter";margin-top:auto;padding-top:14px;display:inline-block;font-size:.68rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--good)}}
 .tool .freebadge{{margin-top:auto;padding-top:14px}}

 /* ===== EVERYTHING-YOU-GET — static full-colour feature grid (#why-grid) =====
    Always-visible companion to the spinning constellation: this is where the
    full-colour illustrated art is shown at its best, in a calm premium grid. */
 .fgrid{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;max-width:1000px;margin:0 auto}}
 @media(max-width:820px){{.fgrid{{grid-template-columns:1fr 1fr}}}}
 @media(max-width:520px){{.fgrid{{grid-template-columns:1fr}}}}
 .fcard{{display:flex;align-items:flex-start;gap:18px;text-align:left;
   background:var(--surface);border:1px solid var(--hair);border-radius:var(--r-card);
   padding:24px 22px;box-shadow:var(--card-shadow);
   transition:transform .18s var(--ease-card),box-shadow .18s var(--ease-card),border-color .18s}}
 .fcard:hover{{transform:var(--lift);box-shadow:var(--card-shadow-hover);border-color:rgba(26,106,72,.5)}}
 @media(prefers-reduced-motion:reduce){{.fcard:hover{{transform:none}}}}
 .fcard .fico{{flex:0 0 auto;width:58px;height:58px;display:grid;place-items:center}}
 .fcard .fico img{{width:58px;height:58px;display:block;
   filter:drop-shadow(0 6px 13px rgba(60,44,20,.20))}}
 .fcard .fbody{{min-width:0}}
 .fcard h4{{font-weight:600;font-size:1.18rem;margin:2px 0 4px;line-height:1.18;color:var(--ink)}}
 .fcard p{{font-family:"Inter";font-size:.84rem;color:var(--muted);line-height:1.5;margin:0}}
 /* anchor cards (e.g. credit → learn page) shouldn't look like dead links */
 a.fcard{{text-decoration:none;color:inherit}}

 /* ===== CITY / REPORT — page hero + listing cards ===== */
 .pagehero{{text-align:center;max-width:760px;margin:54px auto 8px}}
 .pagehero h1{{font-weight:500;font-size:clamp(2.3rem,5vw,3.6rem);line-height:1.06;letter-spacing:.005em;margin:0 auto;max-width:18ch}}
 .pagehero h1 em{{color:var(--gold)}}
 .pagehero p{{font-family:"Inter";color:var(--muted);font-size:1.05rem;margin:16px auto 0;max-width:56ch}}
 .pagehero .cta-row{{margin-top:26px}}
 .deal-list{{max-width:820px;margin:40px auto 0;display:flex;flex-direction:column;gap:14px}}
 .lcard{{display:flex;align-items:center;gap:18px;background:var(--surface);border:1px solid var(--hair);
   border-radius:var(--r);padding:18px 20px;box-shadow:var(--shadow-sm);transition:transform .18s,border-color .2s}}
 .lcard:hover{{transform:translateY(-2px);border-color:rgba(26,106,72,.5)}}
 .lcard .gauge{{width:60px;height:60px;border-radius:50%;flex:0 0 auto;display:grid;place-items:center;position:relative}}
 .lcard .gauge .ring{{position:absolute;inset:0;border-radius:50%}}
 .lcard .gauge .num{{position:relative;font-family:"Cormorant Garamond",serif;font-weight:600;font-size:1.55rem;color:var(--ink)}}
 .lcard .body{{flex:1;min-width:0}}
 .lcard .price{{font-family:"Cormorant Garamond",serif;font-weight:600;font-size:1.65rem;line-height:1;color:var(--ink)}}
 .lcard .addr{{font-family:"Inter";font-weight:600;font-size:.98rem;color:var(--ink-soft);margin-top:3px}}
 .lcard .pills{{margin-top:9px;display:flex;flex-wrap:wrap;gap:7px}}
 .pill{{font-family:"Inter";display:inline-flex;align-items:center;gap:6px;border-radius:999px;
   padding:4px 11px;font-size:.76rem;font-weight:600}}
 .pill.good{{background:var(--good-soft);color:var(--good);border:1px solid rgba(26,143,90,.3)}}
 .pill.warn{{background:var(--weak-soft);color:var(--weak);border:1px solid rgba(192,57,43,.28)}}
 .lcard .trend{{font-family:"Inter";font-size:.8rem;color:var(--faint);margin-top:7px}}
 .pagelinks{{max-width:820px;margin:32px auto 0;font-family:"Inter";font-size:.95rem;text-align:center}}
 .pagelinks a{{color:var(--gold-2);text-decoration:none;font-weight:600}}
 .pagelinks a:hover{{text-decoration:underline}}

 /* ===== LEARN — editorial glossary on ivory ===== */
 .learn-intro{{max-width:780px;margin:54px auto 10px;text-align:center}}
 .learn-intro .learn-kicker{{display:inline-flex;align-items:center;justify-content:center;gap:4px;flex-wrap:wrap}}
 .learn-intro .learn-kicker .freebadge{{text-transform:uppercase;letter-spacing:.16em}}
 .learn-intro h1{{font-weight:500;font-size:clamp(2.3rem,5vw,3.5rem);line-height:1.06;margin:0}}
 .learn-intro h1 em{{color:var(--gold)}}
 .learn-intro p{{font-family:"Inter";color:var(--muted);font-size:1.05rem;margin:16px auto 0;max-width:58ch;line-height:1.6}}
 .toc{{display:flex;flex-wrap:wrap;gap:9px;justify-content:center;max-width:820px;margin:24px auto 10px}}
 .toc a{{font-family:"Inter";display:inline-block;background:var(--surface);border:1px solid var(--hair);
   border-radius:999px;padding:7px 14px;font-size:.85rem;font-weight:600;color:var(--gold-2);text-decoration:none;transition:background .2s,border-color .2s}}
 .toc a:hover{{background:var(--surface-2);border-color:rgba(26,106,72,.55)}}
 .term-list{{max-width:780px;margin:30px auto 0;display:flex;flex-direction:column;gap:16px}}
 .term{{background:var(--surface);border:1px solid var(--hair);border-left:4px solid var(--gold);
   border-radius:var(--r);padding:22px 24px;scroll-margin-top:84px;box-shadow:var(--shadow-sm)}}
 .term h2{{font-weight:600;font-size:1.55rem;margin:0 0 8px;display:flex;align-items:center;gap:11px;color:var(--ink)}}
 .term .ic{{font-size:1.35rem;line-height:1}}
 .term p{{font-family:"Inter";margin:.4rem 0;color:var(--ink-soft);line-height:1.6;font-size:1rem}}
 .term p b{{color:var(--ink);font-weight:600}}
 .term .eg{{font-family:"Inter";background:var(--surface-2);border:1px dashed var(--hair);border-radius:12px;
   padding:11px 14px;margin:.7rem 0 .1rem;color:var(--ink-soft);font-size:.95rem}}
 .term .eg b{{color:var(--gold-2)}}
 .term.warnterm{{border-left-color:var(--okay)}}
 .term.warnterm .eg b{{color:var(--okay)}}
 .scorekey{{display:flex;gap:8px;flex-wrap:wrap;margin:.6rem 0 .2rem}}
 .scorekey span{{font-family:"Inter";display:inline-flex;align-items:center;gap:7px;border-radius:999px;
   padding:5px 13px;font-weight:600;font-size:.85rem;color:#fff}}
 .scorekey .dot{{width:10px;height:10px;border-radius:50%;background:rgba(255,255,255,.9);display:inline-block}}

 /* ===== FORECLOSURE JOURNEY — four-stage explainer on ivory ===== */
 .fjourney{{max-width:820px;margin:0 auto;scroll-margin-top:84px}}
 .fjourney .fj-head{{text-align:center;max-width:680px;margin:0 auto 8px}}
 .fjourney .fj-head .kicker{{display:inline-flex;align-items:center;gap:9px;font-family:"Inter";font-size:.72rem;
   font-weight:600;letter-spacing:.22em;text-transform:uppercase;color:var(--gold-2);margin-bottom:14px}}
 .fjourney .fj-head .kicker::before,.fjourney .fj-head .kicker::after{{content:"";width:24px;height:1px;
   background:linear-gradient(90deg,transparent,var(--gold))}}
 .fjourney .fj-head .kicker::after{{transform:scaleX(-1)}}
 .fjourney .fj-head h2{{font-weight:500;font-size:clamp(1.9rem,4vw,2.7rem);line-height:1.08;margin:0;color:var(--ink)}}
 .fjourney .fj-head h2 em{{color:var(--gold);font-style:italic}}
 .fjourney .fj-head p{{font-family:"Inter";color:var(--muted);font-size:1.02rem;line-height:1.6;margin:14px auto 0;max-width:54ch}}
 /* the vertical journey — a gold spine threading the stages */
 .fj-steps{{position:relative;margin:38px auto 0;padding-left:0;list-style:none;display:flex;flex-direction:column;gap:18px}}
 .fj-steps::before{{content:"";position:absolute;left:23px;top:18px;bottom:42px;width:2px;
   background:linear-gradient(180deg,var(--gold),rgba(26,106,72,.25));border-radius:2px}}
 .fj-step{{position:relative;background:var(--surface);border:1px solid var(--hair);border-radius:var(--r);
   padding:22px 24px 22px 70px;scroll-margin-top:84px;box-shadow:var(--shadow-sm);
   border-left:4px solid var(--stage,var(--gold))}}
 .fj-step .num{{position:absolute;left:8px;top:20px;width:32px;height:32px;border-radius:50%;
   display:flex;align-items:center;justify-content:center;font-family:"Inter";font-weight:700;font-size:.95rem;
   color:#fff;background:var(--stage,var(--gold));box-shadow:0 0 0 5px var(--surface),0 6px 14px -6px rgba(60,44,20,.5)}}
 .fj-step h3{{font-family:"Cormorant Garamond",Georgia,serif;font-weight:600;font-size:1.5rem;line-height:1.1;
   margin:0;color:var(--ink);display:flex;align-items:baseline;gap:11px;flex-wrap:wrap}}
 .fj-step h3 .chip{{font-family:"Inter";font-weight:600;font-size:.62rem;letter-spacing:.14em;text-transform:uppercase;
   padding:4px 10px;border-radius:999px;background:var(--stage-soft,var(--okay-soft));color:var(--stage,var(--gold-2));
   white-space:nowrap}}
 .fj-step p{{font-family:"Inter";color:var(--ink-soft);line-height:1.62;font-size:1rem;margin:.6rem 0 0}}
 .fj-step p b{{color:var(--ink);font-weight:600}}
 .fj-step.warm{{--stage:var(--good);--stage-soft:var(--good-soft)}}
 .fj-step.caution{{--stage:var(--okay);--stage-soft:var(--okay-soft)}}
 .fj-step.early{{--stage:var(--gold);--stage-soft:rgba(26,106,72,.13)}}
 /* why-this-matters payoff panel */
 .fj-why{{max-width:820px;margin:24px auto 0;background:radial-gradient(120% 150% at 50% -10%, #FCF3DF, var(--surface) 62%);
   border:1px solid rgba(26,106,72,.4);border-radius:var(--r-lg);padding:26px 28px;text-align:center;
   box-shadow:0 30px 64px -38px rgba(60,44,20,.30)}}
 .fj-why h3{{font-family:"Cormorant Garamond",Georgia,serif;font-weight:600;font-size:1.6rem;margin:0;color:var(--ink)}}
 .fj-why p{{font-family:"Inter";color:var(--ink-soft);font-size:1.02rem;line-height:1.6;margin:10px auto 0;max-width:58ch}}
 .fj-why p b{{color:var(--gold-2)}}
 .fj-caveat{{font-family:"Inter";display:flex;align-items:flex-start;gap:10px;max-width:760px;margin:16px auto 0;
   background:var(--okay-soft);border:1px solid rgba(181,120,10,.3);border-radius:12px;padding:12px 16px;
   color:var(--ink-soft);font-size:.92rem;line-height:1.5;text-align:left}}
 .fj-caveat .ic{{color:var(--okay);font-size:1.1rem;line-height:1.3;flex:none}}
 @media(max-width:560px){{
   .fj-step{{padding:20px 18px 20px 56px}}
   .fj-step .num{{left:6px;width:28px;height:28px;font-size:.85rem}}
   .fj-steps::before{{left:19px}}
 }}

 /* ===== WAITLIST — gold-bordered coupon ===== */
 .wl{{max-width:800px;margin:0 auto;text-align:center;
   background:radial-gradient(120% 150% at 50% -10%, #FCF3DF, var(--surface) 60%);
   border:1px solid rgba(26,106,72,.4);border-radius:var(--r-lg);padding:clamp(36px,5vw,60px);
   position:relative;overflow:hidden;box-shadow:0 36px 72px -38px rgba(60,44,20,.34)}}
 .wl::before{{content:"";position:absolute;inset:0;pointer-events:none;
   background:radial-gradient(70% 60% at 18% 0%, rgba(26,106,72,.14), transparent 56%),
              radial-gradient(70% 70% at 86% 110%, rgba(26,106,72,.10), transparent 58%)}}
 .wl::after{{content:"";position:absolute;left:0;right:0;top:0;height:1px;
   background:linear-gradient(90deg,transparent,var(--gold) 50%,transparent);opacity:.8}}
 .wl > *{{position:relative;z-index:1}}
 .wl .key{{display:inline-flex;align-items:center;gap:10px;font-family:"Inter";font-size:.72rem;font-weight:600;
   letter-spacing:.22em;text-transform:uppercase;color:var(--gold-2);margin-bottom:18px}}
 .wl .key::before,.wl .key::after{{content:"";width:24px;height:1px;background:linear-gradient(90deg,transparent,var(--gold))}}
 .wl .key::after{{transform:scaleX(-1)}}
 .wl h2{{font-family:"Cormorant Garamond",serif;font-weight:500;font-size:clamp(2.1rem,5vw,3.3rem);line-height:1.06;letter-spacing:.005em;margin:0;color:var(--ink)}}
 .wl p{{font-family:"Inter";color:var(--muted);max-width:48ch;margin:16px auto 4px;font-size:1.04rem}}
 .wl .price{{color:var(--gold-2);font-weight:700}}
 .wl form{{max-width:500px;margin:30px auto 0;display:flex;flex-wrap:wrap;gap:12px}}
 .wl input[type=email]{{flex:1 1 240px;min-width:0;padding:16px 18px;border-radius:13px;
   border:1px solid rgba(30,26,22,.18);background:var(--surface);color:var(--ink);
   font-family:"Inter";font-size:1rem;min-height:44px;transition:border-color .2s,box-shadow .2s}}
 .wl input::placeholder{{color:var(--faint)}}
 .wl input:focus{{outline:2px solid var(--gold);outline-offset:2px;border-color:transparent}}
 .wl button{{flex:0 0 auto;border:0;cursor:pointer;font-family:"Inter";padding:16px 28px;border-radius:13px;
   font-weight:600;font-size:1rem;min-height:44px;color:#FFFBF1;
   background:linear-gradient(150deg,var(--gold-bright),var(--gold) 78%);
   box-shadow:0 14px 28px -14px rgba(14,58,42,.55), inset 0 1px 0 rgba(255,255,255,.4);
   transition:transform .18s var(--ease-card),box-shadow .18s var(--ease-card)}}
 .wl button:hover{{transform:translateY(-2px);box-shadow:0 20px 36px -14px rgba(14,58,42,.6), inset 0 1px 0 rgba(255,255,255,.45)}}
 .wl button:active{{transform:translateY(-1px) scale(.99)}}
 @media(prefers-reduced-motion:reduce){{.wl button:hover,.wl button:active{{transform:none}}}}
 .wl .fine{{font-family:"Inter";margin-top:18px;font-size:.8rem;color:var(--faint)}}

 /* ===== FOOTER ===== */
 footer{{padding:46px 0 60px}}
 .foot-grid{{display:flex;flex-wrap:wrap;gap:18px 30px;align-items:center}}
 .foot-links{{display:flex;flex-wrap:wrap;gap:24px;margin-left:auto}}
 .foot-links a{{font-family:"Inter";text-decoration:none;color:var(--muted);font-size:.9rem;transition:color .2s}}
 .foot-links a:hover{{color:var(--gold-2)}}
 .disclaim{{font-family:"Inter";margin-top:26px;font-size:.76rem;color:var(--faint);line-height:1.7;max-width:74ch}}

 /* ===== BEST-DEALS BANNER — editorial headline + HOW + count + ZIP box ===== */
 /* SEAMLESS HERO HAND-OFF (lightened 2026-06-21, owner: "keep it sunny"):
    the cinematic hero now ends on a LIGHT warm cream (.ch-fade → rgba(238,229,213,.95)),
    not near-black. So this section STARTS at that same warm cream and settles into
    ivory over a short, gentle band. The eye finds no hard line — the bright hero
    foot melts straight into the warm page as ONE continuous surface, with no dark
    band reintroduced. The section's real content sits below the blend, on ivory. */
 .best-wrap{{background:
     linear-gradient(180deg,
       rgb(238,229,213) 0,
       var(--ivory-2) 64px,
       var(--ivory) 140px,
       var(--ivory) 100%)}}
 /* extra top padding so the headline never lands inside the dark blend band */
 .best-wrap>.sec{{padding-top:clamp(150px,18vh,220px)}}
 .best{{max-width:980px;margin:0 auto;text-align:center}}
 .best .kicker{{margin-bottom:18px}}
 .best h2{{font-weight:500;font-size:clamp(2.2rem,5.4vw,3.7rem);line-height:1.08;
   letter-spacing:.004em;margin:0 auto;max-width:20ch}}
 /* RED used TASTEFULLY — only on the load-bearing words, never the whole block,
    so it stays luxe and doesn't fight the deal-score "walk away" red. */
 .best h2 .red{{color:var(--deep-red);font-weight:600}}
 .best h2 em{{color:var(--gold);font-weight:600;font-style:italic}}
 .best .how{{font-family:"Inter";color:var(--ink-soft);font-size:clamp(1.02rem,2vw,1.14rem);
   line-height:1.64;max-width:60ch;margin:22px auto 0}}
 .best .how b{{color:var(--ink);font-weight:600}}
 .best .how .src{{color:var(--gold-2);font-weight:600}}

 /* live count stat — big calm Cormorant number with a gold halo */
 .countstat{{position:relative;display:inline-flex;flex-direction:column;align-items:center;
   margin:34px auto 0;padding:6px 30px}}
 .countstat::before{{content:"";position:absolute;left:50%;top:46%;width:300px;height:160px;
   transform:translate(-50%,-50%);pointer-events:none;border-radius:50%;
   background:radial-gradient(circle, rgba(26,106,72,.18), transparent 68%)}}
 .countstat .num{{position:relative;font-family:"Cormorant Garamond",serif;font-weight:600;
   font-size:clamp(3rem,9vw,5rem);line-height:1;letter-spacing:.005em;color:var(--ink)}}
 .countstat .cap{{position:relative;font-family:"Inter";font-size:.78rem;font-weight:600;
   letter-spacing:.2em;text-transform:uppercase;color:var(--gold-2);margin-top:10px}}

 /* ZIP / city box — inviting, mobile-first, hands off to the live app */
 .ziphunt{{max-width:560px;margin:34px auto 0}}
 .ziphunt .prompt{{font-family:"Inter";color:var(--muted);font-size:.96rem;margin:0 0 14px}}
 .zipform{{display:flex;flex-wrap:wrap;gap:12px;justify-content:center}}
 .zipform .zipwrap{{position:relative;flex:1 1 260px;min-width:0;display:flex;align-items:center}}
 .zipform .zipwrap svg{{position:absolute;left:16px;width:18px;height:18px;color:var(--gold);opacity:.85;pointer-events:none}}
 .zipform input{{width:100%;font-family:"Inter";font-size:1.02rem;color:var(--ink);
   background:var(--surface);border:1px solid rgba(30,26,22,.18);border-radius:13px;
   padding:16px 18px 16px 44px;min-height:44px;transition:border-color .2s,box-shadow .2s}}
 .zipform input::placeholder{{color:var(--faint)}}
 .zipform input:focus{{outline:2px solid var(--gold);outline-offset:2px;border-color:transparent}}
 .zipform button{{flex:0 0 auto;border:0;cursor:pointer;font-family:"Inter";padding:16px 26px;
   border-radius:13px;font-weight:600;font-size:1rem;min-height:44px;color:#FFFBF1;
   display:inline-flex;align-items:center;gap:8px;
   background:linear-gradient(150deg,var(--gold-bright),var(--gold) 78%);
   box-shadow:0 14px 28px -14px rgba(14,58,42,.55), inset 0 1px 0 rgba(255,255,255,.4);
   transition:transform .18s var(--ease-card),box-shadow .18s var(--ease-card)}}
 .zipform button:hover{{transform:translateY(-2px);box-shadow:0 20px 36px -14px rgba(14,58,42,.6), inset 0 1px 0 rgba(255,255,255,.45)}}
 .zipform button:active{{transform:translateY(-1px) scale(.99)}}
 @media(prefers-reduced-motion:reduce){{.zipform button:hover,.zipform button:active{{transform:none}}}}
 .zipform button svg{{width:18px;height:18px}}
 .ziphunt .zipfine{{font-family:"Inter";margin-top:12px;font-size:.78rem;color:var(--faint)}}
 @media(max-width:460px){{.zipform button{{flex:1 1 100%;justify-content:center}}}}

 /* ===== "FREE" BADGE — ONE classy seal, reused everywhere we give value away ===== */
 .freebadge{{display:inline-flex;align-items:center;gap:6px;font-family:"Inter";
   font-size:.66rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;
   color:var(--good);background:linear-gradient(180deg,rgba(26,143,90,.10),rgba(26,106,72,.07));
   border:1px solid rgba(26,143,90,.34);border-radius:999px;padding:5px 12px 5px 10px;
   line-height:1;box-shadow:inset 0 1px 0 rgba(255,255,255,.5)}}
 .freebadge .fdot{{width:6px;height:6px;border-radius:50%;background:var(--good);
   box-shadow:0 0 8px rgba(26,143,90,.7);flex:none}}
 .freebadge.big{{font-size:.74rem;letter-spacing:.18em;padding:7px 16px 7px 13px;gap:8px}}
 .freebadge.big .fdot{{width:7px;height:7px}}

 /* ===== LOCKED TEASER — "a taste of the paid magic, behind glass" ===== */
 .teaser-wrap{{background:linear-gradient(180deg,var(--ivory),var(--ivory-2))}}
 .teaser-grid{{display:grid;grid-template-columns:1fr 1fr;gap:22px;max-width:940px;margin:0 auto}}
 @media(max-width:780px){{.teaser-grid{{grid-template-columns:1fr;max-width:460px}}}}
 .tcard{{position:relative;background:var(--surface);border:1px solid var(--hair);
   border-radius:var(--r-lg);overflow:hidden;box-shadow:var(--shadow);display:flex;flex-direction:column}}
 .tcard .sample-tag{{position:absolute;top:14px;right:14px;z-index:4;font-family:"Inter";
   font-size:.6rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--gold-2);
   background:rgba(251,247,239,.9);border:1px solid var(--hair);border-radius:999px;padding:5px 11px;
   backdrop-filter:blur(4px)}}
 /* the FREE / visible top of the card */
 .tcard .open{{padding:24px 24px 18px;border-bottom:1px solid var(--hair-soft)}}
 .tcard .open .addr{{font-family:"Cormorant Garamond",serif;font-weight:600;font-size:1.7rem;
   line-height:1.1;color:var(--ink);max-width:80%}}
 .tcard .open .meta{{font-family:"Inter";color:var(--muted);font-size:.86rem;margin-top:5px}}
 .tcard .open .teaserline{{font-family:"Inter";color:var(--ink-soft);font-size:.92rem;margin-top:12px;
   display:inline-flex;align-items:center;gap:7px}}
 .tcard .open .teaserline svg{{width:15px;height:15px;color:var(--gold);flex:none}}
 /* the LOCKED / paid rows — real-looking numbers blurred behind frosted glass */
 .tlocked{{position:relative;padding:20px 24px 24px}}
 .tlocked .lrow{{display:flex;align-items:center;justify-content:space-between;gap:14px;
   padding:13px 0;border-bottom:1px solid var(--hair-soft)}}
 .tlocked .lrow:last-child{{border-bottom:0}}
 .tlocked .lrow .lk{{font-family:"Inter";display:inline-flex;align-items:center;gap:9px;
   color:var(--muted);font-size:.88rem}}
 .tlocked .lrow .lk svg{{width:16px;height:16px;color:var(--gold);opacity:.9}}
 .tlocked .lrow .lv{{font-family:"Cormorant Garamond",serif;font-weight:600;font-size:1.5rem;
   letter-spacing:.01em;color:var(--ink)}}
 .tlocked .lrow .lv.good{{color:var(--good)}} .tlocked .lrow .lv.okay{{color:var(--okay)}}
 /* the frost: blur the numbers, dim them, kill selection — genuinely hidden */
 .tlocked .blurfield{{filter:blur(7px);opacity:.85;user-select:none;pointer-events:none;
   -webkit-user-select:none}}
 /* glass overlay with the lock + unlock CTA */
 .tlocked .glass{{position:absolute;inset:0;z-index:3;display:flex;flex-direction:column;
   align-items:center;justify-content:center;text-align:center;gap:12px;padding:22px;
   background:linear-gradient(180deg,rgba(251,247,239,.36),rgba(251,247,239,.72));
   backdrop-filter:blur(2.5px) saturate(1.05);-webkit-backdrop-filter:blur(2.5px) saturate(1.05)}}
 .tlocked .glass .lockwrap{{width:48px;height:48px;border-radius:50%;display:grid;place-items:center;
   background:linear-gradient(155deg,var(--gold-bright),var(--gold-deep));
   box-shadow:0 12px 26px -12px rgba(14,58,42,.6), inset 0 1px 0 rgba(255,255,255,.45)}}
 .tlocked .glass .lockwrap svg{{width:24px;height:24px;color:#FFFBF1}}
 .tlocked .glass .gline{{font-family:"Cormorant Garamond",serif;font-weight:600;font-size:1.28rem;
   line-height:1.2;color:var(--ink);max-width:26ch}}
 .tlocked .glass .unlock{{font-family:"Inter";display:inline-flex;align-items:center;gap:8px;
   text-decoration:none;padding:12px 22px;border-radius:12px;font-weight:600;font-size:.95rem;color:#FFFBF1;
   background:linear-gradient(150deg,var(--gold-bright),var(--gold) 78%);
   box-shadow:0 14px 28px -14px rgba(14,58,42,.55), inset 0 1px 0 rgba(255,255,255,.4);transition:transform .18s}}
 .tlocked .glass .unlock:hover{{transform:translateY(-2px);color:#FFFBF1}}
 .tlocked .glass .unlock svg{{width:16px;height:16px}}
 .tlocked .glass .gfine{{font-family:"Inter";font-size:.74rem;color:var(--muted)}}
 .teaser-foot{{text-align:center;max-width:620px;margin:34px auto 0;font-family:"Inter";
   font-size:.9rem;color:var(--muted)}}
 .teaser-foot a{{color:var(--gold-2);font-weight:600;text-decoration:none}}
 .teaser-foot a:hover{{text-decoration:underline}}

 /* reveal */
 .reveal{{opacity:0;transform:translateY(20px);transition:opacity .8s ease,transform .8s ease}}
 .reveal.in{{opacity:1;transform:none}}
 @media(prefers-reduced-motion:reduce){{
   .reveal{{opacity:1;transform:none;transition:none}}
   #arcF{{transition:none!important}}
   html{{scroll-behavior:auto}}
 }}

 /* ===================================================================
    THE FEATURE GALAXY — dark constellation of everything you get.
    Lifted from design_preview/feature_orbit.html (owner-approved 2026-06-18)
    and folded into the Ivory & Gold brand. The site :root already defines
    --ivory/--ink/--gold*/--good/--okay/--weak/--r/--r-lg, so we DO NOT
    redefine them here — only the NEW dark-field tokens this section needs.
    =================================================================== */
 :root{{
   --teal:#3FB8A0;            /* cool counterpart to the gold — glow accent only */
   --ink-deep:#13100B;        /* warm charcoal / deep ink */
   --ink-deep-2:#1C1711;
   --g-card:rgba(36,29,20,.78);
   --g-line:rgba(46,140,98,.30);
 }}

 .galaxy{{position:relative;overflow:hidden;padding:84px 24px 92px;
   /* pull up under the hero's blurred fade and blend the top edge dark→dark so
      there is NO seam between the cover photo and the constellation (2026-06-20) */
   margin-top:-1px;
   /* CLASSICAL LUXURY BACKGROUND IMAGE SLOT ──────────────────────────
      A single owner-supplied photo (site/assets/galaxy_bg.jpg) sits BEHIND
      the constellation, ALWAYS under a heavy dark scrim so the gold/teal
      nodes + white text stay readable. The warm-ink gradient is layered
      ON TOP of the image as the scrim AND doubles as a tasteful fallback
      when galaxy_bg.jpg is absent — so it looks intentional with OR
      without the file. Recommended image: 2000×1400px landscape, dark/moody
      (classical architecture, marble, night sky). */
   background-color:var(--ink-deep);
   background-image:
     radial-gradient(900px 520px at 50% 8%, rgba(46,140,98,.16), transparent 60%),
     radial-gradient(680px 520px at 12% 96%, rgba(63,184,160,.10), transparent 62%),
     radial-gradient(680px 520px at 92% 70%, rgba(46,140,98,.07), transparent 60%),
     linear-gradient(180deg, rgba(28,23,17,.82) 0%, rgba(19,16,11,.90) 58%, rgba(15,12,8,.95) 100%),
     url('assets/galaxy_bg.jpg');
   background-size:auto,auto,auto,auto,cover;
   background-position:center;background-repeat:no-repeat}}
 /* faint starfield + texture (sits above the bg image, below content) */
 .galaxy::before{{content:"";position:absolute;inset:0;pointer-events:none;opacity:.5;
   background-image:
     radial-gradient(1.4px 1.4px at 18% 24%, rgba(255,247,225,.55), transparent),
     radial-gradient(1.2px 1.2px at 72% 16%, rgba(255,247,225,.40), transparent),
     radial-gradient(1.3px 1.3px at 41% 78%, rgba(255,247,225,.42), transparent),
     radial-gradient(1.1px 1.1px at 86% 52%, rgba(255,247,225,.35), transparent),
     radial-gradient(1.2px 1.2px at 9% 64%, rgba(255,247,225,.30), transparent),
     radial-gradient(1.1px 1.1px at 60% 90%, rgba(255,247,225,.32), transparent)}}
 /* top-edge blend: a short dark wash matching the hero's bottom fade colour,
    resolving into the galaxy's own warm dark — kills any step where the cover
    meets the constellation. Sits above the bg, below the content/starfield. */
 .galaxy::after{{content:"";position:absolute;left:0;right:0;top:0;height:160px;
   z-index:1;pointer-events:none;
   background:linear-gradient(180deg, rgba(14,15,20,1) 0%, rgba(14,15,20,.72) 34%,
     rgba(15,12,8,.30) 70%, transparent 100%)}}
 .galaxy-inner{{position:relative;z-index:2;max-width:1100px;margin:0 auto}}

 .g-head{{text-align:center;margin:0 auto 14px;max-width:64ch}}
 .g-tag{{display:inline-flex;align-items:center;gap:9px;font-family:"Inter";font-size:.7rem;
   font-weight:600;letter-spacing:.22em;text-transform:uppercase;color:var(--gold-bright);
   border:1px solid rgba(46,140,98,.4);border-radius:999px;padding:7px 16px;
   background:rgba(46,140,98,.07)}}
 .g-tag .dot{{width:6px;height:6px;border-radius:50%;background:var(--good);
   box-shadow:0 0 10px rgba(26,143,90,.9)}}
 .g-head h2{{font-family:"Cormorant Garamond",Georgia,serif;color:#FBF3E1;font-weight:500;
   font-size:clamp(2.1rem,5.2vw,3.4rem);line-height:1.04;letter-spacing:.005em;margin:20px 0 0}}
 .g-head h2 em{{color:var(--gold-bright);font-style:italic;font-weight:600}}
 .g-head p{{font-family:"Inter";color:rgba(251,243,225,.66);font-size:clamp(1rem,2vw,1.12rem);
   max-width:54ch;margin:16px auto 0;line-height:1.6}}
 .g-hint{{font-family:"Inter";font-size:.8rem;color:rgba(251,243,225,.45);margin-top:10px;font-style:italic}}

 /* ===== ORBIT STAGE (desktop / tablet) ===== */
 .stage{{position:relative;width:min(560px,90vw);height:min(560px,90vw);margin:48px auto 10px}}
 .orbit-field{{position:absolute;inset:0;animation:gspin 60s linear infinite;transform-origin:50% 50%}}
 @keyframes gspin{{to{{transform:rotate(360deg)}}}}
 .stage.paused .orbit-field{{animation-play-state:paused}}
 .ring{{position:absolute;left:50%;top:50%;border-radius:50%;
   border:1px solid rgba(46,140,98,.14);transform:translate(-50%,-50%);pointer-events:none}}
 .ring.r1{{width:62%;height:62%}}
 .ring.r2{{width:96%;height:96%;border-style:dashed;border-color:rgba(46,140,98,.10)}}

 /* center hub — the Deal Dial mark, pulsing */
 .hub{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
   width:148px;height:148px;border-radius:50%;display:grid;place-items:center;z-index:6;
   cursor:pointer;border:0;padding:0;background:transparent}}
 .hub .glow{{position:absolute;inset:-46px;border-radius:50%;
   background:radial-gradient(circle,rgba(26,143,90,.40),rgba(26,143,90,.10) 48%,transparent 70%);
   animation:gbreathe 4.6s ease-in-out infinite}}
 @keyframes gbreathe{{0%,100%{{transform:scale(1);opacity:.85}}50%{{transform:scale(1.14);opacity:1}}}}
 /* the central Deal-Score dial reads GREEN (good) — reinforcing "green = a good
    deal" — on a calm ivory face, ringed by a thin gold luxury band. */
 .hub .disc{{position:relative;width:148px;height:148px;border-radius:50%;
   background:radial-gradient(120% 120% at 38% 30%, #FFFDF6, #FBF4E1 70%, #F3E8CC 100%);
   box-shadow:0 0 0 2px var(--gold-bright), 0 0 0 4px rgba(255,247,225,.30),
     inset 0 2px 10px rgba(255,255,255,.7), inset 0 -10px 26px rgba(26,143,90,.12),
     0 24px 50px -14px rgba(26,143,90,.4);
   display:flex;flex-direction:column;align-items:center;justify-content:center;color:var(--good)}}
 .hub .disc .ring-svg{{position:absolute;inset:9px;width:auto;height:auto}}
 .hub .disc .num{{font-family:"Cormorant Garamond",serif;font-weight:600;font-size:2.55rem;line-height:1;color:#127A4A}}
 .hub .disc .lbl{{font-family:"Inter";font-weight:700;font-size:.56rem;letter-spacing:.18em;
   text-transform:uppercase;margin-top:1px;color:#1A8F5A}}

 /* nodes — positioned by JS via transform; counter-rotated to stay upright */
 .node{{position:absolute;left:50%;top:50%;width:96px;height:96px;margin:-48px 0 0 -48px;z-index:5}}
 .node .spin-fix{{animation:gspin-rev 60s linear infinite;transform-origin:50% 50%;
   width:100%;height:100%;border-radius:50%}}
 .stage.paused .node .spin-fix{{animation-play-state:paused}}
 @keyframes gspin-rev{{to{{transform:rotate(-360deg)}}}}
 .node button{{all:unset;cursor:pointer;display:block;width:96px;height:96px;border-radius:50%}}
 .node .bubble{{position:relative;width:96px;height:96px;border-radius:50%;display:grid;place-items:center;
   background:radial-gradient(120% 120% at 40% 32%, rgba(48,40,28,.96), rgba(28,23,16,.96));
   border:1px solid var(--g-line);
   box-shadow:0 14px 34px -14px rgba(0,0,0,.7), inset 0 1px 0 rgba(255,247,225,.10);
   transition:transform .25s ease, box-shadow .25s ease, border-color .25s ease}}
 .node .bubble::after{{content:"";position:absolute;inset:-9px;border-radius:50%;
   background:radial-gradient(circle, rgba(46,140,98,.34), transparent 68%);opacity:0;
   transition:opacity .3s;animation:gnodepulse 5s ease-in-out infinite}}
 @keyframes gnodepulse{{0%,100%{{opacity:.18}}50%{{opacity:.42}}}}
 .node .bubble svg{{width:34px;height:34px;color:var(--gold-bright);position:relative;z-index:2}}
 .node .cap{{position:absolute;top:104px;left:50%;transform:translateX(-50%);white-space:nowrap;
   font-family:"Inter";font-size:.72rem;font-weight:600;color:rgba(251,243,225,.78);
   text-shadow:0 1px 8px rgba(0,0,0,.6);text-align:center}}
 .node button:hover .bubble,.node button:focus-visible .bubble{{transform:scale(1.1);
   border-color:rgba(46,140,98,.75);box-shadow:0 18px 40px -12px rgba(46,140,98,.5)}}
 .node button:focus-visible .bubble{{outline:2px solid var(--gold-bright);outline-offset:3px}}
 .node.active .bubble{{background:radial-gradient(120% 120% at 40% 32%, #6FD49F, var(--gold) 58%, var(--gold-deep));
   border-color:rgba(255,247,225,.6);box-shadow:0 20px 46px -10px rgba(46,140,98,.72)}}
 .node.active .bubble svg{{color:#FFFBF1}}
 .node.active .bubble::after{{opacity:.7}}
 .node.related .bubble{{border-color:rgba(63,184,160,.65);box-shadow:0 16px 38px -12px rgba(63,184,160,.45)}}
 .node.related .bubble svg{{color:var(--teal)}}
 .stage.has-active .node:not(.active):not(.related) .bubble{{opacity:.4}}

 /* MEANING-COLOURED constellation icons (owner: all-gold is hard to scan fast).
    GREEN = the deal/found · RED = a warning · BLUE = a money tool. Brighter,
    on-dark variants so they read cleanly over the deep field. Gold stays the
    section accent. */
 .node.mc-green .bubble svg{{color:#5FD89C}}
 .node.mc-red   .bubble svg{{color:#E8917F}}
 .node.mc-blue  .bubble svg{{color:#7FB4E6}}
 .node.mc-green .bubble{{border-color:rgba(95,216,156,.40)}}
 .node.mc-red   .bubble{{border-color:rgba(232,145,127,.40)}}
 .node.mc-blue  .bubble{{border-color:rgba(127,180,230,.40)}}
 .node.mc-green .bubble::after{{background:radial-gradient(circle, rgba(95,216,156,.26), transparent 68%)}}
 .node.mc-red   .bubble::after{{background:radial-gradient(circle, rgba(232,145,127,.26), transparent 68%)}}
 .node.mc-blue  .bubble::after{{background:radial-gradient(circle, rgba(127,180,230,.26), transparent 68%)}}
 /* keep the ACTIVE (gold-filled) state legible: dark glyph on the gold disc */
 .node.active .bubble svg{{color:#2A1E08 !important}}

 /* ===== detail card (popover) ===== */
 .gdetail{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%) scale(.92);
   width:min(340px,86vw);z-index:9;opacity:0;pointer-events:none;
   transition:opacity .28s ease, transform .28s ease}}
 .gdetail.show{{opacity:1;pointer-events:auto;transform:translate(-50%,-50%) scale(1)}}
 .gdetail .card{{position:relative;background:#FFFDF8;border:1px solid var(--g-line);
   border-radius:var(--r-lg);padding:24px 24px 22px;text-align:left;
   box-shadow:0 40px 80px -24px rgba(0,0,0,.7), 0 0 0 1px rgba(46,140,98,.18)}}
 .gdetail .card::before{{content:"";position:absolute;inset:0;border-radius:var(--r-lg);
   background:radial-gradient(120% 90% at 50% -10%, rgba(46,140,98,.12), transparent 60%);pointer-events:none}}
 .gdetail .ic{{width:46px;height:46px;border-radius:13px;display:grid;place-items:center;
   background:linear-gradient(150deg,var(--gold-bright),var(--gold-deep));margin-bottom:14px;
   box-shadow:0 10px 22px -10px rgba(14,58,42,.6),inset 0 1px 0 rgba(255,255,255,.45);position:relative}}
 .gdetail .ic svg{{width:24px;height:24px;color:#FFFBF1}}
 /* meaning-tinted icon tile in the popover (matches the node colour) */
 .gdetail .card.mc-green .ic{{background:linear-gradient(150deg,#2FB873,#147A4A)}}
 .gdetail .card.mc-red   .ic{{background:linear-gradient(150deg,#D75A47,#A22C20)}}
 .gdetail .card.mc-blue  .ic{{background:linear-gradient(150deg,#4A8FCC,#235E94)}}
 .gdetail h3{{font-family:"Cormorant Garamond",serif;font-weight:600;color:var(--ink);
   font-size:1.6rem;line-height:1.1;margin:0;position:relative}}
 .gdetail .what{{font-family:"Inter";font-size:.94rem;color:var(--ink-soft);line-height:1.58;margin:10px 0 0;position:relative}}
 .gdetail .chip{{display:inline-flex;align-items:center;gap:7px;margin-top:14px;
   font-family:"Inter";font-size:.74rem;font-weight:600;letter-spacing:.04em;
   padding:6px 12px;border-radius:999px;position:relative}}
 .gdetail .chip.good{{background:rgba(26,143,90,.12);color:var(--good)}}
 .gdetail .chip.okay{{background:rgba(181,120,10,.13);color:var(--okay)}}
 .gdetail .chip.weak{{background:rgba(192,57,43,.11);color:var(--weak)}}
 /* "See how it works →" link on each card */
 .gdetail .seemore{{display:inline-flex;align-items:center;gap:6px;margin-top:16px;
   font-family:"Inter";font-size:.86rem;font-weight:600;color:var(--gold-2);text-decoration:none;
   position:relative;transition:gap .18s}}
 .gdetail .seemore:hover{{gap:10px;text-decoration:underline}}
 .gdetail .x{{position:absolute;top:12px;right:12px;width:30px;height:30px;border:0;border-radius:50%;
   background:rgba(30,26,22,.06);color:var(--muted);cursor:pointer;display:grid;place-items:center;z-index:2}}
 .gdetail .x:hover{{background:rgba(30,26,22,.12);color:var(--ink)}}
 .gdetail .x svg{{width:15px;height:15px}}

 /* ===== MOBILE FALLBACK — stacked feature cards ===== */
 .glist{{display:none;max-width:540px;margin:30px auto 0;gap:14px;flex-direction:column}}
 .fcard{{display:block;text-align:left;width:100%;
   background:var(--g-card);border:1px solid var(--g-line);border-radius:var(--r);
   padding:17px 18px;color:#FBF3E1;box-shadow:0 16px 36px -22px rgba(0,0,0,.7)}}
 .fcard .frow{{display:flex;gap:15px;align-items:flex-start}}
 .fcard .fic{{flex:0 0 46px;width:46px;height:46px;border-radius:13px;display:grid;place-items:center;
   background:radial-gradient(120% 120% at 40% 30%, rgba(46,140,98,.22), rgba(28,23,16,.9));
   border:1px solid rgba(46,140,98,.35)}}
 .fcard .fic svg{{width:24px;height:24px;color:var(--gold-bright)}}
 /* meaning-coloured icons on the mobile stacked cards too */
 .fcard.mc-green .fic{{background:radial-gradient(120% 120% at 40% 30%, rgba(95,216,156,.20), rgba(28,23,16,.9));border-color:rgba(95,216,156,.35)}}
 .fcard.mc-green .fic svg{{color:#5FD89C}}
 .fcard.mc-red .fic{{background:radial-gradient(120% 120% at 40% 30%, rgba(232,145,127,.20), rgba(28,23,16,.9));border-color:rgba(232,145,127,.35)}}
 .fcard.mc-red .fic svg{{color:#E8917F}}
 .fcard.mc-blue .fic{{background:radial-gradient(120% 120% at 40% 30%, rgba(127,180,230,.20), rgba(28,23,16,.9));border-color:rgba(127,180,230,.35)}}
 .fcard.mc-blue .fic svg{{color:#7FB4E6}}
 .fcard h3{{font-family:"Cormorant Garamond",serif;font-weight:600;font-size:1.3rem;margin:0;color:#FBF3E1;line-height:1.12}}
 .fcard .what{{font-family:"Inter";font-size:.88rem;color:rgba(251,243,225,.66);margin:5px 0 0;line-height:1.5}}
 .fcard .chip{{display:inline-flex;margin-top:9px;font-family:"Inter";font-size:.7rem;font-weight:600;
   padding:4px 11px;border-radius:999px}}
 .fcard .chip.good{{background:rgba(26,143,90,.18);color:#5FD89C}}
 .fcard .chip.okay{{background:rgba(181,120,10,.20);color:#E9C06A}}
 .fcard .chip.weak{{background:rgba(192,57,43,.20);color:#E8917F}}
 .fcard .seemore{{display:inline-flex;align-items:center;gap:6px;margin-top:12px;
   font-family:"Inter";font-size:.84rem;font-weight:600;color:var(--gold-bright);text-decoration:none}}
 .fcard .seemore:hover{{text-decoration:underline}}

 /* below 760px → drop the orbit, show the premium stacked list */
 @media(max-width:760px){{
   .galaxy{{padding:60px 18px 64px}}
   .stage{{display:none}}
   .glist{{display:flex}}
   .g-hint{{display:none}}
 }}
 @media(prefers-reduced-motion:reduce){{
   .orbit-field,.node .spin-fix,.hub .glow,.node .bubble::after{{animation:none !important}}
 }}
</style>"""


# ──────────────────────────────────────────────────────────────────────────────
# Shared header / footer / nav — IDENTICAL brand furniture on every page.
# ──────────────────────────────────────────────────────────────────────────────
def header_html(here: str = "") -> str:
    def cls(slug):
        return " class='here'" if here == slug else ""
    logo_svg = svg("home")
    return (
        "<header><div class='wrap bar'>"
        f"<a class='logo' href='index.html'><span class='mark'>{logo_svg}</span><b>Underlisted</b></a>"
        "<nav class='navlinks'>"
        f"<a href='index.html'{cls('index')}>Deals</a>"
        f"<a href='free-tools.html'{cls('tools')}>Free tools</a>"
        f"<a href='report-underpriced.html'{cls('report')}>Most underpriced</a>"
        f"<a href='learn.html'{cls('learn')}>Learn the basics</a>"
        "<a class='btn-top' href='index.html#early-access'>Get early access</a>"
        "</nav></div></header><div class='rule gold'></div>"
    )


def footer_html() -> str:
    logo_svg = svg("home")
    return (
        "<div class='rule gold'></div><footer><div class='wrap'>"
        "<div class='foot-grid'>"
        f"<a class='logo' href='index.html'><span class='mark'>{logo_svg}</span><b>Underlisted</b></a>"
        "<nav class='foot-links'>"
        "<a href='index.html'>Deals</a>"
        "<a href='free-tools.html'>Free tools</a>"
        "<a href='report-underpriced.html'>Most underpriced</a>"
        "<a href='learn.html'>Learn the basics</a>"
        "<a href='index.html#early-access'>Get access</a>"
        "</nav></div>"
        "<p class='disclaim'>Estimates only — a screening tool, not financial or investment "
        "advice. Always confirm with a lender and an inspection. Fair Housing: our scoring "
        "never uses demographic or neighborhood-quality signals.</p>"
        "</div></footer>"
    )


# ── Netlify waitlist <form> — markup PRESERVED EXACTLY (name/method/data-netlify/
#    honeypot/hidden form-name/bot-field/action/email-required). Appearance only is
#    styled via the .wl wrapper. Never change selling logic / the $19.99 price. ──
WAITLIST = (
    "<section class='sec' id='early-access'><div class='wrap'>"
    "<div class='wl reveal'>"
    "<div class='key'>Founding access</div>"
    "<h2>Be first when we open the doors.</h2>"
    "<p>Founding members lock in <span class='price'>$19.99/mo</span> for a full year — "
    "rising to $49.99/mo soon. No spam, just your invite.</p>"
    "<form name='waitlist' method='POST' data-netlify='true' netlify-honeypot='bot-field' action='/thanks.html'>"
    "<input type='hidden' name='form-name' value='waitlist' />"
    "<p style='display:none'><label>Leave blank: <input name='bot-field' /></label></p>"
    "<input type='email' name='email' placeholder='you@email.com' required aria-label='Your email address' />"
    "<button type='submit'>Join the waitlist →</button>"
    "</form>"
    "<p class='fine'>We email you when your city opens. Unsubscribe anytime.</p>"
    "</div></div></section>"
)


# ──────────────────────────────────────────────────────────────────────────────
# THE CINEMATIC HERO — the dark, dusk-house homepage opener (owner preview build).
# Lifted from design_preview/share_hero/index.html (built by Juliet) and folded in
# as a generator function. EVERY selector is scoped under `.ch-hero` and prefixed
# `ch-` so it can NEVER collide with the rest of the Ivory & Gold site (which uses
# .hero, .bar, .nav, .stage, .smoke, etc. for OTHER things). The CSS is injected
# into <head> for index.html ONLY (via extra_head), the same disciplined way the
# feature galaxy was wired. Brand tokens are reused (gold/ivory/Cormorant) — only
# the NEW dark-field values this section needs are declared here.
#
# Motion honours prefers-reduced-motion (freezes to a still, elegant frame).
# The dusk photo ships to site/assets/hero_house.jpg and is referenced site-relative.
# ──────────────────────────────────────────────────────────────────────────────
CINEMATIC_HERO_CSS = """
<style>
 /* ===== CINEMATIC HERO — scoped under .ch-hero, classes prefixed ch- ===== */
 .ch-hero{position:relative;min-height:100vh;min-height:100svh;display:flex;
   flex-direction:column;overflow:hidden;isolation:isolate;background:#0C1320;
   color:#F6F1E7;--ch-field-tint:12,19,32;--ch-glow:46,140,98;
   --ch-ease:cubic-bezier(.16,.84,.34,1)}
 .ch-hero a{text-decoration:none}

 /* 0 · POSTER SURFACE — the couple still (golden hour). Sits at the very bottom
    of the stack and is what shows for reduced-motion + slow connections (the
    <video> paints over it once it can autoplay). Switched from hero_house.jpg to
    hero_couple_poster.jpg so the still fallback matches the video for consistency.
    Slow Ken-Burns push kept; disabled under reduced-motion below. */
 .ch-img{position:absolute;inset:0;z-index:0;
   background-image:url("assets/hero_couple_poster.jpg");
   background-size:cover;background-position:50% 38%;
   transform:scale(1.08);will-change:transform;
   animation:ch-kb 30s ease-in-out infinite alternate}
 @keyframes ch-kb{from{transform:scale(1.08) translate(0,0)}
   to{transform:scale(1.15) translate(-1.2%,-1.4%)}}

 /* 0b · the cinematic HERO VIDEO — full-bleed, muted, autoplay, looped. Bottom
    visible layer: paints over the poster surface, BEHIND every grade/smoke/grain/
    scrim/fade/text layer (all z-index >= 1). object-fit:cover keeps the frame full.
    NEW sunny clip (2026-06-21): a wide shot of the WHOLE two-storey house with the
    couple walking up the path. The house sits centred and slightly HIGH in the frame,
    so object-position is biased toward centre/upper (50% 38%): on desktop (≈1.6:1 vs
    the 16:9 source) cover crops the SIDES, full height/roofline kept; the upper bias
    just guarantees the roofline never clips. On portrait phones cover crops hard to a
    centre vertical strip — the upper bias keeps the house body + roof in view instead
    of zooming down to the path/feet. Owner ask: "FULL HOUSE visible at the start." */
 .ch-vid{position:absolute;inset:0;z-index:0;width:100%;height:100%;
   object-fit:cover;object-position:50% 38%;pointer-events:none}

 /* 2 · LIGHT warm grade (owner: "keep the picture LIGHT — I like the sunlight").
    The heavy navy darkening pillar is GONE. What's left is (a) a SOFT, feathered
    shade pillar ONLY behind the left text column — much lighter than before and
    fully clear by ~46% of the frame, so ~70%+ of the footage stays bright and
    sunny; and (b) a faint GOLDEN warmth wash so the sunlit footage reads premium
    and golden-hour, not flat. No more full-frame navy tint, no dark top/bottom
    pillars (the seam blend is handled lower, in .ch-scrim/.ch-fade). */
 .ch-grade{position:absolute;inset:0;z-index:1;pointer-events:none;
   background:
     /* localized text-column shade — left only, DEEPER + more defined behind the
        words (owner: "make the fonts readable"), but still FEATHERED so it fades to
        clear by ~mid-frame. The left edge is meaningfully darker now (.66 vs .40)
        so ivory letters always have a calm shadow panel to sit on; by ~50% it's
        gone, so the lit house / couple / golden sky on the RIGHT stay bright. */
     /* gentle supporting left feather (lightened 2026-06-21 so it sums with the new
        single .ch-scrim wash into ONE smooth gradient, not a stacked dark slab). */
     linear-gradient(90deg, rgba(var(--ch-field-tint),.30) 0%, rgba(var(--ch-field-tint),.22) 24%,
       rgba(var(--ch-field-tint),.12) 44%, rgba(var(--ch-field-tint),.04) 58%, transparent 70%),
     /* warm golden-hour wash — adds sunlight glow, no darkening */
     radial-gradient(120% 90% at 64% 30%, rgba(var(--ch-glow),.10) 0%, transparent 56%)}

 /* 3 · warm light-mist (transform/opacity only => GPU). CUT WAY BACK (owner wants
    clean sunlight, not haze) — was .28, now a barely-there warm sparkle so the
    footage stays clean. mix-blend:screen so it only ADDS faint light, never dims. */
 .ch-smoke{position:absolute;inset:-20% -10%;z-index:2;pointer-events:none;
   mix-blend-mode:screen;opacity:.12}
 .ch-smoke span{position:absolute;border-radius:50%;filter:blur(50px);
   background:radial-gradient(circle at 50% 50%,
     rgba(var(--ch-glow),.16) 0%, rgba(246,241,231,.10) 40%, rgba(255,255,255,0) 72%);
   will-change:transform,opacity}
 .ch-smoke .s1{width:48vw;height:48vw;left:8%;top:46%;animation:ch-drift1 42s var(--ch-ease) infinite}
 .ch-smoke .s2{width:40vw;height:40vw;left:58%;top:50%;animation:ch-drift2 54s var(--ch-ease) infinite}
 .ch-smoke .s3{width:34vw;height:34vw;left:34%;top:58%;animation:ch-drift3 48s var(--ch-ease) infinite}
 .ch-smoke .s4{width:28vw;height:28vw;left:70%;top:30%;animation:ch-drift1 64s var(--ch-ease) infinite reverse}
 @keyframes ch-drift1{0%{transform:translate(0,0) scale(1);opacity:.30}
   50%{transform:translate(-6vw,-4vh) scale(1.18);opacity:.55}
   100%{transform:translate(0,0) scale(1);opacity:.30}}
 @keyframes ch-drift2{0%{transform:translate(0,0) scale(1.05);opacity:.24}
   50%{transform:translate(5vw,3vh) scale(.9);opacity:.46}
   100%{transform:translate(0,0) scale(1.05);opacity:.24}}
 @keyframes ch-drift3{0%{transform:translate(0,0) scale(.95);opacity:.26}
   50%{transform:translate(4vw,-5vh) scale(1.2);opacity:.5}
   100%{transform:translate(0,0) scale(.95);opacity:.26}}

 /* 4 · film grain — all but removed (owner: clean sunlight, no dirt/mood). Was
    .045 overlay; now a whisper so the image stays crisp and bright. */
 .ch-grain{position:absolute;inset:0;z-index:3;pointer-events:none;opacity:.014;
   background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>");
   mix-blend-mode:overlay}

 /* 5 · legibility scrim — RADICALLY lightened (owner: keep it sunny, not dark).
    The center darkening is gone. What remains: (a) a very soft top-left feather
    that supports the headline without dimming the frame, and (b) a GENTLE, warm
    bottom fade — no longer a near-black wall. The bottom now lands on a soft warm
    cream-grey so the sunlit hero melts into the ivory page below with no hard
    seam (the .best-wrap blend top was lightened to match). The lowest band is a
    light warm tone, not black, so the picture stays bright top-to-bottom. */
 /* 5 · legibility scrim — REBUILT 2026-06-21 (owner: "the black background does not
    work… make it readable, beautiful, elegant"). The old per-region dark BLOBS are
    gone. In their place: ONE smooth, elegant LEFT-SIDE gradient wash — darkest at the
    very-left edge, feathering to fully transparent by mid-frame — so the WHOLE left
    text column (eyebrow → headline → qualifier → kicker → subcopy) sits on a single
    gentle, even readable wash with NO hard ovals and NO visible edges. The right side
    (house, couple, garden, golden sky) stays bright and sunny. A faint bottom warm
    fade still melts the hero into the ivory page below (no hard seam). */
 .ch-scrim{position:absolute;inset:0;z-index:4;pointer-events:none;
   background:
     /* the single elegant left→transparent wash. Smooth multi-stop linear so it reads
        as one calm gradient, not a panel: firm at the edge for the words, gone by ~52%
        so the lit right side is untouched. */
     linear-gradient(90deg,
       rgba(var(--ch-field-tint),.62) 0%,
       rgba(var(--ch-field-tint),.54) 16%,
       rgba(var(--ch-field-tint),.42) 30%,
       rgba(var(--ch-field-tint),.26) 42%,
       rgba(var(--ch-field-tint),.12) 52%,
       transparent 64%),
     /* gentle warm bottom fade only — melts the hero foot into the ivory page below */
     linear-gradient(180deg, transparent 0%, transparent 62%,
       rgba(60,52,42,.16) 84%, rgba(232,222,205,.52) 100%)}

 /* 6 · BLURRED bottom band — a frosted strip along the lowest edge of the photo
    so it reads as depth softening into darkness (not a hard cutoff). The blur
    feathers in via a mask, and the same band carries the final fade to the
    constellation colour. Pure CSS, no motion (respects reduced-motion). */
 /* now feathers into a LIGHT warm cream (was near-black) so the sunlit hero stays
    bright at its foot and dissolves seamlessly into the ivory page below. */
 .ch-fade{position:absolute;left:0;right:0;bottom:0;height:34%;z-index:5;pointer-events:none;
   -webkit-backdrop-filter:blur(7px);backdrop-filter:blur(7px);
   background:linear-gradient(180deg, transparent 0%, rgba(226,216,200,.18) 46%,
     rgba(232,222,205,.62) 80%, rgba(238,229,213,.95) 100%);
   -webkit-mask-image:linear-gradient(180deg, transparent 0%, #000 50%, #000 100%);
   mask-image:linear-gradient(180deg, transparent 0%, #000 50%, #000 100%)}

 /* 6b · LIVE DATABASE STAT — lower-right proof panel over the video. Anchored to the
    open garden space on the right of the frame, vertically toward the lower third, so
    it's clear of the headline column (left) and the couple/house (centre). z-index 7 so
    it floats above the scrim/fade but below nothing it needs to. A soft radial backing
    + drop-shadow keep it readable on any moving frame WITHOUT a loud badge box. The
    number is brand forest-green→mint for on-video legibility; the label is a small
    letter-spaced ivory line with the same pulsing "live" pip as the map count stat. */
 .ch-stat{position:absolute;z-index:7;right:clamp(28px,4.4vw,72px);bottom:clamp(56px,11vh,128px);
   display:flex;flex-direction:column;align-items:flex-end;text-align:right;pointer-events:none;
   padding:14px 20px 16px;border-radius:16px;
   background:radial-gradient(120% 130% at 78% 40%, rgba(8,14,24,.42), rgba(8,14,24,.10) 62%, transparent 80%)}
 .ch-stat-num{font-family:"Cormorant Garamond",Georgia,serif;font-weight:600;
   font-size:clamp(2.9rem,5.2vw,4.4rem);line-height:.94;letter-spacing:.004em;color:#7BEEB0;
   text-shadow:0 1px 2px rgba(6,8,14,.85), 0 2px 14px rgba(6,8,14,.7), 0 0 26px rgba(26,106,72,.45)}
 .ch-stat-cap{display:inline-flex;align-items:center;gap:9px;margin-top:7px;
   font-family:"Inter";font-size:.685rem;font-weight:600;letter-spacing:.165em;text-transform:uppercase;
   color:#F1EAD9;text-shadow:0 1px 2px rgba(6,8,14,.8), 0 0 10px rgba(6,8,14,.6)}
 .ch-stat-dot{width:7px;height:7px;border-radius:50%;flex:none;background:#5BC78E;
   box-shadow:0 0 0 3px rgba(91,199,142,.22), 0 0 10px rgba(91,199,142,.85);
   animation:ch-stat-pulse 2.6s ease-in-out infinite}
 @keyframes ch-stat-pulse{0%,100%{opacity:.55}50%{opacity:1}}
 @media(prefers-reduced-motion:reduce){.ch-stat-dot{animation:none}}

 /* top bar */
 .ch-header{position:relative;z-index:10}
 .ch-bar{max-width:1180px;margin:0 auto;padding:30px 44px;display:flex;align-items:center;gap:18px}
 /* BRAND WORDMARK — owner: "make UNDERLISTED big" + "elegant again like CASCADE &
    COAL". Kept BIG and unmistakable, but refined to a graceful logotype: a LIGHTER
    Cormorant weight (500, not heavy 700) with GENEROUS airy tracking like the
    reference's letter-spaced top-left mark, bright ivory, a tight stacked dark
    text-shadow so it always holds on a sunlit patch, and a thin gold underline rule
    so it reads as a deliberate, expensive logotype — not body text. */
 /* BOLD CLASSIC FOREST GREEN (owner 2026-06-21: "give a classic BOLD green… make it
    very visible"). A deep, confident forest green (#123F2C) at a HEAVIER weight (700)
    so the logotype is unmistakable — reads as a confident brand mark, not faint text.
    Deep green can sink into a dark video frame, so it carries a tight IVORY micro-halo
    (4-way, hugs each letter) that lifts it off darker footage PLUS a soft dark drop for
    bright sunlit frames — so the bold green POPS on ANY frame. Elegant letter-spacing
    + the green->brick-red underline accent are kept. */
 .ch-wordmark{position:relative;font-family:"Cormorant Garamond",serif;font-weight:700;
   font-size:clamp(2.0rem,3.4vw,2.8rem);line-height:1;
   letter-spacing:.34em;text-transform:uppercase;color:#123F2C;padding:.06em 0 .16em .34em;
   text-shadow:
     0 0 1px rgba(248,244,236,.95), .6px .6px 0 rgba(248,244,236,.80),
     -.6px -.6px 0 rgba(248,244,236,.55), 0 1px 1px rgba(248,244,236,.55),
     0 2px 10px rgba(248,244,236,.42), 0 3px 16px rgba(6,18,12,.30)}
 .ch-wordmark::after{content:"";position:absolute;left:.34em;bottom:0;
   width:1.5em;height:2px;border-radius:2px;
   background:linear-gradient(90deg,#123F2C 58%,#C8443F);
   box-shadow:0 0 3px rgba(248,244,236,.7),0 1px 3px rgba(6,8,14,.4)}
 .ch-nav{margin-left:auto;display:flex;align-items:center;gap:34px}
 .ch-nav a{font-family:"Inter";color:#D8D1C2;font-weight:500;font-size:.72rem;
   letter-spacing:.18em;text-transform:uppercase;transition:color .25s}
 .ch-nav a:hover{color:#3FB07A}
 .ch-navtoggle{display:none}

 /* LEFT-ANCHORED headline stage — the cover copy lives in a confident column on
    the LEFT of the frame (owner: "you can use these sides too, not everything has
    to be in the middle"). This fills the previously-dead left space and lets the
    lit dusk house on the RIGHT show through. The stage is a max-width container so
    the column is pinned left and the copy never drifts over the brightest window. */
 .ch-stage{position:relative;z-index:6;flex:1;display:flex;align-items:center;
   justify-content:flex-start}
 .ch-copy{max-width:1180px;width:100%;margin:0 auto;padding:2vh 44px 7vh;
   text-align:left;display:flex;flex-direction:column;align-items:flex-start}
 /* the headline measure is WIDE (well beyond the old 16ch) so the lead line breaks
    naturally across the frame into a few strong lines instead of a thin centre strip,
    but the whole copy column is held to ~the left half so the house breathes right. */
 .ch-copy > *{max-width:min(720px,58vw)}
 /* EYEBROW — the small-caps label above the headline. Refined to echo the
    "CASCADE & COAL" label: airier tracking (.38em), a calmer medium weight, and the
    refined gold so it reads as an elegant kicker, not a loud tag. */
 .ch-eyebrow{display:inline-flex;align-items:center;gap:16px;
   font-family:"Inter";font-size:.70rem;font-weight:600;letter-spacing:.38em;
   text-transform:uppercase;color:#5BC78E;
   text-shadow:0 1px 2px rgba(6,8,14,.72)}
 .ch-eyebrow::before{content:"";width:0}
 .ch-eyebrow::after{content:"";width:46px;height:1px;
   background:linear-gradient(90deg, rgba(var(--ch-glow),.85), transparent)}
 /* text-shadow does the heavy lifting now that the background is bright: a tight
    dark halo + a soft wider one so ivory letters stay crisp over sunlit spots,
    WITHOUT darkening the whole image. */
 .ch-headline{font-family:"Cormorant Garamond",serif;font-weight:500;
   font-size:clamp(2.7rem,6.4vw,5.6rem);line-height:1.02;letter-spacing:.005em;
   margin:.34em 0 0;color:#FBF7EE;
   text-shadow:0 1px 1px rgba(6,8,14,.78), 0 2px 6px rgba(6,8,14,.60), 0 0 30px rgba(6,8,14,.40)}
 /* LONG/differentiated variant — three deliberately DIFFERENT typographic parts so
    the eye moves (owner: "differentiate your text"), instead of one monotone block.
    Measure is wide (no narrow ch-cap) so the lead spans the frame in ~2 lines. */
 .ch-headline.long{display:block;margin:.18em 0 0;letter-spacing:0;max-width:none}
 /* 1 · LEAD — the dominant phrase. Largest size, ivory, graceful leading. Owner:
    "elegant again like CASCADE & COAL." Dropped from a heavy 600 to a refined 500
    so the Cormorant reads like an expensive editorial serif, not a bold slab; a
    hair MORE line-height (1.06) and a whisper of positive tracking (.004em) so the
    long phrase breathes and feels calm. Legibility kept by the tight stacked dark
    halo + the localized shade panel behind the left column. */
 .ch-headline .ch-hl-lead{display:block;font-weight:500;
   font-size:clamp(2.4rem,5.6vw,4.9rem);line-height:1.06;color:#FBF7EE;
   letter-spacing:.004em;
   /* tight, clean dark halo (not a soft glow) so each elegant letter holds against
      any bright spot behind it — close 1–2px shadows do the work, one wider pass. */
   text-shadow:0 1px 1px rgba(6,8,14,.80), 0 2px 6px rgba(6,8,14,.62), 0 0 28px rgba(6,8,14,.38)}
 /* 2 · QUALIFIER — secondary scale, lighter, calmer ivory. Steps DOWN from the
    lead so it reads as supporting detail, not a headline of its own. "all 50 states"
    keeps the gold accent so the differentiator number still pops. */
 /* QUALIFIER — "Nationwide, in cities across all 50 states." The ugly dark BLOB
    backing (::before) is REMOVED 2026-06-21; the line now sits on the single elegant
    left-side wash like the rest of the column. Brighter ivory + a firm tight stacked
    halo keep it crisp; the green accent word ("across all 50 states.") is brightened
    below so the differentiator still reads on the sunny frame. */
 .ch-headline .ch-hl-qual{display:block;position:relative;
   font-weight:500;font-style:normal;
   font-size:clamp(1.34rem,2.65vw,2.2rem);line-height:1.3;color:#FCF8EF;
   margin-top:.46em;letter-spacing:.006em;max-width:20ch;
   text-shadow:0 1px 1px rgba(6,8,14,.88), 0 1px 5px rgba(6,8,14,.72), 0 0 18px rgba(6,8,14,.50)}
 /* 3 · KICKER — the punchline gets its own emphasized gold-italic line (the luxe
    signature accent). Distinct size + italic so it lands as the closing statement. */
 /* KICKER — owner: "make it elegant AGAIN like CASCADE & COAL" (their gold ampersand).
    Moved OFF the heavy garnet red back to a refined, elegant GOLD — the hero's signature
    gold family (#E7C275→#C79A4B with a #F0CF82 highlight), brightened just enough to
    read on the sunny image. A graceful italic in a lighter weight (600, not 650) so it
    feels like a tasteful signature, not a shout. Kept legible by the lower-left shade
    panel + its own blurred backing + a firm stacked drop-shadow so the gold stays crisp
    on the bright path. This is the single load-bearing accent — calm, expensive gold. */
 /* KICKER — the single load-bearing punchline now carries the logo's BRICK RED (the
    most emphatic of the two brand accents), as a refined italic signature. A warm
    brick-red gradient that stays rich and readable on the sunny image, kept legible
    by the lower-left shade panel + its own blurred backing + a firm stacked shadow. */
 /* KICKER — the load-bearing punchline. REBUILT 2026-06-21 (owner: "I can't read it at
    all… make it readable, beautiful, elegant — this is a very important message"). The
    dark BLOB backing (::before) is REMOVED. Brick-red over bright moving video is the
    hard case, so the LINE is now warm IVORY in the elegant Cormorant italic (the most
    readable colour on video), with ONE brighter brick-red accent word (.ch-kr) for the
    brand pop. A tight 4-way dark micro-outline + soft drop keep the ivory crisp on any
    frame, sitting on the single left wash. Calm, elegant, unmistakably readable. */
 .ch-headline .ch-hl-kicker{display:block;position:relative;
   font-style:italic;font-weight:500;max-width:20ch;
   font-size:clamp(1.5rem,3.1vw,2.6rem);line-height:1.16;margin-top:.5em;
   color:#FCF7EC;
   text-shadow:0 1px 1px rgba(6,8,14,.92), .6px .6px 0 rgba(6,8,14,.55),
     -.6px -.6px 0 rgba(6,8,14,.45), 0 2px 6px rgba(6,8,14,.78), 0 0 20px rgba(6,8,14,.50)}
 /* the single brick-red accent inside the otherwise-ivory kicker — bright enough to
    read on the sunny garden, with the same tight dark micro-outline. */
 .ch-headline .ch-hl-kicker .ch-kr{font-style:italic;color:#FF9A8E;
   text-shadow:0 1px 1px rgba(6,8,14,.95), .6px .6px 0 rgba(6,8,14,.7),
     -.6px -.6px 0 rgba(6,8,14,.6), 0 2px 6px rgba(6,8,14,.85), 0 0 18px rgba(6,8,14,.55)}
 /* "all 50 states" — the differentiator number now carries the refined GOLD accent
    (matches the kicker), so the two gold phrases form one elegant focal thread that
    leads the eye to OUR message. Sits on the lower-left shade + qualifier panel, with
    a firm drop-shadow, so the gold reads crisply on the bright photo. A graceful
    italic, lighter weight (600) so it stays tasteful, not loud. */
 /* "all 50 states" — the differentiator now carries a refined FOREST-GREEN accent
    (matches the logo + the green eyebrow/wordmark), so green leads the eye and the
    brick-red kicker lands as the closing emphasis. A bright readable green so it
    holds on the sunny photo, with a firm drop-shadow. */
 /* "across all 50 states." — the differentiator, in a bright readable forest green so
    it reads cleanly on the sunny frame now that the dark blob is gone. A solid colour
    (not a faint gradient) + tight 4-way dark micro-outline so the green stays crisp. */
 .ch-headline .ch-hl-qual .ch-accent{font-style:italic;font-weight:700;color:#7BEEB0;
   text-shadow:0 1px 1px rgba(6,8,14,.95), .6px .6px 0 rgba(6,8,14,.75),
     -.6px -.6px 0 rgba(6,8,14,.6), 0 2px 5px rgba(6,8,14,.85), 0 0 16px rgba(6,8,14,.55)}
 /* legacy block accent kept for reversibility (was .ch-obvious on the cover) */
 .ch-headline .ch-obvious{display:block;font-style:italic;font-weight:600;color:#F0CF82;
   background:linear-gradient(92deg,#F5D88E,#D2A451,#F5D88E);
   -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;
   filter:drop-shadow(0 1px 1px rgba(6,8,14,.85)) drop-shadow(0 2px 5px rgba(6,8,14,.62)) drop-shadow(0 0 16px rgba(6,8,14,.40))}
 .ch-sub{font-family:"Inter";font-weight:450;font-size:clamp(1.04rem,2vw,1.2rem);
   line-height:1.6;color:#F4EEE0;max-width:42ch;margin:1.3em 0 0;
   /* smallest body line on a bright photo => the firmest tight halo of all */
   text-shadow:0 1px 1px rgba(6,8,14,.80), 0 1px 4px rgba(6,8,14,.62), 0 0 14px rgba(6,8,14,.44)}
 .ch-sub b{color:#FFFBF3;font-weight:650}
 .ch-sub i{font-style:italic;color:#BFE6CF}
 /* both hero buttons share ONE baseline (owner: "must be the same level"). The gold
    CTA sits in a small column with the "New to buying a house?" eyebrow floating ABOVE
    it; align-items:flex-end bottom-aligns the BUTTONS so they read as one clean row
    even with the eyebrow above the gold one. */
 .ch-actions{display:flex;align-items:flex-end;justify-content:flex-start;gap:18px;
   margin-top:2.2em;flex-wrap:wrap}

 /* DORMANT — frosted "What you get" value rail (removed from the hero 2026-06-20;
    CSS kept but unused for reversibility). */
 .ch-rail{position:relative;border-radius:18px;padding:22px 22px 20px;
   background:linear-gradient(180deg, rgba(12,19,32,.62), rgba(8,13,22,.72));
   -webkit-backdrop-filter:blur(12px) saturate(125%);backdrop-filter:blur(12px) saturate(125%);
   border:1px solid rgba(246,241,231,.16);
   box-shadow:0 30px 70px -28px rgba(0,0,0,.7), inset 0 1px 0 rgba(246,241,231,.10);
   --r-green:#5FD89C;--r-red:#E8917F;--r-blue:#7FB4E6}
 .ch-rail-head{display:flex;align-items:center;gap:9px;
   font-family:"Inter";font-size:.62rem;font-weight:700;letter-spacing:.22em;
   text-transform:uppercase;color:#5BC78E;margin-bottom:13px}
 .ch-rail-head::after{content:"";flex:1;height:1px;
   background:linear-gradient(90deg, rgba(var(--ch-glow),.6), transparent)}
 .ch-rail-head .dot{width:6px;height:6px;border-radius:50%;background:#5FD89C;
   box-shadow:0 0 9px rgba(95,216,156,.9)}
 .ch-rail-grid{display:grid;grid-template-columns:1fr 1fr;gap:9px 11px}
 .ch-feat{display:flex;align-items:center;gap:10px;min-width:0}
 .ch-feat .fi{flex:0 0 30px;width:30px;height:30px;border-radius:9px;display:grid;
   place-items:center;background:rgba(246,241,231,.05);border:1px solid rgba(246,241,231,.12)}
 .ch-feat .fi svg{width:17px;height:17px}
 .ch-feat.g .fi{color:var(--r-green);border-color:rgba(95,216,156,.34);background:rgba(95,216,156,.08)}
 .ch-feat.r .fi{color:var(--r-red);border-color:rgba(232,145,127,.34);background:rgba(232,145,127,.08)}
 .ch-feat.b .fi{color:var(--r-blue);border-color:rgba(127,180,230,.34);background:rgba(127,180,230,.08)}
 .ch-feat .ft{min-width:0}
 .ch-feat .ft b{display:block;font-family:"Inter";font-weight:600;font-size:.78rem;
   color:#F6F1E7;line-height:1.2;letter-spacing:.005em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
 .ch-feat .ft span{display:block;font-family:"Inter";font-size:.64rem;color:#A9A293;line-height:1.25;margin-top:1px}
 .ch-rail-foot{margin-top:14px;padding-top:13px;border-top:1px solid rgba(246,241,231,.12);
   display:flex;align-items:center;gap:8px;font-family:"Inter";font-size:.66rem;color:#B7B0A1}
 .ch-rail-foot .pip{flex:0 0 auto;display:inline-flex;align-items:center;gap:5px;
   font-weight:700;color:#5FD89C;letter-spacing:.02em}
 .ch-btn{font-family:"Inter";font-weight:600;font-size:.78rem;letter-spacing:.16em;
   text-transform:uppercase;padding:16px 30px;border-radius:2px;display:inline-flex;
   align-items:center;gap:11px;transition:.3s var(--ch-ease);border:1px solid transparent}
 .ch-btn .arr{transition:transform .3s var(--ch-ease)}
 /* buttons can sit on a bright patch — give each a readable backing so the label
    and border hold: the primary gets a faint dark glass fill + brighter gold text,
    the ghost gets a firmer border + a subtle text-shadow. */
 .ch-btn-primary{color:#5BC78E;border-color:rgba(var(--ch-glow),.85);
   background:linear-gradient(180deg, rgba(var(--ch-field-tint),.30), rgba(var(--ch-field-tint),.20));
   text-shadow:0 1px 2px rgba(6,8,14,.55)}
 .ch-btn-primary:hover{border-color:#5BC78E;background:rgba(var(--ch-glow),.22);
   box-shadow:0 0 34px -8px rgba(var(--ch-glow),.6);color:#fff}
 .ch-btn-primary:hover .arr{transform:translateX(6px)}
 .ch-btn-ghost{color:#F0EADB;border-color:rgba(246,241,231,.55);
   background:rgba(var(--ch-field-tint),.18);text-shadow:0 1px 2px rgba(6,8,14,.55)}
 .ch-btn-ghost:hover{color:#FFFBF3;border-color:rgba(246,241,231,.8);background:rgba(246,241,231,.10)}

 /* #1 GOLD CTA — the first-time-buyer "Learn how it works" button. Gold is declared
    ONLY here (--ch-gold local to this rule) so it can never leak elsewhere on the
    page. ~1.5px gold border, a soft gold fill + glow over the dark-glass backing,
    slightly larger padding, a bright-gold label with a dark text-shadow so it holds
    over the bright sunny video. This out-ranks "See the deals" by styling alone. */
 .ch-btn-gold{--ch-gold:#C79A4B;color:#F4D79A;
   border:1.5px solid var(--ch-gold);padding:18px 34px;border-radius:2px;
   background:
     linear-gradient(180deg, rgba(199,154,75,.26), rgba(199,154,75,.14)),
     linear-gradient(180deg, rgba(var(--ch-field-tint),.34), rgba(var(--ch-field-tint),.24));
   box-shadow:0 0 30px -10px rgba(199,154,75,.7), inset 0 1px 0 rgba(244,215,154,.18);
   text-shadow:0 1px 3px rgba(6,8,14,.7)}
 .ch-btn-gold:hover{color:#FFEEC4;border-color:#E2BE76;
   background:
     linear-gradient(180deg, rgba(199,154,75,.40), rgba(199,154,75,.22)),
     linear-gradient(180deg, rgba(var(--ch-field-tint),.34), rgba(var(--ch-field-tint),.24));
   box-shadow:0 0 44px -8px rgba(199,154,75,.85), inset 0 1px 0 rgba(244,215,154,.28)}
 .ch-btn-gold:hover .arr{transform:translateX(6px)}

 /* the tiny letter-spaced eyebrow sits in a small flex column directly over the
    gold button; it fades out when the story is open (JS toggles .is-open on it). */
 .ch-cta-stack{display:inline-flex;flex-direction:column;align-items:center;gap:7px}
 .ch-cta-eyebrow{font-family:"Inter";font-size:.62rem;font-weight:600;
   letter-spacing:.22em;text-transform:uppercase;color:#E8D9B6;
   text-shadow:0 1px 2px rgba(6,8,14,.6);transition:opacity .25s var(--ch-ease);
   white-space:nowrap}
 .ch-cta-eyebrow.is-open{opacity:0;pointer-events:none}

 /* #2 SECONDARY — "See the deals" demoted: green text, thin dim green border,
    no glow. Clearly clickable, visually ranked below the gold CTA. */
 /* height-matched to the gold CTA so both buttons are the SAME height in the row:
    same 18px vertical padding + 1.5px border box as .ch-btn-gold. */
 .ch-btn-secondary{color:#5BC78E;border:1.5px solid rgba(91,199,142,.45);
   padding:18px 30px;
   background:rgba(var(--ch-field-tint),.18);text-shadow:0 1px 2px rgba(6,8,14,.55)}
 .ch-btn-secondary:hover{color:#9FE6BE;border-color:rgba(91,199,142,.75);
   background:rgba(var(--ch-field-tint),.26)}
 .ch-btn-secondary:hover .arr{transform:translateX(6px)}

 /* (the old .ch-markline footer caption was removed 2026-06-20 — its two phrases
    ran together as mashed text and competed with the longer headline; the bottom
    edge is now calmest empty, melting into the fade.) */

 /* (the old .ch-scrollcue down-arrow + its keyframes were removed 2026-06-20 —
    the blurred, fading bottom edge IS the "there's more below" cue now.) */

 /* entrance motion */
 .ch-rise{opacity:0;transform:translateY(28px);animation:ch-rise 1.2s var(--ch-ease) forwards}
 .ch-d1{animation-delay:.20s}.ch-d2{animation-delay:.55s}.ch-d3{animation-delay:.95s}
 .ch-d4{animation-delay:1.30s}.ch-d5{animation-delay:1.60s}.ch-d6{animation-delay:1.90s}
 @keyframes ch-rise{to{opacity:1;transform:translateY(0)}}

 @media(max-width:780px){
   .ch-bar{padding:22px 22px}
   .ch-wordmark{font-size:clamp(1.6rem,7vw,2.0rem);letter-spacing:.30em;padding-left:.30em}
   .ch-wordmark::after{left:.30em}
   /* MOBILE FRAMING — portrait crops the 16:9 clip hard to a centre vertical strip.
      Lift the bias a little higher (50% 30%) so the house BODY + roofline read on a
      phone instead of zooming down to the path/feet (owner: full house must read). */
   .ch-vid,.ch-img{object-position:50% 30%;background-position:50% 30%}
   .ch-nav{gap:0}
   .ch-nav a{display:none}
   .ch-navtoggle{display:inline-flex;align-items:center;justify-content:center;
     width:42px;height:42px;border:1px solid rgba(246,241,231,.3);border-radius:8px;
     color:#F6F1E7;background:rgba(var(--ch-field-tint),.4)}
   .ch-navtoggle span{display:block;width:18px;height:1.5px;background:#F6F1E7;position:relative}
   .ch-navtoggle span::before,.ch-navtoggle span::after{content:"";position:absolute;left:0;
     width:18px;height:1.5px;background:#F6F1E7}
   .ch-navtoggle span::before{top:-6px}.ch-navtoggle span::after{top:6px}
   /* MOBILE: collapse to a LEFT-aligned single-axis stack (left reads cleanly on a
      narrow screen too), tighter padding, copy spans the full width. */
   .ch-copy{max-width:100%;text-align:left;align-items:flex-start;margin:0;padding:1vh 22px 13vh}
   .ch-copy > *{max-width:100%}
   .ch-eyebrow{justify-content:flex-start;font-size:.62rem;letter-spacing:.24em;gap:10px}
   .ch-eyebrow::after{width:30px}
   /* MOBILE: re-scale the three headline parts so they fit and keep their hierarchy */
   .ch-headline.long{margin:.1em 0 0}
   .ch-headline .ch-hl-lead{font-size:clamp(1.95rem,8.6vw,2.7rem);line-height:1.06}
   .ch-headline .ch-hl-qual{font-size:clamp(1.05rem,4.6vw,1.4rem);line-height:1.25;max-width:30ch}
   .ch-headline .ch-hl-kicker{font-size:clamp(1.3rem,5.6vw,1.7rem);line-height:1.14}
   /* MOBILE legibility (2026-06-21): the dark blob ::before panels are gone, and a
      narrow phone crops the bright doorway right under the wrapped kicker/qualifier.
      So on mobile these lines lean on a FIRMER stacked dark halo (the left wash alone
      may not reach a wrapped second line) — keeps the ivory kicker + green accent
      crisp without bringing back any black patches. */
   .ch-headline .ch-hl-kicker{text-shadow:0 1px 1px rgba(6,8,14,.96), .7px .7px 0 rgba(6,8,14,.7),
     -.7px -.7px 0 rgba(6,8,14,.6), 0 2px 7px rgba(6,8,14,.9), 0 0 22px rgba(6,8,14,.7)}
   .ch-headline .ch-hl-kicker .ch-kr{text-shadow:0 1px 1px rgba(6,8,14,.98), .7px .7px 0 rgba(6,8,14,.82),
     -.7px -.7px 0 rgba(6,8,14,.72), 0 2px 7px rgba(6,8,14,.95), 0 0 20px rgba(6,8,14,.78)}
   .ch-headline .ch-hl-qual .ch-accent{text-shadow:0 1px 1px rgba(6,8,14,.98), .7px .7px 0 rgba(6,8,14,.85),
     -.7px -.7px 0 rgba(6,8,14,.72), 0 2px 6px rgba(6,8,14,.92), 0 0 18px rgba(6,8,14,.72)}
   .ch-sub{max-width:38ch}
   .ch-actions{gap:12px;flex-direction:column;align-items:stretch;justify-content:flex-start}
   .ch-btn{width:100%;max-width:340px;justify-content:center;padding:17px 24px}
   /* on mobile the gold CTA + its eyebrow stack full-width like the other button */
   .ch-cta-stack{width:100%;max-width:340px;align-items:stretch;gap:8px}
   .ch-cta-eyebrow{text-align:center}
   .ch-btn-gold{padding:18px 24px}
   /* match the secondary to the gold so the stacked mobile buttons are identical */
   .ch-btn-secondary{padding:18px 24px}
   /* mobile scrim: KEEP IT LIGHT too. A slightly stronger left feather (the text
      column fills more of a narrow screen) but still a warm-cream bottom, never
      black, so the sunny photo melts into the ivory page below. */
   .ch-scrim{background:
     linear-gradient(90deg, rgba(var(--ch-field-tint),.52) 0%, rgba(var(--ch-field-tint),.34) 40%, rgba(var(--ch-field-tint),.12) 64%, transparent 82%),
     linear-gradient(180deg, rgba(var(--ch-field-tint),.18) 0%, transparent 24%,
       transparent 58%, rgba(232,222,205,.55) 100%)}
   .ch-fade{height:40%}
   /* MOBILE: hide the lower-right live stat. A portrait phone crops the clip hard to
      a centre strip (couple/house fill it) and the buttons stack tall — a floating
      stat would collide with people or controls. The page already shows a prominent
      live count lower down, so dropping it here keeps the cover clean. */
   .ch-stat{display:none}
 }

 @media(prefers-reduced-motion: reduce){
   /* No autoplay motion for users who opt out: HIDE the video entirely and let
      the still poster surface (.ch-img → hero_couple_poster.jpg) show through.
      Kill the Ken-Burns + smoke drift too so the hero is a calm still of the
      couple. */
   .ch-vid{display:none !important}
   .ch-smoke{opacity:.10}
   .ch-smoke span{animation:none !important}
   .ch-img{animation:none !important;transform:scale(1.06)}
   .ch-rise{animation:none !important;opacity:1;transform:none}
 }

 /* ===== "HOW IT WORKS" — UNFOLD-THE-STORY collapsible ======================
    The five story sections live inside #howitworks.hiw. We animate HEIGHT with
    the modern grid-rows trick (0fr → 1fr) so it slides smoothly with NO fixed
    max-height guess and NO clipped content. The wrapper carries NO background of
    its own — so when COLLAPSED, the cover's ivory foot (.ch-fade) flows straight
    into the free-tools section below with no hard seam.

    SEO/no-JS: the markup ships with `.hiw--open`, so crawlers and JS-off users
    get the fully-expanded story. The inline JS removes `.hiw--open` on load
    (collapsing it) only when JS is present — the calm default flow.            */
 .hiw{display:grid;grid-template-rows:0fr;
   transition:grid-template-rows .55s cubic-bezier(.22,.61,.36,1)}
 .hiw--open{grid-template-rows:1fr}
 /* the inner wrapper is the actual scroll/overflow box the grid row sizes */
 .hiw-inner{overflow:hidden;min-height:0}
 /* While COLLAPSED, hard-hide the inner so it can never catch focus, leave a
    stray pixel row, or paint a seam under the cover. Open state restores it. */
 .hiw:not(.hiw--open) .hiw-inner{visibility:hidden}
 .hiw--open .hiw-inner{visibility:visible}

 /* the "▲ Hide how it works" footer control — calm, on ivory, gold-on-hover */
 .hiw-hidebar{background:var(--ivory);text-align:center;padding:8px 20px 46px}
 .hiw-hide{font-family:"Inter",sans-serif;cursor:pointer;
   display:inline-flex;align-items:center;gap:9px;
   font-size:.74rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase;
   color:var(--ink-soft);background:var(--surface);
   border:1px solid var(--hair);border-radius:999px;padding:11px 22px;
   transition:color .2s,border-color .2s,background .2s,box-shadow .2s}
 .hiw-hide:hover{color:var(--gold);border-color:var(--gold);
   box-shadow:0 2px 14px rgba(26,106,72,.16)}
 .hiw-hide .chev{font-size:.62rem;line-height:1;color:var(--gold);
   transform:translateY(-1px)}
 .hiw-hide:focus-visible{outline:2px solid var(--gold);outline-offset:3px}

 @media(prefers-reduced-motion: reduce){
   /* opt-out users get an INSTANT toggle — no slide. */
   .hiw{transition:none}
 }
</style>"""


# ──────────────────────────────────────────────────────────────────────────────
# "SEE WHAT YOU GET" MAP — the compact, side-by-side layout inside #howitworks.
# The revealed story is laid out as a grid of MATCHED TILES on the ivory page
# (a real "map" you scan in one screen instead of scrolling five sections):
#   Row 1 : feature constellation (LEFT, its own DARK framed card) | how-we-find-them (RIGHT)
#   Row 2 : "four things…" (#why, LEFT) | "one home, three seconds" (#glance, RIGHT)
#   Row 3 : locked teaser (full-width)
# Two columns on desktop → ONE column on phones (≤860px).
#
# SEAM FIX: the constellation is dark and the rest is ivory. To kill the
# dark/light section seam, the constellation lives inside its OWN dark rounded
# CARD (.maptile--dark) that simply SITS on the ivory page — so every row reads
# as matched framed tiles. We neutralise the galaxy's full-bleed background-image,
# negative margins, and top-edge ::after blend WHEN it's inside the map.
#
# We also neutralise the inner sections' own full-bleed wrappers (.best-wrap,
# .glance-wrap, .teaser-wrap) and their .rule hairlines inside the map, so they
# stop drawing section backgrounds/dividers and become plain tile contents.
# Everything is scoped under `.hiw-map`, so nothing changes off the homepage.
# ──────────────────────────────────────────────────────────────────────────────
HIW_MAP_CSS = """
<style>
 /* ===== THE "SEE WHAT YOU GET" MAP — matched tiles on the ivory page ===== */
 .hiw-map{max-width:1180px;margin:0 auto;padding:var(--sp-1) 22px var(--sp-1);
   display:grid;grid-template-columns:1fr 1fr;gap:22px;align-items:stretch}
 .hiw-map .row-full{grid-column:1 / -1}

 /* a matched ivory tile — shares the UNIFIED card system (radius/shadow/border)
    so every tile + the free-tools cards read as ONE designed surface. Inner
    content is vertically centred so neither tile floats when the pair stretches
    to equal height. */
 .hiw-map .maptile{position:relative;background:var(--surface);
   border:1px solid var(--hair);border-radius:var(--r-card);
   padding:34px 32px;display:flex;flex-direction:column;justify-content:center;
   box-shadow:var(--card-shadow);
   transition:transform .18s var(--ease-card),box-shadow .18s var(--ease-card),border-color .18s}
 .hiw-map .maptile:hover{transform:var(--lift);box-shadow:var(--card-shadow-hover);
   border-color:rgba(26,106,72,.5)}
 @media(prefers-reduced-motion:reduce){.hiw-map .maptile:hover{transform:none}}
 .hiw-map .maptile-head{margin-bottom:18px}
 .hiw-map .maptile .kicker{margin-bottom:12px}
 .hiw-map .maptile h2{font-family:"Cormorant Garamond",Georgia,serif;font-weight:500;
   font-size:clamp(1.7rem,3vw,2.4rem);line-height:1.08;letter-spacing:.005em;
   margin:0;color:var(--ink)}
 .hiw-map .maptile h2 em{color:var(--gold);font-style:italic;font-weight:600}
 .hiw-map .maptile h2 .red{color:var(--deep-red);font-weight:600}
 .hiw-map .maptile .lead{font-family:"Inter",sans-serif;color:var(--ink-soft);
   font-size:.99rem;line-height:1.55;margin:12px 0 0}
 .hiw-map .maptile .lead b{color:var(--ink);font-weight:600}
 /* brand meaning-colours so the eye scans fast (green=deal, red=risk, blue=money) */
 .hiw-map .mk-green{color:var(--good);font-weight:600}
 .hiw-map .mk-red{color:var(--weak);font-weight:600}
 .hiw-map .mk-blue{color:#235E94;font-weight:600}

 /* ── the DARK constellation card (own framed tile → no dark/light seam) ── */
 /* the dark constellation tile keeps its dark surface but shares the SAME radius
    (var(--r-card), via .maptile) + the same shadow geometry, tuned darker so it
    belongs to the set rather than standing apart. */
 .hiw-map .maptile--dark{padding:0;overflow:hidden;border:1px solid rgba(46,140,98,.34);
   background:var(--ink-deep);
   box-shadow:0 24px 54px -26px rgba(0,0,0,.62), 0 2px 10px -4px rgba(0,0,0,.30), 0 0 0 1px rgba(46,140,98,.10)}
 .hiw-map .maptile--dark:hover{border-color:rgba(46,140,98,.5);
   box-shadow:0 34px 66px -26px rgba(0,0,0,.66), 0 4px 14px -5px rgba(0,0,0,.34), 0 0 0 1px rgba(46,140,98,.16)}
 /* inside the map, the galaxy stops being a full-bleed section: no negative pull,
    no cover photo, no top-edge blend — it's a self-contained tile. */
 .hiw-map .maptile--dark .galaxy{margin-top:0;padding:30px 22px 34px;overflow:hidden;
   background-image:
     radial-gradient(700px 420px at 50% 6%, rgba(46,140,98,.18), transparent 60%),
     radial-gradient(560px 420px at 12% 96%, rgba(63,184,160,.12), transparent 62%),
     radial-gradient(560px 420px at 92% 70%, rgba(46,140,98,.08), transparent 60%),
     linear-gradient(180deg, rgba(28,23,17,.92) 0%, rgba(19,16,11,.95) 60%, rgba(15,12,8,.97) 100%)}
 .hiw-map .maptile--dark .galaxy::after{display:none}      /* kill the cover-blend wash */
 .hiw-map .maptile--dark .galaxy-inner{max-width:none}
 .hiw-map .maptile--dark .g-head{margin-bottom:6px}
 .hiw-map .maptile--dark .g-head h2{font-size:clamp(1.6rem,2.6vw,2.2rem)}
 .hiw-map .maptile--dark .g-head p{font-size:.95rem;margin-top:10px}
 /* scale the ring to fit the narrower column (resize JS keeps node math correct) */
 .hiw-map .maptile--dark .stage{width:min(440px,82%);height:min(440px,82vw);margin:24px auto 6px}

 /* ── RIGHT tile: "Here's how we find them" (keeps ZIP box + live count) ──
    distribute the content over the full tile height: the headline/explainer sit
    at the top, the live count + ZIP box settle toward the bottom. So this tile
    fills its (stretched) height gracefully instead of floating a band of dead
    space below the button — and its head aligns with the dark tile's head. */
 /* the find-tile must let its inner .find stretch the full height (not centre it)
    so the foot can sit at the bottom. */
 .hiw-map .find-tile{justify-content:stretch}
 .hiw-map .find{display:flex;flex-direction:column;flex:1 1 auto}
 .hiw-map .find .find-foot{margin-top:auto;padding-top:8px}
 .hiw-map .find .how{font-family:"Inter",sans-serif;color:var(--ink-soft);
   font-size:.99rem;line-height:1.55;margin:12px 0 0}
 .hiw-map .find .how b{color:var(--ink);font-weight:600}
 .hiw-map .find .how .src{color:var(--gold-2);font-weight:600}
 /* the live database count is PROOF the product is real — so it's a confident
    hero-stat now: big elegant forest-GREEN Cormorant numerals, a soft green halo,
    a "live" pip, and a clear label. Sits inside the find tile (not moved out). */
 .hiw-map .find .countstat{margin:24px 0 4px;align-items:flex-start;padding:4px 0 0}
 .hiw-map .find .countstat::before{left:26%;top:42%;width:340px;height:150px;
   background:radial-gradient(circle, rgba(26,106,72,.20), transparent 66%)}
 .hiw-map .find .countstat .num{font-size:clamp(3.5rem,8vw,5.2rem);font-weight:600;
   color:var(--gold-bright);letter-spacing:.004em;
   text-shadow:0 1px 0 rgba(255,255,255,.5)}
 .hiw-map .find .countstat .cap{display:inline-flex;align-items:center;gap:9px;
   color:var(--gold-2);font-size:.74rem;letter-spacing:.18em;margin-top:6px}
 .hiw-map .find .countstat .cap::before{content:"";width:7px;height:7px;border-radius:50%;
   background:var(--good);box-shadow:0 0 0 3px rgba(26,143,90,.18),0 0 9px rgba(26,143,90,.7);
   flex:none;animation:cs-pulse 2.6s ease-in-out infinite}
 @keyframes cs-pulse{0%,100%{opacity:.55}50%{opacity:1}}
 @media(prefers-reduced-motion:reduce){.hiw-map .find .countstat .cap::before{animation:none}}
 .hiw-map .find .ziphunt{margin:22px 0 0;max-width:none}
 .hiw-map .find .zipform{justify-content:flex-start}
 .hiw-map .find .best-disclaim{margin:18px 0 0!important;text-align:left}

 /* ── compact "four things" list inside its tile (one scannable line each) ── */
 .hiw-map .why .why-list{max-width:none}
 .hiw-map .why .why-item{grid-template-columns:auto 1fr auto;gap:6px 16px;
   padding:14px 0;align-items:center}
 .hiw-map .why .why-item .ico{display:none}
 .hiw-map .why .why-item .no{font-size:1.5rem;padding-top:0}
 .hiw-map .why .why-item .txt h3{font-size:1.18rem;margin:0 0 2px}
 .hiw-map .why .why-item .txt p{font-size:.9rem;line-height:1.45}
 .hiw-map .why .why-item .seal{font-size:.66rem}
 @media(max-width:520px){.hiw-map .why .why-item .seal{display:none}}

 /* ── compact "one home, three seconds" glance card inside its tile ── */
 .hiw-map .glance .glance-card{max-width:none;margin:0}
 .hiw-map .glance .stat-grid{grid-template-columns:1fr 1fr;gap:18px}

 /* ── full-width teaser row: kill its own section wrapper/bg/rules ── */
 .hiw-map .teaser-row .teaser-wrap{background:none}
 .hiw-map .teaser-row .teaser-wrap>.rule,
 .hiw-map .teaser-row .teaser-wrap+.rule{display:none}
 .hiw-map .teaser-row .sec{padding:6px 0 10px}

 /* Inside the map, the inner sections must NOT re-draw their own full-bleed
    backgrounds, extra section padding, or hairline rules — the tile IS the frame. */
 .hiw-map .sec{padding:0}
 .hiw-map .wrap{padding:0;max-width:none}
 .hiw-map .rule{display:none}
 .hiw-map .best-wrap{background:none}
 .hiw-map .best-wrap>.sec{padding-top:0}
 .hiw-map .glance-wrap{background:none}
 /* re-hide the section headlines that the tiles now render themselves */
 .hiw-map .maptile .sec-head{text-align:left;max-width:none;margin:0 0 22px}

 /* ===== RESPONSIVE — phones stack to ONE tight column ===== */
 @media(max-width:860px){
   .hiw-map{grid-template-columns:1fr;gap:16px;padding:30px 16px 6px}
   .hiw-map .maptile{padding:26px 22px}
   .hiw-map .maptile--dark .galaxy{padding:24px 14px 28px}
   .hiw-map .glance .stat-grid{grid-template-columns:1fr 1fr;gap:16px}
 }
</style>"""


def cinematic_hero_section() -> str:
    """The dark cinematic homepage opener (dusk house + drifting smoke + the
    'made obvious' headline). Scoped under `.ch-hero`; its CSS is injected into
    <head> via CINEMATIC_HERO_CSS for index.html only. Buttons/nav point to real,
    existing site links so nothing is a dead end. Sits ABOVE the rest of the
    homepage — everything below it (feature galaxy, why, etc.) is unchanged."""
    return (
        "<section class='ch-hero'>"
        # layers — bottom to top:
        #  · .ch-img  = poster still surface (couple), the reduced-motion fallback
        #  · .ch-vid  = the hero VIDEO, paints over the poster, behind everything else
        #  · grade/smoke/grain/scrim/fade = legibility + atmosphere, ABOVE the video
        "<div class='ch-img'></div>"
        "<video class='ch-vid' autoplay muted loop playsinline preload='auto' "
        "poster='assets/hero_couple_poster.jpg'>"
        "<source src='assets/hero_couple.mp4' type='video/mp4'>"
        "</video>"
        "<div class='ch-grade'></div>"
        "<div class='ch-smoke'><span class='s1'></span><span class='s2'></span>"
        "<span class='s3'></span><span class='s4'></span></div>"
        "<div class='ch-grain'></div>"
        "<div class='ch-scrim'></div>"
        # blurred + fading bottom band: the photo melts into the dark constellation
        # below (this organic fade is the 'there's more' cue — no scroll arrow).
        "<div class='ch-fade'></div>"
        # top bar — real links: Browse→deals report, How it works→feature galaxy,
        # Pricing→founding-access waitlist block, Sign in→the live app.
        "<header class='ch-header'><div class='ch-bar'>"
        "<a class='ch-wordmark ch-rise ch-d1' href='index.html'>Underlisted</a>"
        "<nav class='ch-nav ch-rise ch-d1'>"
        "<a href='report-underpriced.html'>Browse</a>"
        # "How it works" no longer jumps to an anchor — it TOGGLES the #howitworks
        # story (data-hiw-toggle). href kept as a graceful no-JS fallback that still
        # lands on the (open-by-default) section. aria-controls/aria-expanded make it
        # a proper accessible disclosure control.
        "<a href='index.html#howitworks' data-hiw-toggle aria-controls='howitworks' "
        "aria-expanded='true'>How it works</a>"
        "<a href='index.html#early-access'>Pricing</a>"
        f"<a href='{APP_URL}'>Sign in</a>"
        "</nav>"
        "<button class='ch-navtoggle ch-rise ch-d1' aria-label='Menu'><span></span></button>"
        "</div></header>"
        # CENTERED cinematic cover — headline / eyebrow / subcopy / buttons, all
        # centred over the full-bleed dusk-house photo (no value panel; restored
        # 2026-06-20 to the clean 'made obvious' cover at the owner's request).
        "<div class='ch-stage'><div class='ch-copy'>"
        "<div class='ch-eyebrow ch-rise ch-d2'>Underpriced U.S. Homes</div>"
        # The #1 differentiator is the HERO HEADLINE, now LEFT-anchored and split into
        # THREE differentiated typographic parts (owner: "use the sides, differentiate
        # your text", 2026-06-20): (1) a dominant LEAD phrase, (2) a smaller QUALIFIER,
        # (3) the gold-italic KICKER punchline. Each part is a distinct size/weight so
        # the eye moves down a designed statement instead of a monotone block. The wide
        # measure lets the lead span the frame; the column sits left so the lit house
        # on the right shows through.
        "<h1 class='ch-headline long ch-rise ch-d3'>"
        "<span class='ch-hl-lead'>Foreclosures &amp; under-priced homes</span>"
        "<span class='ch-hl-qual'>Nationwide, in cities "
        "<span class='ch-accent'>across all 50 states.</span></span>"
        "<span class='ch-hl-kicker'>The deals other sites make you "
        "<span class='ch-kr'>dig for.</span></span>"
        "</h1>"
        # Subcopy is now the supporting plain-English / "made obvious" line — NO words
        # repeated from the headline above (owner: no duplicate sentences on the cover).
        "<p class='ch-sub ch-rise ch-d4'>Every home scored <b>0&ndash;100 in plain English</b> "
        "&mdash; green means a real deal, with fire &amp; flood risk and the true monthly cost "
        "made <i>obvious</i>.</p>"
        "<div class='ch-actions ch-rise ch-d5'>"
        # #2 action — "See the deals" demoted to the quiet SECONDARY style (green
        # text, thin dim border, no glow). Still clearly clickable, just visually
        # ranked below the gold first-time-buyer CTA. DOM order kept (this first).
        "<a class='ch-btn ch-btn-secondary' href='report-underpriced.html'>"
        "See the deals <span class='arr'>&rarr;</span></a>"
        # #1 action — the GOLD first-time-buyer CTA. A tiny letter-spaced eyebrow
        # ('New to buying a house?') sits directly over the button in a small flex
        # column. The button TOGGLES the #howitworks story; its label is now CONSTANT
        # ('Learn how it works →', no more 'Hide' flip — owner 2026-06-21). The eyebrow
        # hides while open. href is the no-JS fallback. The bottom '▲ Hide how it works'
        # control inside the unfolded story collapses it.
        "<span class='ch-cta-stack'>"
        "<span class='ch-cta-eyebrow' data-hiw-eyebrow>New to buying a house?</span>"
        "<a class='ch-btn ch-btn-gold' href='index.html#howitworks' data-hiw-toggle "
        "data-hiw-hero aria-controls='howitworks' aria-expanded='true'>"
        "<span class='hiw-lbl'>Learn how it works</span> <span class='arr'>&rarr;</span></a>"
        "</span>"
        "</div></div></div>"
        # LOWER-RIGHT live proof-stat (owner ask 2026-06-21): a tasteful, luxe
        # database count parked in the open garden space on the right — clear of the
        # left text column and the couple/house in the centre. Uses the REAL live
        # value (count_label(live_deal_count())) so it can never overstate. Green
        # Cormorant numerals (legible over the moving video) + a small letter-spaced
        # ivory label + the same "live" pulse pip used by the map's count stat, on a
        # soft radial backing so it reads on any frame. Hidden on small screens
        # (the page already carries a prominent count stat lower down).
        "<div class='ch-stat ch-rise ch-d5' aria-label='Homes in our database'>"
        f"<span class='ch-stat-num'>{count_label(live_deal_count())}</span>"
        "<span class='ch-stat-cap'><span class='ch-stat-dot'></span>"
        "homes scored &amp; tracked nationwide</span>"
        "</div>"
        # (The old .ch-markline bottom caption was removed 2026-06-20 — its two
        # phrases ran together as mashed text, and with the longer headline now
        # carrying the message the bottom edge stays calmest empty. The blurred
        # .ch-fade is the only "there's more below" cue.)
        "</section>"
    )


def _hero_value_rail() -> str:
    """DORMANT (not rendered as of 2026-06-20) — kept for reversibility only. The
    owner removed the hero value panel; cinematic_hero_section() no longer calls
    this. Its `.ch-rail*` CSS is likewise left defined but unused.

    The compact 'What you get' rail that sits over the photo on the RIGHT of the
    hero (stacks below the headline on mobile). A scannable, meaning-coloured list of
    the core features — the SAME items as the feature constellation — so the value is
    visible on screen one. Icons are tinted by meaning (green=deal, red=warning,
    blue=money tool) via the rail's own scoped colours."""
    # (icon-name, meaning-class g/r/b, label, tiny sub)
    feats = [
        ("gauge", "g", "Deal Score", "0&ndash;100, plain"),
        ("tag",   "g", "Below value", "savings, in $"),
        ("fire",  "r", "Fire &amp; flood", "FEMA risk"),
        ("up",    "b", "Can I afford it?", "your verdict"),
        ("bank",  "b", "True monthly cost", "all-in"),
        ("coin",  "b", "Real cash to keys", "down + closing"),
        ("home",  "g", "Foreclosures", "nationwide"),
        ("cal",   "b", "Free calculators", "no signup"),
    ]
    rows = ""
    for icon, cls, label, sub in feats:
        rows += (
            f"<span class='ch-feat {cls}'>"
            f"<span class='fi'>{svg(icon, w=17)}</span>"
            f"<span class='ft'><b>{label}</b><span>{sub}</span></span>"
            "</span>"
        )
    return (
        "<aside class='ch-rail ch-rise ch-d5' aria-label='Everything you get with Underlisted'>"
        "<div class='ch-rail-head'><span class='dot'></span>Everything you get</div>"
        f"<div class='ch-rail-grid'>{rows}</div>"
        "<div class='ch-rail-foot'><span class='pip'>&#9679; GREEN = a real deal</span>"
        "<span>red = watch out · blue = the money</span></div>"
        "</aside>"
    )


# ──────────────────────────────────────────────────────────────────────────────
# THE VALUE DASHBOARD — Concept B ("Dashboard Grid"), owner-approved 2026-06-20.
# Sits DIRECTLY under the cinematic hero: the whole offering at a glance so a lazy
# visitor can't miss the value. Three semantic colour lanes — GREEN = the deal /
# savings, RED = the warnings, BLUE = the money tools — with GOLD "then check /
# then decide" flow arrows tying them together, and the closing payoff line.
#
# EVERY selector is scoped under `.vdash` and prefixed `vd-` so it can NEVER
# collide with the rest of the Ivory & Gold site (or the .ch- hero / .galaxy).
# It reuses the site brand tokens (--gold, --ink, --surface, --hair, --muted,
# --faint, --r, --shadow*) and only declares the NEW semantic green/red/blue
# washes it needs. CSS injected into <head> for index.html ONLY via extra_head,
# concatenated after CINEMATIC_HERO_CSS — same discipline as the hero + galaxy.
#
# Lifted from design_preview/value_map_B.html. Compact on desktop (parallel
# lanes, ~one screen); on mobile the three lanes stack with the gold arrows
# rotated to point DOWN (value_map_B_mobile behaviour).
# ──────────────────────────────────────────────────────────────────────────────
VALUE_DASHBOARD_CSS = """
<style>
 /* ===== VALUE DASHBOARD (Concept B) — scoped .vdash, classes prefixed vd- ===== */
 .vdash{padding:54px 24px 64px;position:relative;
   --vd-green:#1A8F5A;--vd-green-soft:rgba(26,143,90,.10);--vd-green-line:rgba(26,143,90,.40);--vd-green-wash:rgba(26,143,90,.05);
   --vd-red:#C0392B;--vd-red-soft:rgba(192,57,43,.10);--vd-red-line:rgba(192,57,43,.38);--vd-red-wash:rgba(192,57,43,.045);
   --vd-blue:#2C6FB0;--vd-blue-soft:rgba(44,111,176,.10);--vd-blue-line:rgba(44,111,176,.40);--vd-blue-wash:rgba(44,111,176,.05);
   --vd-shadow-sm:0 14px 30px -18px rgba(60,44,20,.26)}
 /* (removed 2026-06-20) the thin gold seam-rule under the hero is gone — we now
    want a seamless dark→dark blend, not a hard line. Left as a no-op so the
    dormant section can be re-enabled without bringing the seam back. */
 .vdash::before{content:none}
 .vd-wrap{max-width:1140px;margin:0 auto}
 .vd-head{text-align:center;max-width:720px;margin:0 auto 26px}
 .vd-kicker{font-family:"Inter";font-size:.72rem;font-weight:600;letter-spacing:.22em;
   text-transform:uppercase;color:var(--gold-2);margin-bottom:13px;display:inline-flex;align-items:center;gap:9px}
 .vd-kicker .vd-dot{width:6px;height:6px;border-radius:50%;background:var(--vd-green);
   box-shadow:0 0 10px rgba(26,143,90,.8)}
 .vd-head h2{font-family:"Cormorant Garamond",Georgia,serif;font-weight:500;
   font-size:clamp(1.9rem,4.4vw,2.9rem);line-height:1.08;color:var(--ink);margin:0}
 .vd-head h2 em{color:var(--gold);font-style:italic}
 .vd-head p{font-family:"Inter";color:var(--muted);font-size:1.02rem;margin:13px auto 0;max-width:54ch}

 /* three lanes + flow arrows between them */
 .vd-board{display:grid;grid-template-columns:1fr auto 1fr auto 1fr;gap:0 14px;
   align-items:stretch;max-width:1080px;margin:26px auto 0}
 .vd-lane{border-radius:var(--r-lg,22px);padding:18px 16px 20px;border:1px solid var(--vd-lane-line);
   background:linear-gradient(180deg,var(--vd-lane-wash),var(--surface) 70%);position:relative}
 .vd-lane.vd-green{--vd-lane-c:var(--vd-green);--vd-lane-soft:var(--vd-green-soft);--vd-lane-line:var(--vd-green-line);--vd-lane-wash:var(--vd-green-wash)}
 .vd-lane.vd-red{--vd-lane-c:var(--vd-red);--vd-lane-soft:var(--vd-red-soft);--vd-lane-line:var(--vd-red-line);--vd-lane-wash:var(--vd-red-wash)}
 .vd-lane.vd-blue{--vd-lane-c:var(--vd-blue);--vd-lane-soft:var(--vd-blue-soft);--vd-lane-line:var(--vd-blue-line);--vd-lane-wash:var(--vd-blue-wash)}
 .vd-lane::before{content:"";position:absolute;left:0;right:0;top:0;height:3px;border-radius:3px 3px 0 0;background:var(--vd-lane-c)}

 .vd-lane-head{display:flex;align-items:center;gap:10px;margin-bottom:4px}
 .vd-lane-head .vd-step{flex:0 0 26px;width:26px;height:26px;border-radius:50%;display:grid;place-items:center;
   font-family:"Inter";font-weight:700;font-size:.8rem;color:#fff;background:var(--vd-lane-c)}
 .vd-lane-head h3{font-family:"Cormorant Garamond",Georgia,serif;font-weight:600;font-size:1.4rem;
   color:var(--vd-lane-c);line-height:1.05;margin:0}
 .vd-lane-sub{font-family:"Inter";font-size:.8rem;color:var(--muted);margin:2px 0 14px 36px}

 /* mini-card inside a lane */
 .vd-mini{display:flex;gap:12px;align-items:flex-start;background:var(--surface);
   border:1px solid var(--hair-soft,rgba(30,26,22,.10));border-radius:13px;padding:13px;
   box-shadow:var(--vd-shadow-sm);margin-bottom:11px}
 .vd-mini:last-child{margin-bottom:0}
 .vd-ico{flex:0 0 38px;width:38px;height:38px;border-radius:11px;display:grid;place-items:center;
   background:var(--vd-lane-soft);border:1px solid var(--vd-lane-line)}
 .vd-ico svg{width:21px;height:21px;color:var(--vd-lane-c)}
 /* illustrated raster icons (gold-ringed full-colour art): drop the tint frame so
    the illustration reads true; let the icon sit a touch larger for presence. */
 .vd-ico.vd-illus{flex:0 0 42px;width:42px;height:42px;background:transparent;border:0;
   border-radius:0;overflow:visible}
 .vd-ico.vd-illus .vd-illus-img{width:42px;height:42px;display:block;
   filter:drop-shadow(0 4px 9px rgba(60,44,20,.18))}
 .vd-body{min-width:0;flex:1}
 .vd-body .vd-lbl{display:block;font-family:"Inter";font-weight:600;font-size:.86rem;color:var(--ink);line-height:1.2}
 .vd-body .vd-val{display:block;font-family:"Cormorant Garamond",serif;font-weight:600;font-size:1.5rem;
   line-height:1.05;color:var(--vd-lane-c);margin-top:2px;font-variant-numeric:tabular-nums}
 .vd-body .vd-val.vd-pos{color:var(--vd-green)}
 .vd-body .vd-note{display:block;font-family:"Inter";font-size:.76rem;color:var(--muted);margin-top:3px;line-height:1.4}
 .vd-chip{display:inline-block;margin-top:6px;font-family:"Inter";font-size:.62rem;font-weight:700;
   letter-spacing:.04em;padding:4px 9px;border-radius:999px;background:var(--vd-lane-soft);color:var(--vd-lane-c)}

 /* gold flow arrow between lanes */
 .vd-flow{align-self:center;display:flex;flex-direction:column;align-items:center;gap:6px;width:42px}
 .vd-flow svg{width:30px;height:30px;color:var(--gold)}
 .vd-flow span{font-family:"Inter";font-size:.6rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
   color:var(--faint);text-align:center;line-height:1.2}

 /* the payoff line tying it together */
 .vd-payoff{max-width:760px;margin:30px auto 0;text-align:center;
   background:radial-gradient(120% 150% at 50% -10%,#FCF3DF,var(--surface) 62%);
   border:1px solid rgba(26,106,72,.4);border-radius:var(--r-lg,22px);padding:22px 26px;
   box-shadow:var(--shadow,0 30px 64px -32px rgba(60,44,20,.30))}
 .vd-payoff p{font-family:"Inter";font-size:1.02rem;color:var(--ink-soft,#3A332B);margin:0;line-height:1.55}
 .vd-payoff b{color:var(--gold-2)}

 /* CTA buttons — clean placeholders, real links */
 .vd-ctarow{display:flex;flex-wrap:wrap;gap:13px;justify-content:center;margin:24px auto 0}
 .vd-btn{font-family:"Inter";display:inline-flex;align-items:center;gap:9px;text-decoration:none;cursor:pointer;
   padding:15px 28px;border-radius:13px;font-weight:600;font-size:1rem;border:0;transition:transform .2s,box-shadow .2s}
 .vd-btn-fill{color:#FFFBF1;background:linear-gradient(150deg,var(--gold-bright,#1F7A53),var(--gold) 78%);
   box-shadow:0 18px 34px -16px rgba(14,58,42,.55),inset 0 1px 0 rgba(255,255,255,.4)}
 .vd-btn-fill:hover{transform:translateY(-1px);box-shadow:0 22px 40px -16px rgba(14,58,42,.62),inset 0 1px 0 rgba(255,255,255,.4)}
 .vd-btn-line{color:var(--ink);border:1px solid var(--hair);background:var(--surface)}
 .vd-btn-line:hover{border-color:rgba(26,106,72,.6)}

 /* MOBILE: lanes stack, gold arrows rotate to point DOWN */
 @media(max-width:880px){
   .vdash{padding:44px 18px 52px}
   .vd-board{grid-template-columns:1fr;gap:0;max-width:480px}
   .vd-flow{flex-direction:row;width:auto;gap:10px;justify-content:center;padding:10px 0}
   .vd-flow svg{transform:rotate(90deg);width:26px;height:26px}
   .vd-lane{padding:16px 14px 18px}
   .vd-btn{width:100%;max-width:340px;justify-content:center}
 }
</style>"""


def vd_img(name: str, alt: str = "") -> str:
    """An illustrated raster icon (the nano-banana gold-ringed set) for a value-
    dashboard card. These are full-colour illustrations that read as premium and
    friendly; the `.vd-ico.vd-illus` CSS drops the tint-box so the art shows true."""
    return (f"<img class='vd-illus-img' src='assets/icons/{name}.png' "
            f"alt='{alt}' width='34' height='34' loading='lazy' decoding='async'>")


def icon_img(name: str, alt: str = "") -> str:
    """An illustrated raster icon for the free-tools cards / hub. Same gold-ringed
    art as the value dashboard; the card's `.ico.illus` CSS drops the tint frame."""
    return (f"<img src='assets/icons/{name}.png' alt='{alt}' "
            f"width='62' height='62' loading='lazy' decoding='async'>")


def feature_grid_section() -> str:
    """STATIC full-colour feature grid (#why-grid).

    Companion to the spinning 'Why Underlisted' constellation: that one animates
    line-icons; THIS one shows the nano-banana illustrated art at full colour in a
    calm, premium 3-up grid (responsive to 1–2). Each card = one illustrated icon
    + plain-English label + one-line subtitle.

    Notes (Juliet): credit/foreclosure/agent art has TINY labels baked INSIDE the
    illustration; sized at 58px they read as part of the art, not as duplicate text.
    The credit card links to the learn page (no fake /credit calculator exists).
    """
    # (icon, headline, subtitle, optional href→existing page)
    items = [
        ("afford", "Can I afford it?", "Your income, cash &amp; debts → green, amber or red.",
         "home-affordability-calculator.html"),
        ("risk", "Fire &amp; flood risk", "Insurance surprises, flagged early.", ""),
        ("cost", "True monthly cost", "Every cost added up, not just the loan.",
         "rent-vs-buy-calculator.html"),
        ("cash", "Cash to the keys", "The real money you need up front.",
         "cash-to-close-calculator.html"),
        ("score", "Plain-English Deal Score", "One 0–100 number. Green = a good deal.", ""),
        ("calc", "Free investor calculators", "Rental &amp; flip math, no signup.",
         "rent-vs-buy-calculator.html"),
        ("credit", "Credit score check", "What your score means for your rate &amp; payment.",
         "learn.html"),
        ("foreclosure", "Foreclosures, nationwide", "Bank-owned deals across the USA.", ""),
        ("agent", "Talk to a local agent", "When you’re ready, reach the listing agent.", ""),
    ]
    cards = ""
    for name, head, sub, href in items:
        inner = (
            f"<div class='fico'>{icon_img(name, head.replace('&amp;', 'and'))}</div>"
            f"<div class='fbody'><h4>{head}</h4><p>{sub}</p></div>"
        )
        if href:
            cards += f"<a class='fcard reveal' href='{href}'>{inner}</a>"
        else:
            cards += f"<div class='fcard reveal'>{inner}</div>"
    return (
        "<section class='sec' id='why-grid'><div class='wrap'>"
        "<div class='sec-head reveal'><div class='kicker'>Everything you get</div>"
        "<h2>One simple app, the whole <em>home-buying picture.</em></h2>"
        "<p>The numbers that decide a home — each in plain English, "
        "each at a glance.</p></div>"
        f"<div class='fgrid'>{cards}</div>"
        "</div></section>"
    )


def _vd_mini(icon_svg: str, label: str, value: str, note: str,
             value_pos: bool = False, chip: str = "") -> str:
    """One mini-card inside a value-dashboard lane. `value_pos` paints the value
    green (a reassuring 'you're clear' read even inside the red warnings lane).

    If `icon_svg` is an illustrated raster icon (vd_img), the icon box drops its
    coloured tint frame so the full-colour art reads true."""
    val_cls = "vd-val vd-pos" if value_pos else "vd-val"
    chip_html = f"<span class='vd-chip'>{chip}</span>" if chip else ""
    ico_cls = "vd-ico vd-illus" if "vd-illus-img" in icon_svg else "vd-ico"
    return (
        "<div class='vd-mini'>"
        f"<span class='{ico_cls}'>{icon_svg}</span>"
        f"<span class='vd-body'><span class='vd-lbl'>{label}</span>"
        f"<span class='{val_cls}'>{value}</span>"
        f"<span class='vd-note'>{note}</span>{chip_html}</span>"
        "</div>"
    )


def value_dashboard_section() -> str:
    """Concept B 'Dashboard Grid' — the whole offering at a glance, in three
    semantic colour lanes (green deal / red warnings / blue money tools) joined
    by gold flow arrows. Sits right under the cinematic hero. CSS is scoped under
    .vdash and shipped via VALUE_DASHBOARD_CSS (extra_head, index.html only).
    Real Underlisted numbers; CTA links point to real existing pages."""
    # gold flow arrow (a simple right-pointing arrow; CSS rotates it down on mobile)
    arrow = ("<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' "
             "stroke-linecap='round' stroke-linejoin='round'><path d='M4 12h15'/>"
             "<path d='M13 6l6 6-6 6'/></svg>")
    # lane icons (kept inline — independent of the site svg() set so colours inherit the lane)
    i_gauge = ("<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' "
               "stroke-linecap='round' stroke-linejoin='round'><path d='M3 12a9 9 0 1 0 18 0 9 9 0 0 0-18 0z'/>"
               "<path d='M12 12l4-3'/><circle cx='12' cy='12' r='1.4' fill='currentColor' stroke='none'/></svg>")
    i_tag = ("<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' "
             "stroke-linecap='round' stroke-linejoin='round'><path d='M20.2 13.1 13.1 20.2a1.9 1.9 0 0 1-2.7 0"
             "l-6.8-6.8a1.9 1.9 0 0 1-.6-1.3V4.6a1.9 1.9 0 0 1 1.9-1.9h7.5a1.9 1.9 0 0 1 1.3.6l6.8 6.8a1.9 1.9 0 0 1 0 2.7z'/>"
             "<circle cx='8' cy='8' r='1.15' fill='currentColor' stroke='none'/></svg>")
    i_home = ("<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' "
              "stroke-linecap='round' stroke-linejoin='round'><path d='M3 11l9-8 9 8'/><path d='M5 10v10h14V10'/>"
              "<path d='M9 20v-6h6v6'/></svg>")
    i_fire = ("<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' "
              "stroke-linecap='round' stroke-linejoin='round'><path d='M12 3c3 3 4.5 5.5 4.5 8.5a4.5 4.5 0 0 1-9 0"
              "c0-1.4.6-2.7 1.5-3.6.2 1.3 1 2.1 2 2.1 0-2 .3-4.4 1-7z'/>"
              "<path d='M3 20.5c2-1.5 4-1.5 6 0s4 1.5 6 0 4-1.5 6 0' opacity='.7'/></svg>")
    i_wave = ("<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' "
              "stroke-linecap='round' stroke-linejoin='round'><path d='M3.5 14.4c1.8-2 3.6-2 5.4 0s3.6 2 5.4 0 3.6-2 5.4 0'/>"
              "<path d='M3.5 9.4c1.8-2 3.6-2 5.4 0s3.6 2 5.4 0 3.6-2 5.4 0'/></svg>")
    i_shield = ("<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' "
                "stroke-linecap='round' stroke-linejoin='round'><path d='M12 3 3 7v5c0 5 3.5 8 9 9 5.5-1 9-4 9-9V7z'/>"
                "<path d='M12 8v4M12 15.5h.01'/></svg>")
    i_card = ("<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' "
              "stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='5' width='18' height='14' rx='2'/>"
              "<path d='M3 10h18'/><path d='M7 15h4'/></svg>")
    i_coin = ("<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' "
              "stroke-linecap='round' stroke-linejoin='round'><path d='M12 1v22'/>"
              "<path d='M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6'/></svg>")
    i_check = ("<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' "
               "stroke-linecap='round' stroke-linejoin='round'><path d='M9 11l3 3 8-8'/>"
               "<path d='M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11'/></svg>")
    i_calc = ("<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' "
              "stroke-linecap='round' stroke-linejoin='round'><rect x='4' y='2' width='16' height='20' rx='2'/>"
              "<path d='M8 6h8'/><path d='M8 11h.01M12 11h.01M16 11h.01M8 15h.01M12 15h.01M16 15v3'/></svg>")

    green_lane = (
        "<div class='vd-lane vd-green'>"
        "<div class='vd-lane-head'><span class='vd-step'>1</span><h3>The deal</h3></div>"
        "<div class='vd-lane-sub'>Is it actually under-priced?</div>"
        + _vd_mini(vd_img("score", "Deal score"), "Plain-English Deal Score", "84 / 100", "Green = a genuinely good buy.")
        + _vd_mini(i_tag, "Below its value", "~9% &middot; $34k", "Worth more than the asking price.")
        + _vd_mini(vd_img("foreclosure", "Foreclosures nationwide"), "Foreclosures, nationwide", "HUD &amp; USDA", "The deepest discounts, same scored feed.")
        + "</div>"
    )
    red_lane = (
        "<div class='vd-lane vd-red'>"
        "<div class='vd-lane-head'><span class='vd-step'>2</span><h3>The warnings</h3></div>"
        "<div class='vd-lane-sub'>What could blindside you?</div>"
        + _vd_mini(vd_img("risk", "Fire and hazard risk"), "Fire &amp; hazard risk", "Moderate", "FEMA data &mdash; watch the insurance bill.")
        + _vd_mini(i_wave, "Flood risk", "Low", "Insurance-friendly &mdash; no surprise zone.", value_pos=True)
        + _vd_mini(i_shield, "Over your budget?", "No &mdash; you're clear", "Turns red the moment a home stretches you.", value_pos=True)
        + "</div>"
    )
    blue_lane = (
        "<div class='vd-lane vd-blue'>"
        "<div class='vd-lane-head'><span class='vd-step'>3</span><h3>The money</h3></div>"
        "<div class='vd-lane-sub'>Can you really carry it?</div>"
        + _vd_mini(vd_img("cost", "Monthly cost"), "True monthly cost", "$2,540/mo", "All-in: mortgage, tax, insurance, HOA, upkeep.")
        + _vd_mini(vd_img("cash", "Cash to close"), "Real cash to the keys", "$48,060", "Down + closing + reserves.")
        + _vd_mini(vd_img("afford", "Can I afford it"), "Can I afford it?", "$610 left/mo", "Income, cash &amp; debts &rarr; green/amber/red.", value_pos=True)
        + _vd_mini(vd_img("credit", "Credit score check"), "Credit &amp; rate check", "720 &rarr; better rate", "See how your score shifts the monthly cost.")
        + _vd_mini(vd_img("calc", "Free investor calculators"), "Free investor calculators", "Rental &amp; flip",
                   "Cap rate, cash-on-cash, 1% &amp; 70% rules.", chip="FREE")
        + "</div>"
    )

    return (
        "<section class='vdash' aria-labelledby='vd-title'>"
        "<div class='vd-wrap'>"
        "<div class='vd-head reveal'>"
        "<span class='vd-kicker'><span class='vd-dot'></span>Everything you get, at a glance</span>"
        "<h2 id='vd-title'>Find the deal. Check the risk. <em>Then decide.</em></h2>"
        "<p>The whole offering in three colored lanes &mdash; the deal in green, the warnings "
        "in red, the money tools in blue. No scrolling, no spreadsheet.</p></div>"
        "<div class='vd-board reveal'>"
        + green_lane
        + f"<div class='vd-flow'>{arrow}<span>then check</span></div>"
        + red_lane
        + f"<div class='vd-flow'>{arrow}<span>then decide</span></div>"
        + blue_lane
        + "</div>"
        "<div class='vd-payoff reveal'><p>Zillow shows you the photo. "
        "<b>Underlisted shows you the whole picture</b> &mdash; the deal, the risk, and the "
        "real money &mdash; before you fall in love.</p></div>"
        "<div class='vd-ctarow reveal'>"
        "<a class='vd-btn vd-btn-fill' href='report-underpriced.html'>See the deals near you &rarr;</a>"
        "<a class='vd-btn vd-btn-line' href='index.html#galaxy-title'>How it works</a>"
        "</div>"
        "</div></section>"
    )


# ──────────────────────────────────────────────────────────────────────────────
# FREE-TOOLS CALCULATORS — the verified calculators (Vera + Forge signed off the
# math in design_preview/*.html) ported into the Ivory & Gold brand shell.
#
# The JS/math is preserved EXACTLY from the preview files. Only the *appearance*
# is reskinned: the calculator chrome below maps the preview's teal/paper look
# onto our Ivory & Gold palette so every tool wears the same brand as the site.
# (Class names from the previews are kept so the ported scripts still target them.)
# ──────────────────────────────────────────────────────────────────────────────
CALC_CSS = f"""
<style>
 /* ===== FREE-TOOLS CALCULATOR — Ivory & Gold reskin of the verified previews ===== */
 .calc{{max-width:600px;margin:0 auto}}
 .calc .tnum{{font-variant-numeric:tabular-nums}}
 .calc .card{{background:var(--surface);border:1px solid var(--hair);border-radius:var(--r);
   box-shadow:var(--shadow-sm);padding:18px 16px;margin-bottom:16px}}
 @media(min-width:600px){{.calc .card{{padding:22px}}}}

 .calc .grid2,.calc .dp-row{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
 .calc .row2{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
 @media(max-width:430px){{.calc .grid2{{grid-template-columns:1fr}}}}
 @media(max-width:380px){{.calc .row2{{grid-template-columns:1fr}}}}
 .calc .dp-row .field{{margin:0}}

 .calc .field{{margin-bottom:14px}}
 .calc .field:last-child{{margin-bottom:0}}
 .calc .field label,.calc .field > label{{display:block;font-family:"Inter";font-size:.82rem;
   font-weight:600;color:var(--ink);margin-bottom:6px}}
 .calc .field .hint{{color:var(--muted);font-weight:400}}

 .calc .inputwrap{{position:relative;display:flex;align-items:center}}
 .calc .inputwrap .pre,.calc .inputwrap .post{{position:absolute;color:var(--muted);
   font-weight:600;font-size:1.05rem;pointer-events:none}}
 .calc .inputwrap .pre{{left:14px}} .calc .inputwrap .post{{right:14px}}
 .calc input[type="text"],.calc input[type="number"]{{width:100%;font-family:"Inter";
   font-variant-numeric:tabular-nums;font-size:1.15rem;font-weight:600;color:var(--ink);
   background:var(--surface-2);border:1.5px solid var(--hair);border-radius:12px;
   padding:13px 14px;min-height:44px;
   transition:border-color .16s,box-shadow .16s,background .16s;-moz-appearance:textfield}}
 .calc input::-webkit-outer-spin-button,.calc input::-webkit-inner-spin-button{{-webkit-appearance:none;margin:0}}
 .calc input.has-pre{{padding-left:30px}} .calc input.has-post{{padding-right:40px}}
 .calc input:focus{{outline:0;background:var(--surface);border-color:var(--gold);
   box-shadow:0 0 0 4px rgba(26,106,72,.14)}}
 .calc input.bad{{border-color:var(--weak);box-shadow:0 0 0 4px rgba(192,57,43,.10)}}

 /* segmented / toggle / chips — gold-tinted */
 .calc .seg,.calc .toggle{{display:grid;gap:4px;background:rgba(26,106,72,.10);
   border:1px solid var(--hair);border-radius:999px;padding:5px}}
 .calc .seg{{grid-template-columns:repeat(4,1fr)}}
 .calc .toggle{{grid-template-columns:1fr 1fr;margin-bottom:18px}}
 .calc .seg button,.calc .toggle button{{border:0;cursor:pointer;font-family:"Inter";font-weight:600;
   background:transparent;color:var(--gold-2);border-radius:999px;
   transition:background .18s,color .18s,box-shadow .18s}}
 .calc .seg button{{padding:9px 4px;font-size:.86rem}}
 .calc .toggle button{{padding:11px 10px;font-size:.92rem}}
 .calc .seg button.on,.calc .toggle button.on{{background:var(--surface);color:var(--ink);
   box-shadow:0 1px 2px rgba(60,44,20,.08),0 8px 18px -10px rgba(60,44,20,.30)}}
 .calc .miniseg{{display:inline-flex;gap:2px;margin-left:8px;background:rgba(26,106,72,.10);
   border:1px solid var(--hair);border-radius:999px;padding:2px;vertical-align:middle}}
 .calc .miniseg button{{border:0;cursor:pointer;font-family:"Inter";font-size:.72rem;font-weight:600;
   color:var(--gold-2);padding:2px 9px;border-radius:999px;background:transparent;
   transition:background .15s,color .15s}}
 .calc .miniseg button.on{{background:var(--surface);color:var(--ink);box-shadow:0 1px 2px rgba(60,44,20,.12)}}
 .calc .chips{{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}}
 .calc .chip{{border:1.5px solid var(--hair);background:var(--surface-2);cursor:pointer;
   font-family:"Inter";font-size:.82rem;font-weight:600;color:var(--gold-2);
   padding:7px 13px;border-radius:999px;transition:background .16s,border-color .16s,color .16s}}
 .calc .chip small{{color:var(--muted);font-weight:500}}
 .calc .chip:hover{{border-color:rgba(26,106,72,.6)}}
 .calc .chip.on{{background:var(--gold);border-color:var(--gold);color:#FFFBF1}}
 .calc .chip.on small{{color:rgba(255,251,241,.85)}}

 .calc select{{width:100%;font-family:"Inter";font-size:1rem;font-weight:600;color:var(--ink);
   background:var(--surface-2);border:1.5px solid var(--hair);border-radius:12px;
   padding:12px 14px;min-height:44px;cursor:pointer;appearance:none;
   background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%236B635A' stroke-width='1.6' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");
   background-repeat:no-repeat;background-position:right 14px center}}
 .calc select:focus{{outline:0;border-color:var(--gold);box-shadow:0 0 0 4px rgba(26,106,72,.14)}}

 /* advanced disclosure */
 .calc details.adv{{background:var(--surface-2);border:1px solid var(--hair);border-radius:var(--r);
   margin-bottom:16px;overflow:hidden}}
 .calc details.adv > summary{{list-style:none;cursor:pointer;padding:15px 16px;font-family:"Inter";
   font-weight:600;font-size:.92rem;color:var(--ink);display:flex;align-items:center;gap:8px;user-select:none}}
 .calc details.adv > summary::-webkit-details-marker{{display:none}}
 .calc details.adv > summary .chev{{margin-left:auto;transition:transform .2s;color:var(--muted)}}
 .calc details.adv[open] > summary .chev{{transform:rotate(180deg)}}
 .calc details.adv > summary small{{color:var(--muted);font-weight:400}}
 .calc .adv-body{{padding:0 16px 16px}}
 .calc .adv-note{{font-family:"Inter";color:var(--muted);font-size:.8rem;margin:-2px 0 14px}}

 /* ===== the big answer hero — dark INK plate with a gold halo (Ivory & Gold) ===== */
 .calc .answer{{position:relative;background:radial-gradient(120% 95% at 50% 0%, #2A2118 0%, #17120C 74%);
   color:#F4ECDD;border-radius:24px;padding:28px 22px 24px;text-align:center;
   box-shadow:var(--shadow);overflow:hidden;margin-bottom:16px;border:1px solid rgba(26,106,72,.30)}}
 .calc .answer::after{{content:"";position:absolute;inset:0;pointer-events:none;
   background:radial-gradient(70% 55% at 50% 4%, rgba(217,169,63,.28), transparent 70%)}}
 .calc .answer .eyebrow{{position:relative;z-index:1;font-family:"Inter";text-transform:uppercase;
   letter-spacing:.16em;font-size:.68rem;font-weight:600;color:var(--gold-bright);margin-bottom:10px}}
 .calc .answer .lede-top{{position:relative;z-index:1;color:rgba(244,236,221,.85);font-size:1rem;margin-bottom:4px}}
 .calc .answer .big{{position:relative;z-index:1;font-family:"Cormorant Garamond",serif;font-weight:600;
   font-size:clamp(2.3rem,11vw,3.3rem);line-height:1.04;letter-spacing:.005em;color:#FFFDF8}}
 .calc .answer .big .unit{{font-size:.5em;font-weight:500;color:var(--gold-bright);font-family:"Inter"}}
 .calc .answer .big b{{color:#5FCF93;font-weight:600}}
 .calc .answer .lede{{position:relative;z-index:1;font-family:"Inter";margin-top:10px;
   color:rgba(244,236,221,.86);font-size:.97rem}}
 .calc .answer .lede b{{color:#FFFDF8;font-weight:600}}
 /* warm-warning hero (debts/payment-too-low/renting-wins) */
 .calc .answer.warn{{background:radial-gradient(120% 95% at 50% 0%, #5A3417 0%, #38200E 74%);border-color:rgba(217,169,63,.34)}}
 .calc .answer.warn::after{{background:radial-gradient(70% 55% at 50% 4%, rgba(217,169,63,.30), transparent 70%)}}
 .calc .answer.warn .eyebrow{{color:#F0CE9A}}
 .calc .answer.warn .big{{font-size:clamp(1.35rem,6vw,1.8rem);line-height:1.22}}
 .calc .answer.warn .big b{{color:#FFD08A}}

 /* secondary stat strip */
 .calc .stats{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px}}
 .calc .stat{{background:var(--surface);border:1px solid var(--hair);border-radius:12px;
   padding:14px;box-shadow:var(--shadow-sm)}}
 .calc .stat .k{{font-family:"Inter";font-size:.76rem;color:var(--muted);font-weight:600;margin-bottom:4px}}
 .calc .stat .v{{font-family:"Cormorant Garamond",serif;font-weight:600;font-size:1.4rem;color:var(--ink)}}
 .calc .stat .v .per{{font-size:.6em;font-weight:500;color:var(--muted);font-family:"Inter"}}
 .calc .stat.muted-stat{{background:var(--surface-2)}}

 /* bars / timeline */
 .calc .timeline{{margin-bottom:16px}}
 .calc .barlabels{{display:flex;justify-content:space-between;align-items:baseline;
   font-family:"Inter";font-size:.74rem;color:var(--muted);margin-bottom:8px}}
 .calc .barlabels h3{{font-family:"Cormorant Garamond",serif;font-weight:600;font-size:1.05rem;color:var(--ink)}}
 .calc .bar{{height:16px;border-radius:999px;overflow:hidden;background:var(--okay-soft);display:flex}}
 .calc .bar .principal,.calc .bar .used{{background:var(--good);height:100%;transition:width .5s cubic-bezier(.4,0,.2,1)}}
 .calc .bar .interest{{background:var(--okay);height:100%;transition:width .5s cubic-bezier(.4,0,.2,1)}}
 .calc .bar .used.amber{{background:var(--okay)}} .calc .bar .used.red{{background:var(--weak)}}
 .calc .legend{{display:flex;gap:16px;margin-top:10px;font-family:"Inter";font-size:.8rem;color:var(--muted);flex-wrap:wrap}}
 .calc .legend span{{display:inline-flex;align-items:center;gap:6px}}
 .calc .legend .dot{{width:10px;height:10px;border-radius:3px;display:inline-block}}
 .calc .dot.g,.calc .dot.buy{{background:var(--good)}} .calc .dot.a{{background:var(--okay)}}
 .calc .dot.rent{{background:var(--weak)}} .calc .dot.be{{background:var(--ink)}}
 .calc .chart svg{{display:block;width:100%;height:auto}}

 /* cash cards (cash-to-close) */
 .calc .cash-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
 .calc .cash{{background:var(--surface-2);border:1px solid var(--hair);border-radius:12px;padding:16px}}
 .calc .cash .lbl{{font-family:"Inter";font-size:.8rem;color:var(--muted)}}
 .calc .cash .val{{font-family:"Cormorant Garamond",serif;font-weight:600;font-size:1.5rem;margin-top:5px;color:var(--ink)}}
 .calc .cash .note{{font-family:"Inter";font-size:.73rem;color:var(--muted);margin-top:2px}}
 .calc .cash-total{{margin-top:12px;display:flex;justify-content:space-between;align-items:center;
   padding:14px 16px;background:rgba(26,106,72,.12);border:1px solid var(--hair);border-radius:12px;
   font-family:"Inter";color:var(--gold-deep);font-weight:700}}
 .calc .cash-total .v{{font-family:"Cormorant Garamond",serif;font-size:1.35rem}}
 .calc .reserves{{margin-top:12px;display:flex;gap:11px;align-items:flex-start;padding:13px 14px;
   background:var(--good-soft);border:1px solid rgba(26,143,90,.22);border-radius:12px}}
 .calc .reserves .ic{{font-size:1.1rem;line-height:1.2}}
 .calc .reserves .rt b{{display:block;font-family:"Inter";font-size:.9rem;font-weight:700;color:var(--good)}}
 .calc .reserves .rt span{{font-family:"Inter";font-size:.8rem;color:var(--muted);line-height:1.45}}
 .calc .reserves .rt b .amt{{font-family:"Cormorant Garamond",serif}}
 .calc .card h3{{font-family:"Cormorant Garamond",serif;font-weight:600;font-size:1.15rem;
   display:flex;align-items:center;gap:9px;margin:0 0 3px;color:var(--ink)}}
 .calc .card .sub{{font-family:"Inter";color:var(--muted);font-size:.84rem;margin-bottom:15px}}
 .calc .ico{{width:22px;height:22px;flex:none;color:var(--gold-2)}}

 /* break-even callout (rent vs buy) */
 .calc .breakeven{{display:flex;align-items:center;gap:12px;background:var(--good-soft);
   border:1px solid rgba(26,143,90,.22);border-radius:var(--r);padding:14px 16px;margin-bottom:16px;
   font-family:"Inter";font-size:.98rem;color:var(--ink)}}
 .calc .breakeven .ico{{flex:0 0 auto;width:34px;height:34px;border-radius:10px;background:var(--good);
   color:#fff;display:grid;place-items:center;font-family:"Cormorant Garamond",serif;font-weight:600;font-size:1.1rem}}
 .calc .breakeven b{{color:var(--good)}}
 .calc .breakeven.amber{{background:var(--okay-soft);border-color:rgba(181,120,10,.28)}}
 .calc .breakeven.amber .ico{{background:var(--okay)}} .calc .breakeven.amber b{{color:var(--okay)}}
 .calc .breakeven.red{{background:var(--weak-soft);border-color:rgba(192,57,43,.28)}}
 .calc .breakeven.red .ico{{background:var(--weak)}} .calc .breakeven.red b{{color:var(--weak)}}

 /* the "magic" reward line */
 .calc .magic,.calc .extra{{background:var(--good-soft);border:1px solid rgba(26,143,90,.22);
   border-radius:var(--r);padding:16px;margin-bottom:16px}}
 .calc .magic{{display:flex;align-items:center;gap:10px}}
 .calc .magic.col{{display:block}}
 .calc .magic .toprow,.calc .extra .toprow{{display:flex;align-items:center;gap:8px;margin-bottom:4px}}
 .calc .magic .spark,.calc .extra .spark{{font-size:1.05rem}}
 .calc .magic h3,.calc .extra h3{{font-family:"Cormorant Garamond",serif;font-weight:600;font-size:1.05rem;color:var(--ink)}}
 .calc .extra .sub{{font-family:"Inter";color:var(--muted);font-size:.85rem;margin-bottom:12px}}
 .calc .magic p,.calc .magicline,.calc .saveline{{font-family:"Inter";font-size:.98rem;color:var(--ink)}}
 .calc .magic p b,.calc .magicline b,.calc .saveline b{{color:var(--good)}}
 .calc .magic.idle,.calc .magicline.idle,.calc .saveline.idle{{color:var(--muted)}}
 .calc .magic.idle{{background:var(--surface-2);border-color:var(--hair)}}
 .calc .magic.idle p{{color:var(--muted)}}
 .calc .magic p b.less{{color:var(--good)}} .calc .magic p b.more{{color:var(--weak)}}
 .calc .magic .tag{{font-family:"Inter";color:var(--muted);font-size:.78rem;margin-top:8px}}
 @keyframes calcpop{{0%{{transform:scale(1);box-shadow:0 0 0 0 rgba(26,143,90,.40)}}
   40%{{transform:scale(1.012);box-shadow:0 0 0 8px rgba(26,143,90,0)}}
   100%{{transform:scale(1);box-shadow:0 0 0 0 rgba(26,143,90,0)}}}}
 .calc .pop{{animation:calcpop .55s ease}}

 .calc .disclaimer{{text-align:center;font-family:"Inter";color:var(--faint);font-size:.78rem;
   margin-top:18px;line-height:1.5}}

 /* the calculator page hero (H1 + SEO intro) */
 .calc-intro{{text-align:center;max-width:640px;margin:50px auto 26px}}
 .calc-intro .kicker{{margin-bottom:14px;display:inline-flex;align-items:center;justify-content:center;gap:4px;flex-wrap:wrap}}
 .calc-intro .kicker .freebadge{{text-transform:uppercase;letter-spacing:.16em}}
 .calc-intro h1{{font-weight:500;font-size:clamp(2.1rem,5vw,3.2rem);line-height:1.07;letter-spacing:.005em;margin:0}}
 .calc-intro h1 em{{color:var(--gold)}}
 .calc-intro p{{font-family:"Inter";color:var(--muted);font-size:1.04rem;margin:16px auto 0;max-width:54ch;line-height:1.6}}

 /* free-tools hub cards */
 .hub-grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px;max-width:900px;margin:0 auto}}
 @media(max-width:640px){{.hub-grid{{grid-template-columns:1fr}}}}
 .hub-card{{position:relative;display:flex;flex-direction:column;background:var(--surface);border:1px solid var(--hair);
   border-radius:var(--r-lg);padding:28px 26px;box-shadow:var(--shadow-sm);text-decoration:none;
   color:var(--ink);transition:transform .2s,border-color .2s}}
 .hub-card:hover{{transform:translateY(-3px);border-color:rgba(26,106,72,.55)}}
 .hub-card .hub-badge{{position:absolute;top:22px;right:22px}}
 .hub-card .ico{{width:52px;height:52px;border-radius:15px;display:grid;place-items:center;margin-bottom:18px;
   background:linear-gradient(155deg,rgba(26,106,72,.18),rgba(26,106,72,.05));border:1px solid var(--hair)}}
 .hub-card .ico svg{{width:26px;height:26px;color:var(--gold-2)}}
 .hub-card h3{{font-weight:600;font-size:1.5rem;line-height:1.12;margin:0 0 6px;color:var(--ink)}}
 .hub-card p{{font-family:"Inter";color:var(--muted);font-size:.95rem;line-height:1.55;margin:0}}
 .hub-card .go{{font-family:"Inter";margin-top:18px;display:inline-flex;align-items:center;gap:8px;
   font-weight:600;font-size:.92rem;color:var(--gold-2)}}
 .hub-card .go svg{{width:16px;height:16px}}
</style>"""


# ──────────────────────────────────────────────────────────────────────────────
# DEEP-DIVE "See how it works" pages — one per galaxy feature. Quill wrote the
# honest copy (content/FEATURE_DEEPDIVES.html); this CSS dresses it in Ivory &
# Gold so each page reads as native site furniture, not a bolted-on explainer.
# Structure of every page: editorial hero (kicker + H1 + lede) → "What it is" →
# "How we work it out" (the engineering, shown simply: formula-in-words, named
# data sources, an honest worked example) → "Why you can trust it" → caveat →
# cross-links. No waitlist form, no Payhip button. Pure static HTML.
# ──────────────────────────────────────────────────────────────────────────────
DEEPDIVE_CSS = f"""
<style>
 .dd{{max-width:760px;margin:0 auto}}
 /* breadcrumb / back nav — matches the .pagelinks idiom used elsewhere */
 .dd-back{{font-family:"Inter";font-size:.9rem;margin:26px auto 0;max-width:760px}}
 .dd-back a{{color:var(--gold-2);text-decoration:none;font-weight:600}}
 .dd-back a:hover{{text-decoration:underline}}
 .dd-back .sep{{color:var(--faint);margin:0 8px}}

 /* hero */
 .dd-hero{{text-align:center;max-width:680px;margin:30px auto 6px}}
 .dd-hero .kicker{{display:inline-flex;align-items:center;gap:10px;font-family:"Inter";
   font-size:.72rem;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:var(--gold-2);
   border:1px solid var(--hair);border-radius:999px;padding:7px 16px;margin-bottom:20px;background:var(--surface)}}
 .dd-hero .kicker .dot{{width:6px;height:6px;border-radius:50%;background:var(--good);box-shadow:0 0 10px rgba(26,143,90,.8)}}
 .dd-hero h1{{font-weight:500;font-size:clamp(2.2rem,5vw,3.4rem);line-height:1.06;letter-spacing:.005em;margin:0 auto;max-width:18ch}}
 .dd-hero h1 em{{color:var(--gold);font-weight:600}}
 .dd-hero .lede{{font-family:"Inter";color:var(--muted);font-size:1.08rem;margin:18px auto 0;max-width:54ch;line-height:1.62}}
 .dd-hero .lede b{{color:var(--ink);font-weight:600}}

 /* section blocks */
 .dd-block{{max-width:760px;margin:0 auto;padding:30px 0;border-top:1px solid var(--hair-soft)}}
 .dd-block:first-of-type{{border-top:0}}
 .dd-eyebrow{{font-family:"Inter";font-size:.72rem;font-weight:600;letter-spacing:.2em;
   text-transform:uppercase;color:var(--gold-2);margin-bottom:12px;display:flex;align-items:center;gap:10px}}
 .dd-eyebrow .n{{font-family:"Cormorant Garamond",serif;font-style:italic;font-weight:600;
   font-size:1.4rem;color:var(--gold);letter-spacing:0}}
 .dd-block h2{{font-weight:600;font-size:clamp(1.6rem,3.4vw,2.1rem);line-height:1.14;margin:0 0 4px;color:var(--ink)}}
 .dd-block p{{font-family:"Inter";color:var(--ink-soft);font-size:1.04rem;line-height:1.66;margin:.7rem 0}}
 .dd-block p b{{color:var(--ink);font-weight:600}}
 .dd-block p em{{color:var(--gold-2);font-style:italic}}

 /* worked example — dashed gold card */
 .dd-eg{{font-family:"Inter";background:var(--surface-2);border:1px dashed rgba(26,106,72,.55);
   border-radius:14px;padding:16px 18px;margin:16px 0;color:var(--ink-soft);font-size:1rem;line-height:1.6}}
 .dd-eg .tag{{display:block;font-family:"Inter";font-size:.7rem;font-weight:700;letter-spacing:.14em;
   text-transform:uppercase;color:var(--gold-2);margin-bottom:6px}}
 .dd-eg b{{color:var(--ink);font-weight:600}}

 /* score key chips */
 .dd-scorekey{{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 4px}}
 .dd-scorekey span{{font-family:"Inter";display:inline-flex;align-items:center;gap:7px;border-radius:999px;
   padding:6px 14px;font-weight:600;font-size:.85rem;color:#fff}}

 /* named data sources */
 .dd-sources{{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0 2px}}
 .dd-sources .chip{{font-family:"Inter";display:inline-flex;align-items:center;gap:7px;
   background:var(--surface);border:1px solid var(--hair);border-radius:999px;padding:6px 13px;
   font-size:.83rem;font-weight:600;color:var(--gold-deep)}}
 .dd-sources .chip svg{{width:14px;height:14px;color:var(--gold);opacity:.9}}

 /* trust close — calm green panel */
 .dd-trust{{background:var(--good-soft);border:1px solid rgba(26,143,90,.26);border-radius:16px;
   padding:20px 22px;margin:6px auto 0;max-width:760px}}
 .dd-trust .dd-eyebrow{{color:var(--good)}}
 .dd-trust h2{{font-weight:600;font-size:1.5rem;margin:0 0 4px;color:var(--ink)}}
 .dd-trust p{{font-family:"Inter";color:var(--ink-soft);font-size:1.02rem;line-height:1.62;margin:.5rem 0}}
 .dd-trust p b{{color:var(--good)}}

 /* honest caveat — soft amber */
 .dd-caveat{{font-family:"Inter";display:flex;align-items:flex-start;gap:11px;max-width:760px;
   margin:18px auto 0;background:var(--okay-soft);border:1px solid rgba(181,120,10,.3);border-radius:13px;
   padding:14px 17px;color:var(--ink-soft);font-size:.96rem;line-height:1.58}}
 .dd-caveat .ic{{color:var(--okay);font-size:1.15rem;line-height:1.4;flex:none}}
 .dd-caveat b{{color:var(--okay)}}

 /* cross-links footer strip */
 .dd-more{{max-width:760px;margin:30px auto 0;padding-top:24px;border-top:1px solid var(--hair-soft);
   font-family:"Inter";font-size:.96rem;color:var(--muted);text-align:center}}
 .dd-more a{{color:var(--gold-2);text-decoration:none;font-weight:600}}
 .dd-more a:hover{{text-decoration:underline}}
 .dd-more .sep{{color:var(--faint);margin:0 7px}}
</style>"""


def calc_shell(title: str, desc: str, *, h1: str, intro: str, body: str,
               here: str = "") -> str:
    """A calculator page: brand hero (H1 + SEO intro) → the calculator →
    the SAME waitlist coupon used site-wide. CALC_CSS is injected in <head>."""
    page = (
        "<section class='masthead' style='padding:0'><div class='wrap'>"
        "<div class='calc-intro reveal in'>"
        f"<div class='kicker'>{free_badge(big=True)} &nbsp;Plain English · no signup</div>"
        f"<h1>{h1}</h1>"
        f"<p>{intro}</p>"
        "</div></div></section>"
        "<section class='sec' style='padding-top:18px'><div class='wrap'>"
        f"<div class='calc'>{body}</div>"
        "</div></section>"
        + WAITLIST
    )
    return shell(title, desc, page, here=here, extra_head=CALC_CSS)


def shell(title: str, desc: str, body: str, *, here: str = "",
          robots: str = "", extra_head: str = "", show_header: bool = True) -> str:
    """Wrap page body in the shared brand shell (head + header + footer + JS).

    `show_header=False` suppresses the sticky Ivory site-header — used only by the
    homepage, whose full-screen cinematic hero carries its own top bar (so the page
    opens cleanly on the hero with no doubled navigation). Every other page keeps
    the shared sticky header."""
    robots_tag = f"<meta name='robots' content='{robots}'>" if robots else ""
    head_bar = header_html(here) if show_header else ""
    return (
        "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{title}</title><meta name='description' content='{desc}'>"
        f"{robots_tag}{FONTS}{CSS}{extra_head}</head><body>"
        f"{head_bar}{body}{footer_html()}{REVEAL_JS}"
        "</body></html>"
    )


REVEAL_JS = """
<script>
 (function(){
   var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
   window.addEventListener("load", function(){
     var arc = document.getElementById("arcF");
     if(arc){ var pct = parseFloat(arc.getAttribute("data-pct")||"0.84");
       if(reduce){arc.style.transition="none";}
       requestAnimationFrame(function(){ arc.style.strokeDashoffset = (251.2*(1-pct)).toFixed(1); }); }
   });
   if(reduce){ document.querySelectorAll(".reveal").forEach(function(e){e.classList.add("in")}); return; }
   var io = new IntersectionObserver(function(es){
     es.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add("in"); io.unobserve(e.target);} });
   },{threshold:.14});
   document.querySelectorAll(".reveal:not(.in)").forEach(function(e){io.observe(e)});
 })();
</script>"""


# ──────────────────────────────────────────────────────────────────────────────
# "HOW IT WORKS" — UNFOLD-THE-STORY toggle wiring (index.html only).
# Vanilla JS, no framework/build. Wires three controls to ONE collapsible
# (#howitworks): the hero ghost button, the header nav link, and the in-block
# "▲ Hide" button. Each is a real, keyboard-operable control with correct
# aria-expanded state. The early-collapse guard (inline, mid-body) already set
# the default collapsed state pre-paint; this just handles clicks + scroll.
# ──────────────────────────────────────────────────────────────────────────────
HIW_JS = """
<script>
(function(){
  var panel = document.getElementById('howitworks');
  if(!panel) return;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var toggles = Array.prototype.slice.call(document.querySelectorAll('[data-hiw-toggle]'));
  var hides   = Array.prototype.slice.call(document.querySelectorAll('[data-hiw-hide]'));

  function isOpen(){ return panel.classList.contains('hiw--open'); }

  // keep every toggle's aria-expanded in sync. The hero gold button's label is now
  // CONSTANT ("Learn how it works →") — it no longer flips to "Hide" when open
  // (owner 2026-06-21: "Why call it 'Hide'?"). The bottom "▲ Hide how it works"
  // control inside the unfolded story is still the way to collapse it.
  function syncState(){
    var open = isOpen();
    toggles.forEach(function(t){ t.setAttribute('aria-expanded', open ? 'true':'false'); });
    // the "New to buying a house?" eyebrow only shows while the story is closed
    var eyebrow = document.querySelector('[data-hiw-eyebrow]');
    if(eyebrow){ eyebrow.classList.toggle('is-open', open); }
  }

  function smoothTo(el){
    if(!el) return;
    el.scrollIntoView({behavior: reduce ? 'auto' : 'smooth', block:'start'});
  }

  // The story sections use the site's scroll-triggered fade-in (.reveal -> .reveal.in
  // added by the IntersectionObserver). When the block unfolds, the sections now on
  // screen would read faint until the user scrolls. So the instant we open, we mark
  // any .reveal inside #howitworks that's already in (or near) the viewport as visible
  // by adding the SAME ".in" class the observer uses. Elements further down keep their
  // un-revealed state and still animate normally on scroll.
  function revealVisibleInside(){
    var vh = window.innerHeight || document.documentElement.clientHeight;
    var margin = vh * 0.25; // also pre-reveal a little below the fold so nothing pops faint
    var els = panel.querySelectorAll('.reveal:not(.in)');
    Array.prototype.forEach.call(els, function(e){
      var r = e.getBoundingClientRect();
      if(r.top < vh + margin && r.bottom > -margin){ e.classList.add('in'); }
    });
  }

  function open(){
    panel.classList.add('hiw--open');
    syncState();
    // crisp-up the now-visible story sections immediately (no faint flash),
    // then scroll to the top of the unfolded story after the row begins to expand.
    requestAnimationFrame(function(){
      revealVisibleInside();
      smoothTo(panel);
      // after the smooth scroll settles, catch anything newly brought into view
      requestAnimationFrame(revealVisibleInside);
    });
  }
  function close(scrollUp){
    panel.classList.remove('hiw--open');
    syncState();
    if(scrollUp){
      // collapse, then ease back up to the cinematic cover
      var cover = document.querySelector('.ch-hero') || document.body;
      requestAnimationFrame(function(){
        window.scrollTo({top:0, behavior: reduce ? 'auto':'smooth'});
        if(cover && cover.scrollIntoView){ /* top is the cover */ }
      });
    }
  }

  toggles.forEach(function(t){
    t.addEventListener('click', function(ev){
      ev.preventDefault();
      if(isOpen()){ close(true); } else { open(); }
    });
  });
  hides.forEach(function(h){
    h.addEventListener('click', function(ev){
      ev.preventDefault();
      close(true);
    });
  });

  syncState();
})();
</script>"""


def _score_meaning(s: int) -> str:
    return "good" if s >= 70 else ("okay" if s >= 45 else "weak")


def _score_color(s: int) -> str:
    return GOOD if s >= 70 else (OKAY if s >= 45 else WEAK)


# ──────────────────────────────────────────────────────────────────────────────
# "Why our deals are the best" — owner-approved headline (RED used tastefully on
# the key words only), a plain HOW explainer, the live deal-count stat, and the
# "see deals near you" ZIP box that hands off to the live app.
#
# Honesty guardrail (Portia to bless final words): NO unprovable superlatives like
# "lowest price anywhere" / "nowhere cheaper". We describe what we actually do —
# pull government foreclosure/bank-owned feeds + under-priced listings, and score
# every one 0–100 with risk + true monthly cost.
# ──────────────────────────────────────────────────────────────────────────────
def best_deals_section() -> str:
    """RIGHT tile of Row 1 in the "see what you get" map: "Here's how we find
    them" — keeps the live count + ZIP search box, copy tightened to one
    scannable line. No full-bleed wrapper/rules: it's plain tile content now
    (the map's .maptile is the frame). Brand meaning-colours mark the scan."""
    count = live_deal_count()
    return (
        "<div class='find reveal'>"
        "<div class='maptile-head'>"
        "<div class='kicker'>Why our deals are the best</div>"
        "<h2>Here's how we <em>find</em> them.</h2></div>"
        # ONE scannable line (every fact kept; padding cut). Meaning-colours:
        # green = the deal we surface · red = the risk we flag · blue = money tools.
        "<p class='how'>We pull "
        "<span class='src'>government foreclosure &amp; bank-owned feeds (HUD &amp; USDA)</span> "
        "plus <b>under-priced listings nationwide</b>, then score every one "
        "<b>0–100 in plain English</b> — with "
        "<span class='mk-red'>fire &amp; flood risk</span> and the "
        "<span class='mk-blue'>true monthly cost</span> built in.</p>"
        # .find-foot: the count + ZIP box + disclaimer are grouped so they can be
        # pushed to the BOTTOM of the (stretched) tile — the head stays at the top
        # and aligns with the dark constellation tile's head; no floating dead band.
        "<div class='find-foot'>"
        # live count stat
        "<div class='countstat'>"
        f"<div class='num tnum'>{count_label(count)}</div>"
        "<div class='cap'>homes scored &amp; tracked nationwide</div>"
        "</div>"
        # ZIP / city box → routes to the live app
        "<div class='ziphunt'>"
        "<p class='prompt'>Type your ZIP — see the under-priced homes near you.</p>"
        f"<form class='zipform' action='{APP_BROWSE_URL}' method='get' target='_blank' rel='noopener'>"
        "<span class='zipwrap'>"
        f"{svg('home', w=18)}"
        "<input type='text' name='area' inputmode='text' autocomplete='postal-code' "
        "placeholder='ZIP or city — e.g. 30303 or Atlanta' aria-label='Your ZIP code or city' />"
        "</span>"
        f"<button type='submit'>See deals near you {svg('arrow', w=18)}</button>"
        "</form></div>"
        # Portia-required disclaimer (screening tool, not advice/guarantee).
        "<p class='best-disclaim' style='font-size:.72rem;line-height:1.5;color:#938A7E'>"
        "Deal Scores and cost estimates are automated screening tools — not appraisals or "
        "financial advice. Verify with a licensed lender, agent and inspector before buying.</p>"
        "</div>"  # /.find-foot
        "</div>"
    )


# ──────────────────────────────────────────────────────────────────────────────
# LOCKED TEASER — "here's a taste of the paid magic, behind glass." A freemium
# unlock hook: 1–2 clearly-labelled SAMPLE result cards. The FREE/basic parts are
# visible (address, beds/baths, a teaser line); the VALUABLE paid answers — the
# Deal Score, the "$X below value", the true monthly cost, the afford verdict —
# are BLURRED behind a frosted-glass overlay with a lock + an "Unlock" CTA.
#
# HONESTY: every card is plainly marked "SAMPLE" and uses made-up numbers, never a
# real listing. The Unlock button only LINKS to the existing signup section
# (#early-access → the waitlist now, the Payhip subscribe when live). No selling/
# pricing/checkout logic lives or changes here — it is a routed anchor link.
# ──────────────────────────────────────────────────────────────────────────────
def _teaser_card(addr: str, meta: str, teaser: str,
                 score: int, verdict: str, below: str, cost: str, afford: str,
                 afford_cls: str) -> str:
    sc_cls = _score_meaning(score)
    return (
        "<div class='tcard reveal'>"
        "<span class='sample-tag'>Sample home</span>"
        # ── visible / FREE top ──
        "<div class='open'>"
        f"<div class='addr'>{addr}</div>"
        f"<div class='meta'>{meta}</div>"
        f"<div class='teaserline'>{svg('home', w=15)}{teaser}</div>"
        "</div>"
        # ── locked / PAID rows behind glass ──
        "<div class='tlocked'>"
        "<div class='blurfield' aria-hidden='true'>"
        f"<div class='lrow'><span class='lk'>{svg('gauge', w=16)}Deal Score</span>"
        f"<span class='lv {sc_cls} tnum'>{score} · {verdict}</span></div>"
        f"<div class='lrow'><span class='lk'>{svg('tag', w=16)}Below its value</span>"
        f"<span class='lv good tnum'>{below}</span></div>"
        f"<div class='lrow'><span class='lk'>{svg('bank', w=16)}True cost / month</span>"
        f"<span class='lv tnum'>{cost}</span></div>"
        f"<div class='lrow'><span class='lk'>{svg('coin', w=16)}Can you afford it?</span>"
        f"<span class='lv {afford_cls}'>{afford}</span></div>"
        "</div>"
        # the frosted glass + lock + unlock CTA (routes to the existing signup)
        "<div class='glass'>"
        f"<span class='lockwrap'>{svg('lock', w=24)}</span>"
        "<span class='gline'>Subscribe to see every home's Deal Score, true cost &amp; risk.</span>"
        f"<a class='unlock' href='index.html#early-access'>{svg('lock', w=16)}"
        "Unlock — founding $19.99/mo</a>"
        "<span class='gfine'>Cancel anytime · founding price locked for a year</span>"
        "</div>"
        "</div></div>"
    )


def locked_teaser_section() -> str:
    cards = (
        _teaser_card(
            "1428 Magnolia Ave", "Sacramento, CA · 3 bed · 2 bath · 41 days listed",
            "Listed at $389,000 — but is it a deal?",
            84, "GREAT", "$34,000", "$2,760/mo", "Yes — $610 left/mo", "good")
        + _teaser_card(
            "76 Birchwood Ln", "Cleveland, OH · 4 bed · 2 bath · 18 days listed",
            "Listed at $214,500 — but is it a deal?",
            71, "STRONG", "$19,800", "$1,640/mo", "Yes — $430 left/mo", "good")
    )
    return (
        # No full-bleed wrapper/rules here: the map's full-width row frames it.
        "<div class='teaser-wrap'>"
        "<section class='sec' id='peek'><div class='wrap'>"
        "<div class='sec-head reveal'><div class='kicker'>What you'll find when you search</div>"
        "<h2>The free part is the address. The <em>magic</em> is behind the glass.</h2>"
        "<p>The parts that actually answer “is this a good deal?” unlock the moment you subscribe.</p></div>"
        f"<div class='teaser-grid'>{cards}</div>"
        "<p class='teaser-foot'>Every example is a <b>sample</b> with made-up numbers. "
        "Inside Underlisted, every real U.S. home gets the same plain-English read — "
        "<a href='index.html#early-access'>get founding access →</a></p>"
        "</div></section></div>"
    )


# ──────────────────────────────────────────────────────────────────────────────
# THE HOMEPAGE — the full Ivory & Gold brand page (the blueprint, made dynamic).
# ──────────────────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────
# THE FEATURE GALAXY — interactive constellation of everything you get.
# Lifted from design_preview/feature_orbit.html (owner-approved 2026-06-18):
# auto-rotating orbit, tap-to-expand cards, related-node glow, reduced-motion
# support, and a premium stacked-card fallback on mobile. Re-themed to Ivory &
# Gold and given a "See how it works →" link on every card.
#
# NOTE (Quill): the "See how it works" links currently point to the most relevant
# EXISTING page/anchor so nothing is broken. Repoint each `href` to its dedicated
# per-feature deep-dive page once Quill's content ships.
# ──────────────────────────────────────────────────────────────────────────────
def feature_galaxy_section() -> str:
    return """
<section class="galaxy" aria-labelledby="galaxy-title">
  <div class="galaxy-inner">
    <div class="g-head reveal">
      <span class="g-tag"><span class="dot"></span>Everything you get</span>
      <h2 id="galaxy-title">One app. Every answer a <em>home buyer</em> needs.</h2>
      <p>No more clicking around or doing the math in spreadsheets. Tap any point in the
         constellation to see what it does for you.</p>
      <p class="g-hint">The ring turns on its own — tap a node to pause and explore.</p>
    </div>

    <!-- ORBIT (desktop/tablet) -->
    <div class="stage" id="g-stage" aria-hidden="false">
      <div class="ring r1"></div>
      <div class="ring r2"></div>
      <div class="orbit-field" id="g-field"><!-- nodes injected by JS --></div>
      <button class="hub" id="g-hub" aria-label="Underlisted Deal Score — collapse any open feature">
        <span class="glow"></span>
        <span class="disc">
          <svg class="ring-svg" viewBox="0 0 130 130" width="130" height="130" aria-hidden="true">
            <path d="M20 95 A52 52 0 1 1 110 95" fill="none" stroke="rgba(26,143,90,.16)" stroke-width="9" stroke-linecap="round"/>
            <path d="M20 95 A52 52 0 0 1 105 50" fill="none" stroke="#1FA968" stroke-width="9" stroke-linecap="round"/>
          </svg>
          <span class="num">84</span>
          <span class="lbl">Deal Score</span>
        </span>
      </button>
      <div class="gdetail" id="g-detail" role="dialog" aria-modal="false" aria-live="polite"></div>
    </div>

    <!-- MOBILE FALLBACK: stacked cards (same features) -->
    <div class="glist" id="g-list" aria-label="Underlisted features"></div>
  </div>
</section>
<script>
(function(){
  var ICONS = {
    score:'<path d="M3 12a9 9 0 1 0 18 0 9 9 0 0 0-18 0z"/><path d="M12 12l4-3"/><circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none"/>',
    fire:'<path d="M12 3c3 3 4.5 5.5 4.5 8.5a4.5 4.5 0 0 1-9 0c0-1.4.6-2.7 1.5-3.6.2 1.3 1 2.1 2 2.1 0-2 .3-4.4 1-7z"/><path d="M3 20.5c2-1.5 4-1.5 6 0s4 1.5 6 0 4-1.5 6 0" opacity=".7"/>',
    cost:'<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18"/><path d="M7 15h4"/>',
    cash:'<path d="M12 1v22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
    afford:'<path d="M9 11l3 3 8-8"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>',
    fore:'<path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M9 20v-6h6v6"/><circle cx="16.5" cy="7.5" r="2.4"/><path d="M16.5 6.4v2.2M15.4 7.5h2.2"/>',
    calc:'<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M8 6h8"/><path d="M8 11h.01M12 11h.01M16 11h.01M8 15h.01M12 15h.01M16 15v3"/>'
  };
  // `link` = the dedicated "See how it works" deep-dive page for each feature
  // (Quill's honest engineering explainers, one indexable URL per buyer search).
  // EXCEPTION: the Foreclosures node ALSO has a deep-dive, but we route it to
  // that deep-dive (which itself links onward to learn.html#what-is-reo).
  // `mc` = MEANING colour of the node's icon (owner wants instant scan, not all-gold):
  //   green = the deal / good / found · red = a warning · blue = a money tool.
  var FEATURES = [
    {id:'score', icon:'score', tone:'good', mc:'green', title:'Plain-English Deal Score',
     tag:'0\\u2013100 \\u00b7 green = good', link:'how-deal-score-works.html',
     what:'Every U.S. home gets one honest number from 0 to 100. Green means a genuinely under-priced deal \\u2014 no jargon, no spreadsheets, just "is this a good buy, yes or no."'},
    {id:'fire', icon:'fire', tone:'weak', mc:'red', title:'Fire & flood insurance risk',
     tag:'FEMA risk \\u00b7 warnings only', link:'how-insurance-risk-works.html', related:['cost','afford'],
     what:'We check FEMA fire and flood data for the address, so a pretty home in a high-risk zone never blindsides you with a sky-high insurance bill after you move in.'},
    {id:'cost', icon:'cost', tone:'okay', mc:'blue', title:'The true monthly cost',
     tag:'all-in, honest ranges', link:'how-true-monthly-cost-works.html', related:['afford','fire'],
     what:'Mortgage, taxes, insurance, PMI, HOA and upkeep \\u2014 gathered into one honest all-in number you can actually plan around, shown as realistic ranges, not a fantasy.'},
    {id:'cash', icon:'cash', tone:'okay', mc:'blue', title:'The real cash to the keys',
     tag:'down + closing + reserves', link:'how-cash-to-keys-works.html', related:['afford'],
     what:'Down payment, closing costs and a sensible reserve add up to the real cash you need in the bank before you get the keys \\u2014 no surprises at the closing table.'},
    {id:'afford', icon:'afford', tone:'good', mc:'blue', title:'"Can I afford it?"',
     tag:'green / amber / red verdict', link:'how-afford-check-works.html', related:['cost','cash'],
     what:'Enter your income, savings and debts once. Each home turns green, amber or red with "$X left every month," so you instantly see what you can comfortably carry.'},
    {id:'fore', icon:'fore', tone:'good', mc:'green', title:'Foreclosures, nationwide',
     tag:'HUD & USDA homes', link:'how-foreclosures-work.html',
     what:'Bank-owned and government (HUD / USDA) homes are folded into the same scored feed across the whole USA \\u2014 the deepest discounts, scored the same plain way as everything else.'},
    {id:'calc', icon:'calc', tone:'good', mc:'blue', title:'Free investor calculators',
     tag:'rental & fix-and-flip \\u00b7 free', link:'how-free-calculators-work.html',
     what:'Free rental cash-flow and fix-and-flip / ARV calculators \\u2014 cap rate, cash-on-cash, the 1% and 70% rules \\u2014 so beginners can run the numbers without signing up.'}
  ];

  var field  = document.getElementById('g-field');
  var stage  = document.getElementById('g-stage');
  var detail = document.getElementById('g-detail');
  var hub    = document.getElementById('g-hub');
  var list   = document.getElementById('g-list');
  if(!field || !stage) return;
  var R = 0.62;
  var nodeEls = {};

  FEATURES.forEach(function(f){
    var node = document.createElement('div');
    node.className = 'node mc-' + (f.mc||'gold');
    node.dataset.id = f.id;
    node.innerHTML =
      '<div class="spin-fix"><button aria-label="'+f.title.replace(/"/g,'&quot;')+'">'+
        '<span class="bubble"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '+
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'+ICONS[f.icon]+'</svg></span>'+
        '<span class="cap">'+f.title.replace(' insurance risk','').replace(/"/g,'')+'</span>'+
      '</button></div>';
    field.appendChild(node);
    nodeEls[f.id] = node;
    node.querySelector('button').addEventListener('click', function(e){ e.stopPropagation(); openCard(f.id); });
  });

  function place(){
    var half = stage.clientWidth/2;
    FEATURES.forEach(function(f,i){
      var ang = (i / FEATURES.length) * Math.PI*2 - Math.PI/2;
      var x = Math.cos(ang) * R * half;
      var y = Math.sin(ang) * R * half;
      nodeEls[f.id].style.transform = 'translate('+x+'px,'+y+'px)';
    });
  }
  window.addEventListener('resize', place); place();

  var activeId = null;
  function openCard(id){
    var f = FEATURES.find(function(x){return x.id===id;});
    activeId = id;
    stage.classList.add('paused','has-active');
    Object.keys(nodeEls).forEach(function(k){ nodeEls[k].classList.remove('active','related'); });
    nodeEls[id].classList.add('active');
    (f.related||[]).forEach(function(r){ if(nodeEls[r]) nodeEls[r].classList.add('related'); });
    detail.innerHTML =
      '<div class="card mc-'+(f.mc||'gold')+'">'+
        '<button class="x" aria-label="Close">'+
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>'+
        '</button>'+
        '<div class="ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'+ICONS[f.icon]+'</svg></div>'+
        '<h3>'+f.title+'</h3>'+
        '<p class="what">'+f.what+'</p>'+
        '<span class="chip '+f.tone+'">'+f.tag+'</span><br>'+
        '<a class="seemore" href="'+f.link+'">See how it works <span aria-hidden="true">\\u2192</span></a>'+
      '</div>';
    detail.classList.add('show');
    detail.querySelector('.x').addEventListener('click', function(e){ e.stopPropagation(); closeCard(); });
  }
  function closeCard(){
    activeId = null;
    detail.classList.remove('show');
    stage.classList.remove('paused','has-active');
    Object.keys(nodeEls).forEach(function(k){ nodeEls[k].classList.remove('active','related'); });
  }
  hub.addEventListener('click', function(){ if(activeId) closeCard(); });
  stage.addEventListener('click', closeCard);
  detail.addEventListener('click', function(e){ e.stopPropagation(); });
  document.addEventListener('keydown', function(e){ if(e.key==='Escape') closeCard(); });

  // mobile fallback — stacked cards, each with the same "See how it works" link
  FEATURES.forEach(function(f){
    var c = document.createElement('div');
    c.className = 'fcard mc-' + (f.mc||'gold');
    c.innerHTML =
      '<div class="frow">'+
        '<span class="fic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'+ICONS[f.icon]+'</svg></span>'+
        '<span><h3>'+f.title+'</h3><p class="what">'+f.what+'</p>'+
        '<span class="chip '+f.tone+'">'+f.tag+'</span></span>'+
      '</div>'+
      '<a class="seemore" href="'+f.link+'">See how it works <span aria-hidden="true">\\u2192</span></a>';
    list.appendChild(c);
  });
})();
</script>
"""


def index_page(city_chips: str) -> str:
    body = (
        # ===== CINEMATIC HERO (dark dusk-house opener — replaces the old masthead) =====
        cinematic_hero_section() +

        # ===== "HOW IT WORKS" — UNFOLD-THE-STORY collapsible (progressive disclosure).
        # The five "story" sections below (best-deals → galaxy → why → glance → teaser)
        # are wrapped in ONE container, #howitworks, that the visitor unfolds by
        # tapping "How it works" (hero ghost button OR header nav). It renders OPEN in
        # the HTML so no-JS users and search crawlers see every word (SEO-safe — we
        # NEVER server-remove it); a tiny inline JS guard collapses it on load when JS
        # is on, so the default reading flow is the calm: cover → free tools → waitlist.
        # The wrapper itself carries NO background, so when collapsed the cover's
        # ivory foot (.ch-fade) flows straight into the free-tools section below with
        # no hard seam. Smooth height via grid-template-rows 0fr↔1fr (reduced-motion
        # falls back to an instant toggle). See the .hiw CSS + the inline JS below.
        "<div id='howitworks' class='hiw hiw--open' role='region' "
        "aria-label='How Underlisted works'><div class='hiw-inner'>"

        # ===== THE "SEE WHAT YOU GET" MAP — matched tiles, scanned in one screen =====
        # Restructured 2026-06-21 (Juliet): instead of five stacked full-bleed
        # sections you scroll through, the revealed story is a 2-up grid of matched
        # tiles on the ivory page → far less scroll, reads like a real "map".
        #   Row 1: constellation (LEFT, own dark card) | how-we-find-them (RIGHT)
        #   Row 2: "four things…" (LEFT) | "one home, three seconds" (RIGHT)
        #   Row 3: locked teaser (full-width). Stacks to one column ≤860px.
        "<div class='hiw-map'>" +

        # ── Row 1 LEFT: the interactive constellation, inside its OWN dark card
        #    (frames the dark field as a tile → NO dark/light section seam) ──
        "<div class='maptile maptile--dark'>" + feature_galaxy_section() + "</div>" +

        # ── Row 1 RIGHT: "Here's how we find them" (live count + ZIP search box) ──
        "<div class='maptile find-tile'>" + best_deals_section() + "</div>" +

        # ── Row 2 LEFT: WHY UNDERLISTED — four things, one scannable line each ──
        "<div class='maptile why reveal'><section class='sec' id='why'><div class='wrap'>"
        "<div class='sec-head'><div class='kicker'>Why Underlisted</div>"
        "<h2>Four things every site makes you <em>figure out alone.</em></h2></div>"
        "<div class='why-list'>"
        f"<div class='why-item'><div class='no'>I.</div>"
        "<div class='txt'><h3>A plain-English <span class='mk-green'>Deal Score</span></h3>"
        "<p>Every home, one 0–100 number. Green = a good deal.</p></div><div class='seal'>0–100</div></div>"
        f"<div class='why-item'><div class='no'>II.</div>"
        "<div class='txt'><h3><span class='mk-red'>Fire &amp; flood</span> insurance warning</h3>"
        "<p>FEMA risk flagged before you fall in love.</p></div><div class='seal'>FEMA</div></div>"
        f"<div class='why-item'><div class='no'>III.</div>"
        "<div class='txt'><h3>The <span class='mk-blue'>true monthly cost</span></h3>"
        "<p>Mortgage + tax + insurance + upkeep + HOA, all-in.</p></div><div class='seal'>All-in</div></div>"
        f"<div class='why-item'><div class='no'>IV.</div>"
        "<div class='txt'><h3>The <span class='mk-blue'>real cash</span> you'd need</h3>"
        "<p>Down payment + closing — the money to get the keys.</p></div><div class='seal'>To keys</div></div>"
        "</div></div></section></div>"

        # ── Row 2 RIGHT: WHAT YOU SEE — one home, read in three seconds ──
        "<div class='maptile glance reveal'><section class='sec' id='glance'><div class='wrap'>"
        "<div class='sec-head'><div class='kicker'>What you see</div>"
        "<h2>One home, read in <em>three seconds.</em></h2></div>"
        "<div class='glance-card'>"
        "<div class='glance-top'><span class='addr'>Maple Ridge Bungalow</span>"
        "<span class='meta'>Houston, TX · 3 bed · 2 bath</span>"
        f"<span class='chip'>{svg('check', w=14)}Strong deal</span></div>"
        "<div class='stat-grid'>"
        f"<div class='stat'><div class='l'>{svg('bank', w=16)}True cost / month</div><div class='v good tnum'>$2,540</div><div class='f'>All-in, no surprises</div></div>"
        f"<div class='stat'><div class='l'>{svg('coin', w=16)}Real cash needed</div><div class='v tnum'>$48,060</div><div class='f'>To actually buy</div></div>"
        f"<div class='stat'><div class='l'>{svg('wave', w=16)}Flood risk</div><div class='v good'>Low</div><div class='f'>Insurance friendly</div></div>"
        f"<div class='stat'><div class='l'>{svg('fire', w=16)}Fire risk</div><div class='v okay'>Moderate</div><div class='f'>Watch insurance</div></div>"
        "</div></div></div></section></div>"

        # ── Row 3 FULL-WIDTH: the locked teaser ("the free part is the address…") ──
        "<div class='maptile teaser-row row-full reveal'>" + locked_teaser_section() + "</div>"

        # close .hiw-map
        "</div>" +

        # tasteful "▲ Hide" control — collapses #howitworks and scrolls the reader
        # back up to the cover. A real <button> (keyboard-operable); the JS wires the
        # collapse + scroll. data-hiw-hide tells the script this one only closes.
        "<div class='hiw-hidebar'><button type='button' class='hiw-hide' "
        "data-hiw-hide aria-controls='howitworks'>"
        "<span class='chev'>&#9650;</span> Hide how it works</button></div>"
        # close .hiw-inner + #howitworks (the collapsible wrapper opened above the
        # best-deals section). Everything BELOW this stays always-visible.
        "</div></div>" +

        # EARLY COLLAPSE GUARD — runs the instant this point is parsed (the #howitworks
        # element already exists above), BEFORE the free-tools/waitlist below paint. So
        # JS-on visitors never see the story flash open then snap shut: it's collapsed
        # pre-paint. JS-off visitors (and crawlers) skip this and keep it open. Full
        # toggle wiring lives in HIW_JS at the end of <body>.
        "<script>(function(){var e=document.getElementById('howitworks');"
        "if(e){e.classList.remove('hiw--open');"
        "document.querySelectorAll('[data-hiw-toggle]').forEach(function(t){"
        "t.setAttribute('aria-expanded','false');});}})();</script>" +

        # ===== EVERYTHING YOU GET — static full-colour feature grid =====
        # Always-visible (sits OUTSIDE the collapsible #howitworks above). Pairs
        # with the spinning constellation: same features, but here the illustrated
        # full-colour art is the star, in a calm premium grid. (Juliet 2026-06-24)
        feature_grid_section() +

        # ===== FREE TOOLS =====
        "<section class='sec' id='tools'><div class='wrap'>"
        "<div class='sec-head reveal'><div class='kicker'>Free to try</div>"
        "<h2>Run the numbers <em>before</em> you fall in love.</h2>"
        f"<p>Four plain-English calculators. No signup, no math homework. {free_badge(big=True)}</p></div>"
        "<div class='tools-grid'>"
        f"<a class='tool reveal' href='home-affordability-calculator.html'><div class='ico illus'>{icon_img('afford','Can I afford it')}</div><h4>Can I afford it?</h4>"
        f"<p>Income, cash and debts → green, amber or red.</p>{free_badge()}</a>"
        f"<a class='tool reveal' href='cash-to-close-calculator.html'><div class='ico illus'>{icon_img('cash','Cash to the keys')}</div><h4>Cash to the keys</h4>"
        f"<p>Down payment + closing, the real number.</p>{free_badge()}</a>"
        f"<a class='tool reveal' href='rent-vs-buy-calculator.html'><div class='ico illus'>{icon_img('cost','Rent vs buy')}</div><h4>Rent vs buy</h4>"
        f"<p>Which one really wins for you, and when.</p>{free_badge()}</a>"
        f"<a class='tool reveal' href='mortgage-payoff-calculator.html'><div class='ico illus'>{icon_img('calc','Payoff time')}</div><h4>Payoff time</h4>"
        f"<p>How fast a little extra clears the loan.</p>{free_badge()}</a>"
        "</div>"
        # city chips — real SEO links to the city pages
        "<div class='pagelinks reveal' style='margin-top:44px'>"
        "<div class='kicker' style='margin-bottom:14px'>Deals by city</div>"
        f"{city_chips}</div>"
        "</div></section>"

        # ===== WAITLIST =====
        + WAITLIST

        # ===== "HOW IT WORKS" toggle wiring (index-only) =====
        + HIW_JS
    )
    return shell(
        "Underlisted — the homes worth buying, made obvious",
        "Every home in America, scored in plain English. Green means a real deal — "
        "with fire/flood insurance risk, the true monthly cost, and the real cash you'd need.",
        body, here="index",
        # VALUE_DASHBOARD_CSS dropped from injection — its only consumer (the
        # 3-lane table) is no longer rendered on the homepage. Constant stays
        # defined for reuse; re-add it here if the dashboard is ever brought back.
        extra_head=CINEMATIC_HERO_CSS + HIW_MAP_CSS, show_header=False,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Listing card (city + report pages) — Cormorant price, gold score gauge, pills.
# ──────────────────────────────────────────────────────────────────────────────
def card_html(row) -> str:
    l, s = row["listing"], row["score"]
    disc = _discount(row)
    risk = row.get("risk")
    score = s.total
    color = _score_color(score)
    # gold-haloed conic score ring (the Deal Dial signature, miniature)
    pct = max(0, min(100, score))
    ring = (f"background:conic-gradient({color} 0 {pct}%, rgba(26,106,72,.15) {pct}% 100%);"
            "padding:5px")
    gauge = (f"<div class='gauge'><div class='ring' style='{ring}'></div>"
             f"<div style='position:absolute;inset:5px;border-radius:50%;background:var(--surface)'></div>"
             f"<div class='num' style='color:{color}'>{score}</div></div>")
    pills = ""
    if disc and disc > 0:
        pills += f"<span class='pill good'>{svg('tag', w=13)}{disc:.0f}% below value</span>"
    if risk and getattr(risk, "flood_zone", "") == "High":
        pills += f"<span class='pill warn'>{svg('wave', w=13)}Flood zone</span>"
    if risk and getattr(risk, "fire_zone", "") in ("High", "Moderate"):
        pills += f"<span class='pill warn'>{svg('fire', w=13)}{risk.fire_zone} fire risk</span>"
    pills_html = f"<div class='pills'>{pills}</div>" if pills else ""
    trend = market.price_trend(l.zip_code)
    tr = ""
    if trend and trend.get("change") is not None:
        up = trend["change"] >= 0
        tr = (f"<div class='trend'>Area prices {'▲' if up else '▼'} "
              f"{abs(trend['change']):.1f}% ({trend['year']})</div>")
    return (
        "<div class='lcard reveal'>"
        f"{gauge}"
        "<div class='body'>"
        f"<div class='price tnum'>{money(l.list_price)}</div>"
        f"<div class='addr'>{l.address or '—'}</div>"
        f"{pills_html}{tr}"
        "</div></div>"
    )


# ──────────────────────────────────────────────────────────────────────────────
# LEARN — editorial glossary, one shared source (src/glossary.py).
# ──────────────────────────────────────────────────────────────────────────────
LEARN_EXTRA_EG = {
    "deal-score":
        f"<div class='scorekey'><span style='background:{GOOD}'><span class='dot'></span>70–100 Good</span>"
        f"<span style='background:{OKAY}'><span class='dot'></span>45–69 Okay</span>"
        f"<span style='background:{WEAK}'><span class='dot'></span>0–44 Weak</span></div>",
}


def foreclosure_journey_section() -> str:
    """SEO explainer: pre-foreclosure → foreclosure → auction → bank-owned (REO).

    Plain-English, brand-safe (Ivory & Gold), mobile-first. Each stage gets its
    own anchor id so the homepage 'Foreclosures nationwide' galaxy node can deep
    link here (recommended target: learn.html#what-is-reo). No billable calls.
    """
    stages = [
        dict(
            id="pre-foreclosure", num="1", cls="early", chip="Early warning",
            title="Pre-foreclosure",
            body=(
                "The owner has <b>fallen behind on their mortgage payments</b> — but "
                "they haven't lost the home yet. There's still a chance they catch up, "
                "or sell before the bank steps in. Think of this as the <b>early-warning "
                "stage</b>: the home isn't truly for sale yet, but trouble is brewing."
            ),
        ),
        dict(
            id="foreclosure", num="2", cls="caution", chip="Bank takes over",
            title="Foreclosure",
            body=(
                "The owner couldn't catch up. So the bank takes <b>legal action to take "
                "the home back</b> and recover the money it lent. At this point the owner "
                "must leave. The home is now headed toward a sale — but it's the bank, not "
                "the owner, calling the shots."
            ),
        ),
        dict(
            id="auction", num="3", cls="caution", chip="Risky · cash-only",
            title="Auction",
            body=(
                "The bank sells the home to the <b>highest bidder</b> — on the courthouse "
                "steps or online. Prices can be very cheap. But this is the <b>risky</b> "
                "stage for a normal buyer: it's usually <b>cash-only</b>, sold strictly "
                "<b>“as-is,”</b> and often with <b>no inspection</b> and no chance to walk "
                "through first. This stage is really for experienced investors who can "
                "absorb surprises."
            ),
        ),
        dict(
            id="what-is-reo", num="4", cls="warm", chip="Friendliest for buyers",
            title="Bank-owned / REO",
            body=(
                "If nobody buys it at auction, the <b>bank now owns the home</b> outright. "
                "That's what <b>“REO”</b> means — <b>Real Estate Owned</b> (by the bank). "
                "Now the bank lists it like a normal home, through a regular agent. This is "
                "the <b>friendliest of the three</b> for a regular buyer: you can usually "
                "<b>tour it, get an inspection, and use a normal mortgage</b> — and because "
                "the bank just wants it off its books, it's often <b>priced to sell</b>."
            ),
        ),
    ]
    steps = "".join(
        f"<li class='fj-step {s['cls']}' id='{s['id']}'>"
        f"<span class='num'>{s['num']}</span>"
        f"<h3>{s['title']}<span class='chip'>{s['chip']}</span></h3>"
        f"<p>{s['body']}</p></li>"
        for s in stages
    )
    return (
        "<section class='sec' style='padding-top:8px'><div class='wrap'>"
        "<div class='fjourney reveal' id='foreclosure-explained'>"
        "<div class='fj-head'>"
        "<div class='kicker'>The foreclosure journey</div>"
        "<h2>Foreclosure, auction &amp; bank-owned homes — <em>explained.</em></h2>"
        "<p>You'll hear these four words a lot when hunting for under-priced homes. "
        "They're really just <b>four stages of the same story</b> — what happens after an "
        "owner can't pay. Here's the journey, in plain English.</p>"
        "</div>"
        f"<ul class='fj-steps'>{steps}</ul>"
        "<div class='fj-why'>"
        "<h3>Why this matters for your search</h3>"
        "<p>In every one of these cases, the bank just wants <b>its money back — not top "
        "dollar.</b> That's exactly why these homes are so often <b>under-priced</b>, and "
        "exactly the kind of deal Underlisted is built to surface for you.</p>"
        "</div>"
        "<div class='fj-caveat'>"
        "<span class='ic'>&#9888;</span>"
        "<span>One honest heads-up: these homes carry more risk than a normal sale — "
        "<b>auctions especially</b>, where there's usually no inspection. Always verify the "
        "condition, title, and any liens before you buy.</span>"
        "</div>"
        "</div></div></section>"
    )


def learn_page() -> str:
    toc = "".join(f"<a href='#{t.key}'>{t.label}</a>" for t in glossary.TERMS)
    cards = []
    for t in glossary.TERMS:
        body = "".join(f"<p>{p}</p>" for p in t.paragraphs)
        eg = LEARN_EXTRA_EG.get(t.key, t.example)
        if eg:
            body += f"<div class='eg'>{eg}</div>"
        cls = "term warnterm" if t.warn else "term"
        cards.append(
            f"<div class='{cls}' id='{t.key}'>"
            f"<h2><span class='ic'>{t.icon}</span>{t.title}</h2>{body}</div>"
        )
    page_body = (
        "<section class='masthead' style='padding-bottom:0'><div class='wrap'>"
        "<div class='learn-intro reveal in'>"
        f"<div class='kicker learn-kicker'>{free_badge(big=True)} &nbsp;Plain English · the whole glossary</div>"
        "<h1>Learn the basics — <em>without the jargon.</em></h1>"
        "<p>Buying a home comes with a lot of confusing words. Here's every term we show "
        "you, explained simply — like we're chatting at the kitchen table. No jargon, no "
        "pressure. This page is free. Tap a word to jump to it.</p>"
        f"<div class='toc'>{toc}</div></div></div></section>"
        "<section class='sec' style='padding-top:30px;padding-bottom:14px'><div class='wrap'>"
        f"<div class='term-list'>{''.join(cards)}</div>"
        "</div></section>"
        f"{foreclosure_journey_section()}"
        "<section class='sec' style='padding-top:18px'><div class='wrap'>"
        "<p class='pagelinks'>That's the whole glossary. When you see any of these inside "
        "Underlisted, you'll know exactly what it means. "
        "<a href='index.html'>← Back to the deals</a></p>"
        "</div></section>"
    )
    return shell(
        "What is an REO home? Pre-foreclosure, foreclosure & auction — explained "
        "simply | Underlisted",
        "What is an REO (bank-owned) home? A free, plain-English guide for first-time "
        "buyers to pre-foreclosure, foreclosure, auction and bank-owned / REO homes — plus "
        "a simple glossary: deal score, underpriced, true monthly cost, PMI, HOA, cash to "
        "close and insurance risk.",
        page_body, here="learn",
    )


# Backward-compatible alias: the learn page used to be exposed as
# `learn_page_body()`. The rewrite renamed it to `learn_page()`. Keep the old
# public name so callers/tests that depend on the shared-glossary contract
# (website + app must build the learn page from the SAME glossary) keep working.
learn_page_body = learn_page


# ──────────────────────────────────────────────────────────────────────────────
# THANKS — waitlist redirect target (noindex). Same brand, no form.
# ──────────────────────────────────────────────────────────────────────────────
def thanks_page() -> str:
    body = (
        "<section class='masthead'><div class='wrap'>"
        "<div class='dateline reveal in'><span class='dot'></span>You're on the list</div>"
        "<h1 class='reveal in'>You're <em>in.</em></h1>"
        "<p class='lede reveal in'>Thanks! You'll be first to know when we open — and your "
        "<b>$19.99/mo founding price (locked for a full year)</b> is reserved. No spam, just your invite.</p>"
        "<div class='cta-row reveal in'>"
        f"<a class='btn-fill' href='index.html'>Back to the deals {svg('arrow', w=18)}</a>"
        "<a class='btn-line' href='learn.html'>Learn the basics <span class='ar'>→</span></a>"
        "</div></div></section>"
    )
    return shell(
        "You're on the list | Underlisted",
        "Thanks for joining the Underlisted waitlist — your founding price is reserved.",
        body, robots="noindex",
    )


# ──────────────────────────────────────────────────────────────────────────────
# The FOUR calculator bodies. Markup + <script> ported VERBATIM from the verified
# previews in design_preview/ (math signed off by Vera + Forge). Only the brand
# chrome around them is reskinned via CALC_CSS. Do NOT edit the math here.
# ──────────────────────────────────────────────────────────────────────────────

def _payoff_calc_body() -> str:
    return r"""
    <div class="toggle" role="tablist">
      <button id="tab1" class="on" onclick="setMode(1)">I'll pay $X a month</button>
      <button id="tab2" onclick="setMode(2)">Be done in Y years</button>
    </div>
    <div class="card">
      <div class="field">
        <label for="loan">Loan amount <span class="hint">— what you still owe</span></label>
        <div class="inputwrap"><span class="pre">$</span>
          <input id="loan" class="has-pre" type="text" inputmode="numeric" value="300,000" /></div>
      </div>
      <div class="field">
        <label for="rate">Interest rate</label>
        <div class="inputwrap"><input id="rate" class="has-post" type="text" inputmode="decimal" value="6.5" />
          <span class="post">%</span></div>
      </div>
      <div class="field" id="f-payment">
        <label for="payment">Monthly payment <span class="hint">— just the loan part</span></label>
        <div class="inputwrap"><span class="pre">$</span>
          <input id="payment" class="has-pre" type="text" inputmode="numeric" value="1,950" /></div>
      </div>
      <div class="field" id="f-years" style="display:none">
        <label for="years">Pay it off in</label>
        <div class="inputwrap"><input id="years" class="has-post" type="text" inputmode="numeric" value="20" />
          <span class="post">years</span></div>
      </div>
    </div>
    <div class="extra">
      <div class="toprow"><span class="spark">✨</span><h3>Add extra each month</h3></div>
      <p class="sub">Even a small amount can shave off years. Try it.</p>
      <div class="field" style="margin:0"><div class="inputwrap"><span class="pre">$</span>
        <input id="extra" class="has-pre" type="text" inputmode="numeric" value="200" /></div></div>
    </div>
    <div class="answer" id="answer">
      <div class="eyebrow" id="ans-eyebrow">You'll own it free &amp; clear in</div>
      <div class="big" id="ans-big">—</div>
      <div class="lede" id="ans-lede"></div>
    </div>
    <div class="stats">
      <div class="stat"><div class="k" id="s1-k">Interest you'll pay</div><div class="v tnum" id="s1-v">—</div></div>
      <div class="stat muted-stat"><div class="k" id="s2-k">Total of all payments</div><div class="v tnum" id="s2-v">—</div></div>
    </div>
    <div class="card timeline" id="timeline">
      <div class="barlabels"><span>What you borrowed</span><span>What it costs in interest</span></div>
      <div class="bar"><div class="principal" id="bar-p" style="width:70%"></div>
        <div class="interest" id="bar-i" style="width:30%"></div></div>
      <div class="legend"><span><i class="dot g"></i> Loan (principal)</span><span><i class="dot a"></i> Interest</span></div>
    </div>
    <div class="card" id="savecard">
      <p class="saveline idle" id="saveline">Add an amount above to see how much sooner you'd be done.</p>
    </div>
    <p class="disclaimer">An estimate to help you picture it — not a loan offer.<br/>
      Shows the loan-only payment; taxes &amp; insurance aren't included.</p>
<script>
  function num(id){var raw=(document.getElementById(id).value||"").replace(/[^0-9.]/g,"");var v=parseFloat(raw);return isFinite(v)?v:0;}
  function money(n){return "$"+Math.round(n).toLocaleString("en-US");}
  function plainTime(months){months=Math.max(0,Math.round(months));var y=Math.floor(months/12);var m=months%12;
    var yStr=y+" year"+(y===1?"":"s");var mStr=m+" month"+(m===1?"":"s");if(y===0)return mStr;if(m===0)return yStr;return yStr+" "+mStr;}
  function paymentForTerm(L,r,n){if(n<=0)return 0;if(r===0)return L/n;return L*r/(1-Math.pow(1+r,-n));}
  function monthsForPayment(L,r,M){if(M<=0)return Infinity;if(r===0)return Math.ceil(L/M);if(M<=L*r)return Infinity;
    var n=-Math.log(1-(L*r)/M)/Math.log(1+r);return Math.ceil(n);}
  var mode=1;
  function setMode(m){mode=m;document.getElementById("tab1").classList.toggle("on",m===1);
    document.getElementById("tab2").classList.toggle("on",m===2);
    document.getElementById("f-payment").style.display=(m===1)?"":"none";
    document.getElementById("f-years").style.display=(m===2)?"":"none";compute();}
  function compute(animateSave){
    var L=num("loan");var annual=num("rate");var r=annual/100/12;var extra=Math.max(0,num("extra"));
    var answer=document.getElementById("answer");var eyebrow=document.getElementById("ans-eyebrow");
    var big=document.getElementById("ans-big");var lede=document.getElementById("ans-lede");
    var s1k=document.getElementById("s1-k"),s1v=document.getElementById("s1-v");
    var s2k=document.getElementById("s2-k"),s2v=document.getElementById("s2-v");
    var saveline=document.getElementById("saveline");var payInput=document.getElementById("payment");
    payInput.classList.remove("bad");
    if(L<=0){answer.classList.remove("warn");eyebrow.textContent="Enter a loan amount";big.textContent="—";lede.textContent="";
      s1v.textContent="—";s2v.textContent="—";saveline.className="saveline idle";
      saveline.textContent="Fill in the loan above to see your payoff.";setBar(1,0);return;}
    var basePayment,baseMonths,neverPaysOff=false;
    if(mode===1){basePayment=num("payment");baseMonths=monthsForPayment(L,r,basePayment);if(!isFinite(baseMonths))neverPaysOff=true;}
    else{var years=Math.max(0,num("years"));var n=Math.round(years*12);basePayment=paymentForTerm(L,r,n);baseMonths=n;}
    if(neverPaysOff){payInput.classList.add("bad");answer.classList.add("warn");eyebrow.textContent="Hmm — that won't get there";
      var monthlyInterest=L*r;big.innerHTML="That payment only covers the interest.";
      lede.innerHTML="Right now you'd need about <b>"+money(monthlyInterest)+"/mo</b> just to cover interest, so the balance never shrinks. Try a bit higher.";
      s1k.textContent="Interest you'll pay";s1v.textContent="—";s2k.textContent="Total of all payments";s2v.textContent="—";
      setBar(0,1);saveline.className="saveline idle";saveline.textContent="Once it pays off, the extra-payment savings will show here.";return;}
    answer.classList.remove("warn");var baseTotalPaid=basePayment*baseMonths;var baseInterest=Math.max(0,baseTotalPaid-L);
    var withPayment=basePayment+extra;var withMonths=monthsForPayment(L,r,withPayment);if(!isFinite(withMonths))withMonths=baseMonths;
    var withTotal=withPayment*withMonths;var withInterest=Math.max(0,withTotal-L);
    var shownMonths=(extra>0)?withMonths:baseMonths;var shownInterest=(extra>0)?withInterest:baseInterest;var shownTotal=(extra>0)?withTotal:baseTotalPaid;
    eyebrow.textContent="You'll own it free & clear in";big.innerHTML=plainTimeHTML(shownMonths);
    if(mode===2){lede.innerHTML="To finish that fast, pay <b>"+money(withPayment)+"/mo</b>"+(extra>0?" (incl. your $"+Math.round(extra).toLocaleString()+" extra).":".");}
    else{lede.innerHTML=(extra>0)?"Paying <b>"+money(withPayment)+"/mo</b> total (with your extra).":"At <b>"+money(basePayment)+"/mo</b>.";}
    s1k.textContent="Interest you'll pay";s1v.textContent=money(shownInterest);
    s2k.textContent="Total of all payments";s2v.textContent=money(shownTotal);setBar(L,shownInterest);
    if(extra>0){var monthsSaved=baseMonths-withMonths;var interestSaved=Math.max(0,baseInterest-withInterest);
      if(monthsSaved>0||interestSaved>0){saveline.className="saveline";
        saveline.innerHTML="Add just <b>"+money(extra)+" more</b> a month and you'd own it <b>"+plainTime(monthsSaved)+" sooner</b> — saving <b>"+money(interestSaved)+"</b> in interest.";
        if(animateSave){var sc=document.getElementById("savecard");sc.classList.remove("pop");void sc.offsetWidth;sc.classList.add("pop");}}
      else{saveline.className="saveline idle";saveline.textContent="That extra doesn't change much here — try a larger amount.";}}
    else{saveline.className="saveline idle";saveline.textContent="Add an amount above to see how much sooner you'd be done.";}}
  function plainTimeHTML(months){months=Math.max(0,Math.round(months));var y=Math.floor(months/12);var m=months%12;var out="";
    if(y>0)out+=y+'<span class="unit"> year'+(y===1?"":"s")+'</span>';
    if(m>0||y===0)out+=(y>0?" ":"")+m+'<span class="unit"> month'+(m===1?"":"s")+'</span>';return out;}
  function setBar(principal,interest){var total=principal+interest;var pPct=total>0?(principal/total)*100:100;var iPct=100-pPct;
    document.getElementById("bar-p").style.width=pPct.toFixed(1)+"%";document.getElementById("bar-i").style.width=iPct.toFixed(1)+"%";}
  function formatThousands(el){var start=el.selectionStart;var before=el.value;var digits=before.replace(/[^0-9]/g,"");
    if(digits===""){el.value="";return;}var formatted=parseInt(digits,10).toLocaleString("en-US");el.value=formatted;
    var diff=formatted.length-before.length;var pos=Math.max(0,(start||formatted.length)+diff);try{el.setSelectionRange(pos,pos);}catch(e){}}
  ["loan","payment","extra"].forEach(function(id){var el=document.getElementById(id);
    el.addEventListener("input",function(){formatThousands(el);compute(id==="extra");});});
  ["rate","years"].forEach(function(id){document.getElementById(id).addEventListener("input",function(){compute();});});
  compute();
</script>"""


def _afford_calc_body() -> str:
    return r"""
    <div class="card">
      <div class="grid2">
        <div class="field">
          <label for="income">Yearly income <span class="hint">— before tax</span></label>
          <div class="inputwrap"><span class="pre">$</span>
            <input id="income" class="has-pre" type="text" inputmode="numeric" value="90,000" /></div>
        </div>
        <div class="field">
          <label for="debts">Monthly debts <span class="hint">— car, student, cards</span></label>
          <div class="inputwrap"><span class="pre">$</span>
            <input id="debts" class="has-pre" type="text" inputmode="numeric" value="450" /></div>
        </div>
      </div>
      <div class="grid2">
        <div class="field">
          <label for="cash">Cash for down payment</label>
          <div class="inputwrap"><span class="pre">$</span>
            <input id="cash" class="has-pre" type="text" inputmode="numeric" value="40,000" /></div>
        </div>
        <div class="field">
          <label for="rate">Interest rate</label>
          <div class="inputwrap"><input id="rate" class="has-post" type="text" inputmode="decimal" value="6.6" />
            <span class="post">%</span></div>
        </div>
      </div>
      <div class="field" style="margin-bottom:0">
        <label>Down payment <span class="hint">— share of the price you pay upfront</span></label>
        <div class="seg" id="seg">
          <button data-dp="3" onclick="setDP(3)">3%</button>
          <button data-dp="5" onclick="setDP(5)">5%</button>
          <button data-dp="10" class="on" onclick="setDP(10)">10%</button>
          <button data-dp="20" onclick="setDP(20)">20%</button>
        </div>
      </div>
    </div>
    <div class="answer" id="answer">
      <div class="eyebrow" id="ans-eyebrow">You could comfortably afford a home around</div>
      <div class="big" id="ans-big">—</div>
      <div class="lede" id="ans-lede"></div>
    </div>
    <div class="stats">
      <div class="stat"><div class="k" id="s1-k">Comfortable monthly payment</div><div class="v tnum" id="s1-v">—</div></div>
      <div class="stat muted-stat"><div class="k" id="s2-k">Cash you'd put down</div><div class="v tnum" id="s2-v">—</div></div>
    </div>
    <div class="card timeline" id="timeline">
      <div class="barlabels"><span>Housing as a share of income</span><span id="dti-label">—</span></div>
      <div class="bar"><div class="used" id="bar-u" style="width:50%"></div></div>
      <div class="legend"><span><i class="dot g"></i> Comfortable (under 28%)</span>
        <span><i class="dot a"></i> A stretch (28–36%)</span></div>
    </div>
    <div class="magic col" id="magiccard">
      <div class="toprow"><span class="spark">✨</span><h3>One small move, more home</h3></div>
      <p class="magicline idle" id="magicline">Adjust your numbers to see how to unlock more buying power.</p>
    </div>
    <p class="disclaimer">A comfortable estimate to help you picture it — not a loan approval.<br/>
      Keeps your housing under ~28% of income, with room set aside for taxes, insurance &amp; PMI.</p>
<script>
  var TAX_PCT_YR=(0.5+2.1)/2/100;var INS_PCT_YR=(0.35+0.80)/2/100;var PMI_PCT_YR=(0.4+1.2)/2/100;
  var HOA_MONTHLY=(0+350)/2;var PMI_BELOW_DP=20;var FRONT_DTI=28;var TOTAL_DTI=36;var TERM_YEARS=30;
  var dp=10;
  function num(id){var raw=(document.getElementById(id).value||"").replace(/[^0-9.]/g,"");var v=parseFloat(raw);return isFinite(v)?v:0;}
  function money(n){return "$"+Math.round(n).toLocaleString("en-US");}
  function moneyK(n){n=Math.round(n);if(n>=100000)return "$"+(Math.round(n/1000)*1000).toLocaleString("en-US");
    if(n>=10000)return "$"+(Math.round(n/500)*500).toLocaleString("en-US");return "$"+n.toLocaleString("en-US");}
  function loanForPI(pi,r,n){if(pi<=0)return 0;if(r===0)return pi*n;return pi*(1-Math.pow(1+r,-n))/r;}
  function solveMaxPrice(housingBudget,r,n){if(housingBudget<=0)return {price:0,loan:0,pi:0,down:0};
    var dpFrac=dp/100;var pmiOn=dp<PMI_BELOW_DP;var price=housingBudget*200;
    for(var i=0;i<40;i++){var loan=price*(1-dpFrac);var taxM=price*TAX_PCT_YR/12;var insM=price*INS_PCT_YR/12;
      var pmiM=pmiOn?loan*PMI_PCT_YR/12:0;var piBudget=housingBudget-taxM-insM-pmiM-HOA_MONTHLY;
      if(piBudget<=0)return {price:0,loan:0,pi:0,down:0};var newLoan=loanForPI(piBudget,r,n);var newPrice=newLoan/(1-dpFrac);
      if(Math.abs(newPrice-price)<1){price=newPrice;break;}price=newPrice;}
    var loan2=price*(1-dpFrac);var taxM2=price*TAX_PCT_YR/12;var insM2=price*INS_PCT_YR/12;var pmiM2=pmiOn?loan2*PMI_PCT_YR/12:0;
    var pi=housingBudget-taxM2-insM2-pmiM2-HOA_MONTHLY;
    return {price:price,loan:loan2,pi:Math.max(0,pi),down:price*dpFrac,taxM:taxM2,insM:insM2,pmiM:pmiM2,hoaM:HOA_MONTHLY};}
  function affordability(incomeMonthly,debts,r,n){var front=incomeMonthly*FRONT_DTI/100;var back=incomeMonthly*TOTAL_DTI/100-debts;
    var housingBudget=Math.min(front,back);var res=solveMaxPrice(housingBudget,r,n);res.housingBudget=housingBudget;
    res.frontCap=front;res.backCap=back;res.dtiPct=incomeMonthly>0?(housingBudget/incomeMonthly)*100:0;return res;}
  function setDP(v){dp=v;document.querySelectorAll('#seg button').forEach(function(b){b.classList.toggle('on',parseInt(b.dataset.dp,10)===v);});compute();}
  function compute(animateMagic){
    var income=num("income");var incomeMonthly=income/12;var debts=Math.max(0,num("debts"));var cash=Math.max(0,num("cash"));
    var r=num("rate")/100/12;var n=TERM_YEARS*12;
    var answer=document.getElementById("answer");var eyebrow=document.getElementById("ans-eyebrow");
    var big=document.getElementById("ans-big");var lede=document.getElementById("ans-lede");
    var s1k=document.getElementById("s1-k"),s1v=document.getElementById("s1-v");
    var s2k=document.getElementById("s2-k"),s2v=document.getElementById("s2-v");
    var barU=document.getElementById("bar-u");var dtiLabel=document.getElementById("dti-label");var magicline=document.getElementById("magicline");
    if(income<=0){answer.classList.remove("warn");eyebrow.textContent="Enter your income to start";big.textContent="—";lede.textContent="";
      s1v.textContent="—";s2v.textContent="—";dtiLabel.textContent="—";barU.style.width="0%";
      magicline.className="magicline idle";magicline.textContent="Fill in your yearly income above to see your number.";return;}
    var res=affordability(incomeMonthly,debts,r,n);
    if(res.housingBudget<=0||res.price<=0){answer.classList.add("warn");eyebrow.textContent="Let's clear a little room first";
      big.innerHTML="Your monthly debts use up the budget.";var target=incomeMonthly*TOTAL_DTI/100-incomeMonthly*0.10;
      var payDown=Math.max(0,debts-Math.max(0,target));
      lede.innerHTML="Paying down about <b>"+money(payDown)+"/mo</b> of those debts would unlock real buying power. You've got this.";
      s1k.textContent="Comfortable monthly payment";s1v.textContent="$0";s2k.textContent="Cash you'd put down";s2v.textContent=money(cash);
      dtiLabel.textContent="Over budget";barU.style.width="100%";barU.className="used red";magicline.className="magicline";
      magicline.innerHTML="Pay off <b>"+money(payDown)+"</b> of monthly debt and you could start affording a home — debt-free buyers have the most room.";
      if(animateMagic)bump("magiccard");return;}
    answer.classList.remove("warn");eyebrow.textContent="You could comfortably afford a home around";big.innerHTML=moneyK(res.price);
    var note;if(res.backCap<res.frontCap){note="Your monthly debts hold this back a little — without them you'd qualify for more.";}
    else{note="This keeps your housing under ~"+FRONT_DTI+"% of income — the comfortable zone.";}
    lede.innerHTML=note;
    s1k.textContent="Comfortable monthly payment";s1v.innerHTML=money(res.housingBudget)+"<span class='per'>/mo</span>";
    s2k.textContent="Cash you'd put down ("+dp+"%)";s2v.textContent=money(res.down);
    var dtiPct=res.dtiPct;var widthPct=Math.min(100,(dtiPct/40)*100);barU.style.width=widthPct.toFixed(1)+"%";
    barU.className="used"+(dtiPct>36.5?" red":dtiPct>28.5?" amber":"");dtiLabel.textContent=Math.round(dtiPct)+"% of income";
    if(cash>0&&cash<res.down){lede.innerHTML=note+" <span style='color:#FFD9CF'>You'd need about "+money(res.down-cash)+" more saved for this down payment.</span>";}
    var extraDown=10000;var payDown=200;var debtGain=0;
    if(debts>0&&res.backCap<=res.frontCap){var after=affordability(incomeMonthly,Math.max(0,debts-payDown),r,n);debtGain=Math.max(0,after.price-res.price);}
    var downGain=extraDown;magicline.className="magicline";
    if(debtGain>downGain){magicline.innerHTML="Pay off just <b>"+money(payDown)+"/mo</b> of debt and you could afford a home about <b>"+moneyK(debtGain)+" nicer</b>.";}
    else{magicline.innerHTML="Add <b>"+money(extraDown)+"</b> to your down payment and you could buy about <b>"+moneyK(downGain)+" more home</b> — for the same monthly payment.";}
    if(animateMagic)bump("magiccard");}
  function bump(id){var el=document.getElementById(id);el.classList.remove("pop");void el.offsetWidth;el.classList.add("pop");}
  function formatThousands(el){var start=el.selectionStart;var before=el.value;var digits=before.replace(/[^0-9]/g,"");
    if(digits===""){el.value="";return;}var formatted=parseInt(digits,10).toLocaleString("en-US");el.value=formatted;
    var diff=formatted.length-before.length;var pos=Math.max(0,(start||formatted.length)+diff);try{el.setSelectionRange(pos,pos);}catch(e){}}
  ["income","debts","cash"].forEach(function(id){var el=document.getElementById(id);
    el.addEventListener("input",function(){formatThousands(el);compute(true);});});
  document.getElementById("rate").addEventListener("input",function(){compute();});
  compute();
</script>"""


def _rent_vs_buy_calc_body() -> str:
    return r"""
    <div class="card">
      <div class="field">
        <label for="rent">Your rent now <span class="hint">— per month</span></label>
        <div class="inputwrap"><span class="pre">$</span>
          <input id="rent" class="has-pre" type="text" inputmode="numeric" value="2,000" /></div>
      </div>
      <div class="field">
        <label for="price">Home you'd buy <span class="hint">— the price</span></label>
        <div class="inputwrap"><span class="pre">$</span>
          <input id="price" class="has-pre" type="text" inputmode="numeric" value="350,000" /></div>
      </div>
      <div class="field">
        <label for="down">Down payment
          <span class="miniseg" id="downseg">
            <button type="button" class="on" data-mode="amt" onclick="setDownMode('amt')">$</button>
            <button type="button" data-mode="pct" onclick="setDownMode('pct')">%</button>
          </span>
        </label>
        <div class="inputwrap"><span class="pre" id="down-pre">$</span>
          <span class="post" id="down-post" style="display:none">%</span>
          <input id="down" class="has-pre" type="text" inputmode="numeric" value="35,000" /></div>
        <p class="adv-note" id="down-note" style="margin:6px 0 0">That's 10% down.</p>
      </div>
      <div class="row2">
        <div class="field" style="margin-bottom:0"><label for="rate">Interest rate</label>
          <div class="inputwrap"><input id="rate" class="has-post" type="text" inputmode="decimal" value="6.5" /><span class="post">%</span></div></div>
        <div class="field" style="margin-bottom:0"><label for="years">Years you'll stay</label>
          <div class="inputwrap"><input id="years" class="has-post" type="text" inputmode="numeric" value="7" /><span class="post">yrs</span></div></div>
      </div>
    </div>
    <details class="adv">
      <summary>Fine-tune the assumptions <small>(optional)</small><span class="chev">⌄</span></summary>
      <div class="adv-body">
        <p class="adv-note">Good defaults are filled in. Change them only if you know your area's numbers.</p>
        <div class="row2">
          <div class="field"><label for="rentGrow">Rent goes up</label>
            <div class="inputwrap"><input id="rentGrow" class="has-post" type="text" inputmode="decimal" value="3" /><span class="post">%/yr</span></div></div>
          <div class="field"><label for="appr">Home value grows</label>
            <div class="inputwrap"><input id="appr" class="has-post" type="text" inputmode="decimal" value="3" /><span class="post">%/yr</span></div></div>
          <div class="field"><label for="tax">Property tax</label>
            <div class="inputwrap"><input id="tax" class="has-post" type="text" inputmode="decimal" value="1.1" /><span class="post">%/yr</span></div></div>
          <div class="field"><label for="ins">Insurance</label>
            <div class="inputwrap"><input id="ins" class="has-post" type="text" inputmode="decimal" value="0.5" /><span class="post">%/yr</span></div></div>
          <div class="field"><label for="upkeep">Upkeep</label>
            <div class="inputwrap"><input id="upkeep" class="has-post" type="text" inputmode="decimal" value="1" /><span class="post">%/yr</span></div></div>
          <div class="field"><label for="loanyears">Loan length</label>
            <div class="inputwrap"><input id="loanyears" class="has-post" type="text" inputmode="numeric" value="30" /><span class="post">yrs</span></div></div>
          <div class="field"><label for="buycost">Cost to buy</label>
            <div class="inputwrap"><input id="buycost" class="has-post" type="text" inputmode="decimal" value="3" /><span class="post">% of price</span></div></div>
          <div class="field"><label for="sellcost">Cost to sell</label>
            <div class="inputwrap"><input id="sellcost" class="has-post" type="text" inputmode="decimal" value="6" /><span class="post">% of value</span></div></div>
        </div>
      </div>
    </details>
    <div class="answer" id="answer">
      <div class="eyebrow" id="ans-eyebrow">Over your time in the home</div>
      <div class="big" id="ans-big">—</div>
      <div class="lede" id="ans-lede"></div>
    </div>
    <div class="breakeven" id="breakeven">
      <span class="ico" id="be-ico">4</span>
      <div id="be-text">Buying pulls ahead after about <b>year 4</b>.</div>
    </div>
    <div class="stats">
      <div class="stat"><div class="k">Renting costs you</div><div class="v tnum" id="s1-v">—</div></div>
      <div class="stat muted-stat"><div class="k">Owning truly costs you</div><div class="v tnum" id="s2-v">—</div></div>
    </div>
    <div class="card chartcard">
      <div class="barlabels"><h3>Rent vs buy over time</h3><span id="chart-cap">true cost so far, each year</span></div>
      <div class="chart" id="chart"></div>
      <div class="legend"><span><i class="dot rent"></i> Renting</span><span><i class="dot buy"></i> Buying</span><span><i class="dot be"></i> Break-even</span></div>
    </div>
    <div class="magic" id="magic"><span class="spark">✨</span><p id="magic-text">—</p></div>
    <p class="disclaimer">A simple estimate using typical assumptions — your real numbers will vary. Not financial advice.</p>
<script>
  function num(id){var el=document.getElementById(id);if(!el)return 0;var raw=(el.value||"").replace(/[^0-9.]/g,"");var v=parseFloat(raw);return isFinite(v)?v:0;}
  function money(n){if(!isFinite(n))n=0;return "$"+Math.round(n).toLocaleString("en-US");}
  function roundNice(n){n=Math.abs(n);if(n>=100000)return Math.round(n/1000)*1000;if(n>=10000)return Math.round(n/500)*500;
    if(n>=1000)return Math.round(n/100)*100;return Math.round(n/50)*50;}
  var downMode="amt";
  function setDownMode(m){if(m===downMode)return;var price=num("price");var el=document.getElementById("down");var cur=num("down");
    if(m==="pct"){var pct=price>0?(cur/price)*100:0;el.value=(Math.round(pct*10)/10).toString();}
    else{var amt=price*(cur/100);el.value=Math.round(amt).toLocaleString("en-US");}
    downMode=m;document.querySelectorAll("#downseg button").forEach(function(b){b.classList.toggle("on",b.dataset.mode===m);});
    document.getElementById("down-pre").style.display=(m==="amt")?"":"none";document.getElementById("down-post").style.display=(m==="pct")?"":"none";
    el.classList.toggle("has-pre",m==="amt");el.classList.toggle("has-post",m==="pct");compute();}
  function downPayment(){var price=num("price");if(downMode==="pct")return price*(num("down")/100);return num("down");}
  function monthlyPI(loan,annualRate,years){if(loan<=0)return 0;var r=annualRate/100/12;var n=Math.round(years*12);
    if(n<=0)return 0;if(r===0)return loan/n;return loan*r/(1-Math.pow(1+r,-n));}
  function balanceAfter(loan,annualRate,years,m){if(loan<=0)return 0;var r=annualRate/100/12;var n=Math.round(years*12);
    if(m>=n)return 0;if(r===0)return Math.max(0,loan*(1-m/n));var pay=monthlyPI(loan,annualRate,years);
    var bal=loan*Math.pow(1+r,m)-pay*(Math.pow(1+r,m)-1)/r;return Math.max(0,bal);}
  function compute(animate){
    var rent0=num("rent");var price=num("price");var down=Math.min(downPayment(),price);var loan=Math.max(0,price-down);
    var rate=num("rate");var stay=Math.max(1,Math.round(num("years")));
    var rentGrow=num("rentGrow")/100;var appr=num("appr")/100;var taxPct=num("tax")/100;var insPct=num("ins")/100;
    var upkeepPct=num("upkeep")/100;var loanYears=Math.max(1,num("loanyears"));var buyCost=num("buycost")/100;var sellCost=num("sellcost")/100;
    var dnote=document.getElementById("down-note");
    if(price>0){var pct=(down/price)*100;dnote.textContent="That's "+(Math.round(pct*10)/10)+"% down"+(downMode==="pct"?" ("+money(down)+").":".");}else{dnote.textContent="";}
    var answer=document.getElementById("answer");var eyebrow=document.getElementById("ans-eyebrow");
    var big=document.getElementById("ans-big");var lede=document.getElementById("ans-lede");
    if(price<=0||rent0<=0){answer.classList.remove("warn");eyebrow.textContent="Fill in rent and a home price";big.textContent="—";lede.textContent="";
      document.getElementById("s1-v").textContent="—";document.getElementById("s2-v").textContent="—";drawChart([],[],0,0);setBreakeven(null,0);setMagic(null);return;}
    var pi=monthlyPI(loan,rate,loanYears);var HORIZON=Math.max(stay,30);var rentCum=[0];var buyCum=[0];var buyNet=[0];
    var rentSpent=0;var buySpent=down+price*buyCost;
    for(var y=1;y<=HORIZON;y++){var rentThisYear=rent0*12*Math.pow(1+rentGrow,y-1);rentSpent+=rentThisYear;rentCum[y]=rentSpent;
      var homeVal=price*Math.pow(1+appr,y-1);var piYear=pi*12;var taxYear=homeVal*taxPct;var insYear=homeVal*insPct;var upYear=homeVal*upkeepPct;
      buySpent+=piYear+taxYear+insYear+upYear;buyCum[y]=buySpent;
      var valEnd=price*Math.pow(1+appr,y);var balEnd=balanceAfter(loan,rate,loanYears,y*12);var equity=valEnd*(1-sellCost)-balEnd;
      buyNet[y]=buySpent-equity;}
    var beYear=null;for(var y2=1;y2<=HORIZON;y2++){if(buyNet[y2]<=rentCum[y2]){beYear=y2;break;}}
    var rentAtStay=rentCum[stay];var buyAtStay=buyNet[stay];var gap=rentAtStay-buyAtStay;
    document.getElementById("s1-v").textContent=money(rentAtStay);document.getElementById("s2-v").textContent=money(buyAtStay);
    var buyingAhead=gap>0;
    if(buyingAhead){answer.classList.remove("warn");eyebrow.textContent="Over your "+stay+" years in the home";
      big.innerHTML="Buying could leave you about <b>"+money(roundNice(gap))+"</b> ahead of renting.";
      lede.innerHTML="Renting that whole time costs about <b>"+money(rentAtStay)+"</b>; owning truly costs about <b>"+money(buyAtStay)+"</b> once you sell and pocket your equity.";}
    else{answer.classList.add("warn");eyebrow.textContent="Over your "+stay+" years in the home";
      big.innerHTML="Renting likely leaves you about <b>"+money(roundNice(-gap))+"</b> ahead.";
      if(beYear&&beYear>stay){lede.innerHTML="You'd need to stay until about <b>year "+beYear+"</b> for buying to pull ahead — longer than you plan to.";}
      else{lede.innerHTML="At these numbers, buying doesn't catch up within a normal holding period. Renting is the smarter money here.";}}
    setBreakeven(beYear,stay);setMagic({beYear:beYear,stay:stay,buyNet:buyNet,rentCum:rentCum,gap:gap,buyingAhead:buyingAhead},animate);
    drawChart(rentCum,buyNet,stay,beYear);}
  function setBreakeven(beYear,stay){var box=document.getElementById("breakeven");var ico=document.getElementById("be-ico");var text=document.getElementById("be-text");
    box.classList.remove("amber","red");
    if(beYear==null){box.classList.add("red");ico.textContent="∞";text.innerHTML="Buying doesn't pull ahead within 30 years at these numbers — <b>renting wins</b>.";return;}
    ico.textContent=beYear;
    if(beYear<=stay){text.innerHTML="Buying pulls ahead after about <b>year "+beYear+"</b> — every year after that, you're further ahead.";}
    else{box.classList.add("amber");text.innerHTML="Buying only pulls ahead after about <b>year "+beYear+"</b> — that's after you plan to move.";}}
  function setMagic(d,animate){var box=document.getElementById("magic");var text=document.getElementById("magic-text");
    if(!d){box.classList.add("idle");text.textContent="Enter your numbers above to see your rent-vs-buy turning point.";return;}
    var beYear=d.beYear,stay=d.stay,buyNet=d.buyNet,rentCum=d.rentCum,gap=d.gap,buyingAhead=d.buyingAhead;
    if(!buyingAhead){box.classList.add("idle");
      if(stay<=3&&beYear&&beYear>stay){text.innerHTML="If you'll move within ~"+stay+" years, renting is likely the smarter money.";}
      else if(beYear&&beYear>stay){text.innerHTML="Stay until about <b>year "+beYear+"</b> and buying starts to win — short of that, keep renting.";}
      else{text.innerHTML="Renting is the smarter money at these numbers.";}return;}
    box.classList.remove("idle");var extra=2;var future=Math.min(stay+extra,buyNet.length-1);
    var gapNow=rentCum[stay]-buyNet[stay];var gapLater=rentCum[future]-buyNet[future];var moreAhead=gapLater-gapNow;
    if(future>stay&&moreAhead>0){var yrsMore=future-stay;
      text.innerHTML="Stay just <b>"+yrsMore+" more year"+(yrsMore===1?"":"s")+"</b> and buying pulls about <b>"+money(roundNice(moreAhead))+"</b> further ahead.";}
    else{text.innerHTML="The longer you stay, the further buying pulls ahead.";}
    if(animate){box.classList.remove("pop");void box.offsetWidth;box.classList.add("pop");}}
  function drawChart(rentCum,buyNet,stay,beYear){var host=document.getElementById("chart");
    var W=520,H=200,padL=8,padR=8,padT=14,padB=26;
    if(!rentCum.length){host.innerHTML='<svg viewBox="0 0 '+W+' '+H+'" preserveAspectRatio="none"></svg>';return;}
    var lastYr=Math.min(Math.max(stay,beYear||stay)+1,rentCum.length-1);var years=lastYr;
    var xs=function(y){return padL+(y/years)*(W-padL-padR);};
    var maxV=0;for(var y=1;y<=years;y++){maxV=Math.max(maxV,rentCum[y],buyNet[y]);}
    var minV=0;for(var y3=1;y3<=years;y3++){minV=Math.min(minV,buyNet[y3]);}
    var span=(maxV-minV)||1;var ys=function(v){return padT+(1-(v-minV)/span)*(H-padT-padB);};
    function path(arr){var d="";for(var y4=0;y4<=years;y4++){d+=(y4===0?"M":"L")+xs(y4).toFixed(1)+" "+ys(arr[y4]).toFixed(1)+" ";}return d.trim();}
    var zeroY=ys(0);var rentPath=path(rentCum);var buyPath=path(buyNet);var beMark="";
    if(beYear&&beYear<=years){var bx=xs(beYear);
      beMark='<line x1="'+bx.toFixed(1)+'" y1="'+padT+'" x2="'+bx.toFixed(1)+'" y2="'+(H-padB)+'" stroke="#1E1A16" stroke-width="1.5" stroke-dasharray="4 4" opacity=".45"/>'
        +'<circle cx="'+bx.toFixed(1)+'" cy="'+ys(buyNet[beYear]).toFixed(1)+'" r="4.5" fill="#1E1A16"/>'
        +'<text x="'+bx.toFixed(1)+'" y="'+(H-padB+18)+'" text-anchor="middle" font-size="11" fill="#6B635A" font-family="Inter,sans-serif">yr '+beYear+'</text>';}
    var stayMark="";if(stay<=years){var sx=xs(stay);
      stayMark='<circle cx="'+sx.toFixed(1)+'" cy="'+ys(rentCum[stay]).toFixed(1)+'" r="3.5" fill="#C0392B"/>'
        +'<circle cx="'+sx.toFixed(1)+'" cy="'+ys(buyNet[stay]).toFixed(1)+'" r="3.5" fill="#1A8F5A"/>';}
    host.innerHTML='<svg viewBox="0 0 '+W+' '+H+'" preserveAspectRatio="none" role="img" aria-label="Rent versus buy cumulative cost over time">'
      +'<line x1="'+padL+'" y1="'+zeroY.toFixed(1)+'" x2="'+(W-padR)+'" y2="'+zeroY.toFixed(1)+'" stroke="#EBE3D2" stroke-width="1"/>'
      +beMark+'<path d="'+rentPath+'" fill="none" stroke="#C0392B" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>'
      +'<path d="'+buyPath+'" fill="none" stroke="#1A8F5A" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>'+stayMark+'</svg>';}
  function formatThousands(el){var start=el.selectionStart;var before=el.value;var digits=before.replace(/[^0-9]/g,"");
    if(digits===""){el.value="";return;}var formatted=parseInt(digits,10).toLocaleString("en-US");el.value=formatted;
    var diff=formatted.length-before.length;var pos=Math.max(0,(start||formatted.length)+diff);try{el.setSelectionRange(pos,pos);}catch(e){}}
  ["rent","price"].forEach(function(id){var el=document.getElementById(id);el.addEventListener("input",function(){formatThousands(el);compute(true);});});
  document.getElementById("down").addEventListener("input",function(){var el=document.getElementById("down");if(downMode==="amt")formatThousands(el);compute(true);});
  ["rate","years","rentGrow","appr","tax","ins","upkeep","loanyears","buycost","sellcost"].forEach(function(id){
    var el=document.getElementById(id);if(el)el.addEventListener("input",function(){compute(true);});});
  compute();
</script>"""


def _cash_to_close_calc_body() -> str:
    return r"""
    <div class="card">
      <div class="field">
        <label for="price">Home price</label>
        <div class="inputwrap"><span class="pre">$</span>
          <input id="price" class="has-pre" type="text" inputmode="numeric" value="350,000" /></div>
      </div>
      <div class="field">
        <label>Down payment <span class="hint">— enter a % or a dollar amount</span></label>
        <div class="dp-row">
          <div class="field"><div class="inputwrap"><input id="dpPct" class="has-post" type="text" inputmode="decimal" value="10" /><span class="post">%</span></div></div>
          <div class="field"><div class="inputwrap"><span class="pre">$</span><input id="dpAmt" class="has-pre" type="text" inputmode="numeric" value="35,000" /></div></div>
        </div>
        <div class="chips" id="chips">
          <button class="chip" data-pct="3.5" type="button">3.5% <small>FHA</small></button>
          <button class="chip" data-pct="5" type="button">5%</button>
          <button class="chip on" data-pct="10" type="button">10%</button>
          <button class="chip" data-pct="20" type="button">20% <small>no PMI</small></button>
        </div>
      </div>
      <div class="field">
        <label for="rate">Interest rate <span class="hint">— for the monthly estimate</span></label>
        <div class="inputwrap"><input id="rate" class="has-post" type="text" inputmode="decimal" value="6.6" /><span class="post">%</span></div>
      </div>
      <div class="field">
        <label for="reserves">Months of reserves <span class="hint">— a cushion you keep, optional</span></label>
        <select id="reserves">
          <option value="0" selected>None — just the cash to close</option>
          <option value="2">2 months</option><option value="3">3 months</option><option value="6">6 months</option>
        </select>
      </div>
    </div>
    <div class="answer" id="answer">
      <div class="eyebrow">Cash to get the keys</div>
      <div class="lede-top">You'd need about</div>
      <div class="big tnum" id="ans-big">—</div>
      <div class="lede" id="ans-lede"></div>
    </div>
    <div class="card">
      <h3><svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v10M9.5 9.5a2.5 2 0 0 1 5 0c0 2.5-5 1.5-5 4a2.5 2 0 0 0 5 0"/></svg>Cash you'd need up front</h3>
      <p class="sub">The money that actually leaves your account to buy this home.</p>
      <div class="cash-grid">
        <div class="cash"><div class="lbl">Down payment <small id="dp-card-pct">(10%)</small></div>
          <div class="val tnum" id="dp-card-val">—</div><div class="note">The chunk you put toward the price.</div></div>
        <div class="cash"><div class="lbl">Closing costs</div>
          <div class="val tnum" id="cc-card-val">—</div><div class="note">Lender, title &amp; signing fees (~3.5%).</div></div>
      </div>
      <div class="cash-total"><span>Total cash to get the keys</span><span class="v tnum" id="total-card-val">—</span></div>
      <div class="reserves" id="reserves-row" style="display:none">
        <span class="ic">🛟</span>
        <div class="rt"><b>+ <span class="amt tnum" id="res-val">$0</span> reserves <span style="font-weight:500;color:var(--muted)">(nice to have)</span></b>
          <span id="res-note">A cushion lenders like you to keep after closing. You don't spend it — so it's not part of the cash to get the keys.</span></div>
      </div>
    </div>
    <div class="magic col" id="magic">
      <div class="toprow"><span class="spark">✨</span><h3>The trade-off, honestly</h3></div>
      <p id="magic-line">—</p>
      <p class="tag">An estimate — the monthly difference is just the loan part, at the rate above.</p>
    </div>
    <p class="disclaimer">An estimate to help you plan — closing costs vary by state and lender.<br/>
      Not a loan offer. Reserves are money you keep, not spend.</p>
<script>
  var CLOSING_PCT=3.5;var TERM_YEARS=30;var COMPARE_LOW=3.5;var COMPARE_HIGH=20;
  function num(id){var raw=(document.getElementById(id).value||"").replace(/[^0-9.]/g,"");var v=parseFloat(raw);return isFinite(v)?v:0;}
  function money(n){return "$"+Math.round(n).toLocaleString("en-US");}
  function pmt(principal,annualPct,years){var r=annualPct/100/12;var n=years*12;if(principal<=0)return 0;if(r===0)return principal/n;return principal*r/(1-Math.pow(1+r,-n));}
  var dpMode="pct";
  function syncDownPayment(){var price=num("price");
    if(dpMode==="pct"){var pct=num("dpPct");var amt=price*pct/100;document.getElementById("dpAmt").value=Math.round(amt).toLocaleString("en-US");return {pct:pct,amt:amt};}
    else{var amt2=num("dpAmt");var pct2=price>0?(amt2/price*100):0;document.getElementById("dpPct").value=(Math.round(pct2*10)/10).toString();return {pct:pct2,amt:amt2};}}
  function compute(){var price=num("price");var rate=num("rate");var months=parseInt(document.getElementById("reserves").value,10)||0;
    var dp=syncDownPayment();var dpPct=dp.pct,down=dp.amt;var closing=price*CLOSING_PCT/100;var totalToKeys=down+closing;
    var loan=Math.max(0,price-down);var monthly=pmt(loan,rate,TERM_YEARS);var reserves=months*monthly;
    document.querySelectorAll(".chip").forEach(function(c){c.classList.toggle("on",Math.abs(parseFloat(c.dataset.pct)-dpPct)<0.01);});
    document.getElementById("ans-big").textContent=money(totalToKeys);
    document.getElementById("ans-lede").innerHTML="to get the keys on a <b>"+money(price)+"</b> home with <b>"+(Math.round(dpPct*10)/10)+"%</b> down."
      +(months>0?" Plus a <b>"+money(reserves)+"</b> cushion to keep.":"");
    document.getElementById("dp-card-pct").textContent="("+(Math.round(dpPct*10)/10)+"%)";
    document.getElementById("dp-card-val").textContent=money(down);document.getElementById("cc-card-val").textContent=money(closing);
    document.getElementById("total-card-val").textContent=money(totalToKeys);
    var resRow=document.getElementById("reserves-row");
    if(months>0&&reserves>0){resRow.style.display="flex";document.getElementById("res-val").textContent=money(reserves);
      document.getElementById("res-note").textContent=months+" months of the loan payment ("+money(monthly)+"/mo) — a cushion lenders like you to keep after closing. You don't spend it, so it's not part of the cash to get the keys.";}
    else{resRow.style.display="none";}renderMagic(price,rate);}
  function renderMagic(price,rate){var el=document.getElementById("magic-line");
    if(price<=0){el.textContent="Enter a home price to see the trade-off.";return;}
    var lowDown=price*COMPARE_LOW/100;var highDown=price*COMPARE_HIGH/100;var cashLess=highDown-lowDown;
    var lowLoan=price-lowDown;var highLoan=price-highDown;var moreMonthly=pmt(lowLoan,rate,TERM_YEARS)-pmt(highLoan,rate,TERM_YEARS);
    el.innerHTML="Put <b>"+COMPARE_LOW+"%</b> down instead of <b>"+COMPARE_HIGH+"%</b> and you'd need about "
      +"<b class='less'>"+money(cashLess)+" less</b> cash up front — but pay roughly <b class='more'>"+money(moreMonthly)+" more</b> a month on the loan.";}
  function formatThousands(el){var start=el.selectionStart;var before=el.value;var digits=before.replace(/[^0-9]/g,"");
    if(digits===""){el.value="";return;}var formatted=parseInt(digits,10).toLocaleString("en-US");el.value=formatted;
    var diff=formatted.length-before.length;var pos=Math.max(0,(start||formatted.length)+diff);try{el.setSelectionRange(pos,pos);}catch(e){}}
  ["price","dpAmt"].forEach(function(id){var el=document.getElementById(id);
    el.addEventListener("input",function(){if(id==="dpAmt")dpMode="amt";formatThousands(el);compute();});});
  document.getElementById("dpPct").addEventListener("input",function(){dpMode="pct";compute();});
  ["rate","reserves"].forEach(function(id){document.getElementById(id).addEventListener("input",function(){compute();});});
  document.getElementById("reserves").addEventListener("change",function(){compute();});
  document.querySelectorAll(".chip").forEach(function(c){c.addEventListener("click",function(){dpMode="pct";document.getElementById("dpPct").value=c.dataset.pct;compute();});});
  compute();
</script>"""


# Calculator registry — (filename, nav-key, builder, H1, SEO intro, <title>, meta).
CALCULATORS = [
    {
        "file": "home-affordability-calculator.html",
        "icon": "up",
        "card_title": "How much house can I afford?",
        "card_desc": "Income, cash and debts → a calm green, amber or red number.",
        "h1": "How much house can I <em>afford?</em>",
        "intro": "A free home affordability calculator that turns your income, debts and "
                 "down-payment cash into one plain-English number — the home price you can "
                 "comfortably afford.",
        "title": "Home Affordability Calculator — how much house can I afford? | Underlisted",
        "meta": "Free home affordability calculator. Enter your income, monthly debts and down "
                "payment to see how much house you can comfortably afford, in plain English.",
        "body": _afford_calc_body,
    },
    {
        "file": "cash-to-close-calculator.html",
        "icon": "coin",
        "card_title": "Cash to the keys",
        "card_desc": "Down payment plus closing — the real money you'd need.",
        "h1": "How much cash do I need to <em>buy?</em>",
        "intro": "A free cash-to-close calculator: down payment plus closing costs, so you "
                 "know the real cash you'd need in the bank to get the keys.",
        "title": "Cash to Close Calculator — how much cash to buy a house | Underlisted",
        "meta": "Free cash to close calculator. See the real cash you need to buy a home — "
                "down payment plus closing costs — with an optional reserves cushion.",
        "body": _cash_to_close_calc_body,
    },
    {
        "file": "rent-vs-buy-calculator.html",
        "icon": "bank",
        "card_title": "Rent vs buy",
        "card_desc": "Which one really wins for you — and the year buying pulls ahead.",
        "h1": "Should I keep renting, or <em>buy?</em>",
        "intro": "A free rent vs buy calculator that shows which one leaves more money in "
                 "your pocket over the years you'll stay — and the year buying pulls ahead.",
        "title": "Rent vs Buy Calculator — should I rent or buy a house? | Underlisted",
        "meta": "Free rent vs buy calculator. Compare the true cost of renting versus buying "
                "over the years you'll stay, and find the break-even year buying pulls ahead.",
        "body": _rent_vs_buy_calc_body,
    },
    {
        "file": "mortgage-payoff-calculator.html",
        "icon": "cal",
        "card_title": "Payoff time",
        "card_desc": "How fast a little extra each month clears the loan.",
        "h1": "How fast will I <em>own my home?</em>",
        "intro": "A free mortgage payoff calculator: see when your loan is gone — and how "
                 "much sooner (and how much interest saved) a little extra each month would do.",
        "title": "Mortgage Payoff Calculator — pay off your mortgage early | Underlisted",
        "meta": "Free mortgage payoff calculator. See when your mortgage is paid off and how "
                "much time and interest you'd save by adding a little extra each month.",
        "body": _payoff_calc_body,
    },
]


def free_tools_hub_page() -> str:
    # map each calculator's line-icon name to its illustrated raster counterpart
    # (the nano-banana gold-ringed set) so the hub wears the same premium art as
    # the homepage tool grid. Falls back to the SVG if no illustration exists.
    HUB_ILLUS = {"up": "afford", "coin": "cash", "bank": "cost", "cal": "calc"}
    cards = []
    for c in CALCULATORS:
        illus = HUB_ILLUS.get(c["icon"])
        ico = (f"<span class='ico illus'>{icon_img(illus, c['card_title'])}</span>"
               if illus else f"<span class='ico'>{svg(c['icon'], w=26)}</span>")
        cards.append(
            f"<a class='hub-card reveal' href='{c['file']}'>"
            f"<span class='hub-badge'>{free_badge()}</span>"
            f"{ico}"
            f"<h3>{c['card_title']}</h3>"
            f"<p>{c['card_desc']}</p>"
            f"<span class='go'>Open the calculator {svg('arrow', w=16)}</span>"
            "</a>"
        )
    body = (
        "<section class='masthead' style='padding-bottom:0'><div class='wrap'>"
        "<div class='pagehero reveal in'>"
        "<div class='kicker'>Free · no signup · plain English</div>"
        "<h1>Free home-buying <em>calculators.</em></h1>"
        "<p>Run the numbers before you fall in love with a house. Four plain-English tools — "
        f"no math homework, no spreadsheet, no signup. {free_badge(big=True)}</p>"
        "</div></div></section>"
        "<section class='sec' style='padding-top:34px'><div class='wrap'>"
        f"<div class='hub-grid'>{''.join(cards)}</div>"
        "</div></section>"
        + WAITLIST
    )
    return shell(
        "Free home-buying calculators | Underlisted",
        "Four free, plain-English home-buying calculators: how much house you can afford, "
        "cash to close, rent vs buy, and mortgage payoff. No signup.",
        body, here="tools", extra_head=CALC_CSS,
    )


# ──────────────────────────────────────────────────────────────────────────────
# THE 7 "SEE HOW IT WORKS" DEEP-DIVES — one indexable page per galaxy feature.
#
# WHY one page per feature (not one anchored mega-page): each deep-dive targets a
# DISTINCT buyer search ("how does the deal score work", "fire & flood risk on a
# home", "how much cash to buy a house"). Distinct URLs each with their own
# <title>/meta rank far better than seven anchors sharing one page. Quill already
# wrote a separate SEO title + meta for each of the seven — that maps 1:1 to a page.
#
# Copy is adapted from content/FEATURE_DEEPDIVES.html (Quill) — same honest,
# no-overpromise claims, reshaped into the Ivory & Gold section rhythm.
#
# Each dict: file, title, meta, kicker, h1 (with <em> accent), lede, then a list
# of "how we work it out" paragraphs, an optional worked example, named sources,
# a trust close, an honest caveat, and cross-links. NO waitlist form / Payhip.
# ──────────────────────────────────────────────────────────────────────────────
DEEPDIVES = [
    dict(
        file="how-deal-score-works.html",
        title="How the Underlisted Deal Score Works (0–100, Explained Simply) | Underlisted",
        meta="See exactly how Underlisted scores a home from 0 to 100 — value discount, "
             "rent yield, days on market and fire/flood risk, weighted and fully transparent. "
             "Honest, no jargon.",
        kicker="Feature · The Deal Score",
        h1="The Deal Score isn't a guess — it's four honest <em>checks</em>, weighted",
        lede="One number from <b>0 to 100</b>. When you see a green 82, it's not a vibe — "
             "here's exactly how it's built.",
        what="When you see a green “82,” it's not a mood. Behind it we run a home through four "
             "checks and add up the points. The biggest check by far is the one that matters most "
             "to a buyer: <b>how far below its estimated value is this home actually listed?</b>",
        how=[
            "We compare the asking price to an estimated market value (an <em>AVM</em> — an "
            "automated value estimate). If a second independent estimate is available, we "
            "<b>average the two</b>, because two estimates that agree are more trustworthy than "
            "one. Listed well under value earns the most points.",
            "Then we add three smaller checks: <b>rent yield</b> (would the yearly rent cover a "
            "healthy share of the price?), <b>days on market</b> (a home sitting a long time gives "
            "you more room to negotiate), and <b>risk</b> (fire/flood lowers the score a little). "
            "Roughly, value counts for about half the score, rent yield about a third, and the "
            "last two are smaller signals.",
            "The honest part: if a piece of data isn't loaded yet — say we don't have a rent "
            "estimate for a home — we <b>don't fake it</b>. We drop that check and re-balance the "
            "score over the checks we do have, and the breakdown tells you so. And if a home has "
            "no price and no value at all (common for a brand-new foreclosure), we show "
            "“awaiting a value estimate” instead of a fake 100.",
        ],
        scorekey=True,
        sources=["Estimated value (AVM)", "Rent estimate", "Days on market",
                 "FEMA fire & flood risk"],
        trust="Every score opens into a plain breakdown that shows which checks counted, how many "
              "points each earned, and which were skipped for missing data. Nothing is hidden — "
              "and we never use anything about the people in an area. Only the home's price, value, "
              "rent, time on market and natural-hazard risk.",
        caveat="The Deal Score is a fast screening tool, not an appraisal. It points you at homes "
               "worth a closer look — it doesn't replace your own walkthrough, an inspection, or a "
               "real appraisal before you buy.",
        more=[("how-insurance-risk-works.html", "How we check fire & flood risk"),
              ("how-true-monthly-cost-works.html", "The true monthly cost"),
              ("learn.html", "Learn the basics")],
    ),
    dict(
        file="how-insurance-risk-works.html",
        title="Fire & Flood Risk on a Home — How We Check It (Free FEMA Data) | Underlisted",
        meta="Underlisted warns you if a home sits in a FEMA flood or wildfire zone before you "
             "fall in love with it — using free official FEMA maps and the National Risk Index. "
             "Here's how.",
        kicker="Feature · Fire & flood risk",
        h1="The fire &amp; flood warning comes straight from the <em>U.S. government</em>",
        lede="A “cheap” home in a flood zone isn't cheap. <b>We check before you fall in love</b> "
             "— using free official FEMA data.",
        what="Most home sites show you the price, the photos, the comps — and stay silent about "
             "whether the home sits in a wildfire or flood zone where insurance is costly, or "
             "sometimes hard to get at all. That silence can wreck the real monthly cost. We check "
             "it for you.",
        how=[
            "For each home's exact location, we ask <b>FEMA's flood maps</b> whether it falls in a "
            "designated flood zone (the kind where flood insurance is usually required), and we "
            "ask <b>FEMA's National Risk Index</b> for its wildfire and earthquake risk rating.",
            "Sometimes the precise point-level reading comes back empty (rural gaps, an odd "
            "coordinate, or the service is briefly down). So we built a safety net: a one-time "
            "download of FEMA's official <b>county-level</b> risk table that fills any blank — so "
            "the warning is never silently empty. We always prefer the more precise reading and "
            "only fall back to the county rating when we have to.",
            "This risk reading does two jobs: it shows you a plain warning (<em>“In a FEMA flood "
            "zone — flood insurance is likely required”</em>), and it quietly nudges the "
            "home-insurance estimate higher in the true-monthly-cost panel, so the extra cost "
            "shows up in real dollars.",
        ],
        sources=["FEMA flood maps (National Flood Hazard Layer)",
                 "FEMA National Risk Index — wildfire", "FEMA county risk table (backup)"],
        trust="It's the same public FEMA data your lender and insurer use — not our opinion. And "
              "it's strictly a natural-hazard signal. We never use it to judge a neighbourhood or "
              "the people in it.",
        caveat="FEMA maps are accurate to an area, not a perfect prediction for one address. Always "
               "get a real insurance quote for the specific home before you commit — that quote is "
               "the final word on cost.",
        more=[("how-true-monthly-cost-works.html", "How risk becomes real dollars"),
              ("how-deal-score-works.html", "The Deal Score"),
              ("learn.html#insurance-risk", "Learn the basics")],
    ),
    dict(
        file="how-true-monthly-cost-works.html",
        title="The True Monthly Cost of a Home — Beyond the Loan Payment | Underlisted",
        meta="Underlisted shows the real monthly cost of a home — loan, property tax, insurance, "
             "PMI, HOA and upkeep — as honest ranges, so the bills don't surprise you. See how "
             "it's built.",
        kicker="Feature · True monthly cost",
        h1="The true monthly cost adds back everything other sites <em>hide</em>",
        lede="Not just the loan payment — <b>the number you actually pay</b> once the real bills "
             "arrive.",
        what="Most sites show you the loan payment and stop. Then the real bills arrive. We add "
             "back the costs first-time buyers forget, and we show each one as an honest low–high "
             "range instead of a fake exact number.",
        how=[
            "Starting from the price, we build the monthly cost from its real parts: "
            "<b>principal + interest</b> on the loan, <b>property tax</b>, <b>home insurance</b>, "
            "<b>PMI</b> (only if your down payment is under 20%), <b>HOA dues</b> (if any), and a "
            "line for <b>upkeep &amp; repairs</b>. We separate what a lender counts as your “house "
            "payment” from the all-in cost of actually living there, so you see both.",
            "Because tax and insurance genuinely vary a lot, we show ranges, not false precision — "
            "and we label why. Property tax swings by county; insurance climbs when FEMA flags fire "
            "or flood risk on that home (so the warning turns into real dollars here). PMI only "
            "appears when it actually applies, with a plain note that it usually drops off once you "
            "reach 20% equity.",
        ],
        eg="<b>Example:</b> the loan alone is $1,500/mo — but with tax, insurance, PMI and the "
           "rest, the real number is closer to <b>$2,050/mo</b>. We show you the $2,050.",
        sources=["Live 30-year mortgage rate (Freddie Mac)", "FEMA risk (insurance bump)",
                 "Standard tax / insurance / PMI assumptions"],
        trust="It's plain arithmetic on the price and standard assumptions you can see — no hidden "
              "formula, and zero data fetched while you browse. We'd rather show an honest range "
              "than a precise-looking number that's quietly wrong.",
        caveat="These are estimates to help you budget, not a quote. Your exact tax bill, insurance "
               "premium and HOA come from the county, an insurer and the listing — confirm them "
               "before you buy.",
        more=[("how-cash-to-keys-works.html", "The real cash to the keys"),
              ("home-affordability-calculator.html", "Can I afford it? (free)"),
              ("free-tools.html", "All free calculators")],
    ),
    dict(
        file="how-cash-to-keys-works.html",
        title="How Much Cash Do You Really Need to Buy a House? | Underlisted",
        meta="Underlisted shows the real cash to the keys — down payment plus closing costs, with "
             "reserves separated — using today's live mortgage rate. One clear number, then the "
             "breakdown.",
        kicker="Feature · Real cash to the keys",
        h1="The real cash to the keys — one clear <em>number</em>, then the breakdown",
        lede="The cash that actually has to leave your account <b>before you move in</b>.",
        what="“How much do I need saved?” is the question that stops most first-time buyers. We "
             "answer it with one headline number, then show the friendly breakdown so nothing is a "
             "mystery.",
        how=[
            "From the price and your loan type, we work out your <b>down payment</b> (as low as 3% "
            "on a conventional loan, 3.5% FHA, 0% for eligible VA), then add <b>closing costs</b> "
            "(title, escrow, appraisal and lender fees) shown as a range. Those two together are "
            "your <b>cash to close</b> — the money that leaves your account.",
            "We keep <b>reserves</b> (money the lender wants you to still have in the bank "
            "afterward) shown <b>separately</b>, so a “live-in” buyer isn't scared by a number "
            "meant mainly for investors. The monthly loan payment uses the <b>live 30-year "
            "mortgage rate</b> from Freddie Mac's free weekly feed, nudged up a little for lower "
            "credit bands — so the math reflects today's market, not a stale number.",
        ],
        eg="<b>Example:</b> on a $300,000 home with 10% down, that's $30,000 down plus a few "
           "thousand in closing costs — <b>roughly $35,000 in hand</b> to get the keys.",
        sources=["Live 30-year mortgage rate (Freddie Mac)",
                 "Standard down-payment & closing-cost ranges"],
        trust="It's transparent arithmetic — down payment plus closing costs, with reserves shown "
              "on their own line. We never bury reserves in the headline to make the number look "
              "scarier, and we never hide closing costs to make it look smaller.",
        caveat="This is an estimate, not a loan offer. Your actual down payment, rate and closing "
               "costs come from a real lender — use this to plan, then get a quote.",
        more=[("cash-to-close-calculator.html", "Try the cash-to-close calculator (free)"),
              ("how-true-monthly-cost-works.html", "The true monthly cost"),
              ("home-affordability-calculator.html", "Can I afford it?")],
    ),
    dict(
        file="how-afford-check-works.html",
        title="\"Can I Afford This House?\" — The 28/36 Rule, Made Simple | Underlisted",
        meta="Underlisted checks any home against your income, savings and debts using the lender "
             "28/36 rule, and tells you green, amber or red plus what you'd have left each month. "
             "Your numbers stay private.",
        kicker="Feature · Can I afford it?",
        h1="“Can I afford it?” uses the <em>same rule lenders use</em>",
        lede="You tell us your income, savings and debts. We answer <b>green, amber or red</b> — "
             "plus what you'd have left each month.",
        what="A home can be a great <b>deal</b> and still be wrong for <b>your</b> budget. This is "
             "the feature that answers the question a deal score can't: can <em>I</em> actually "
             "carry this one?",
        how=[
            "You enter your monthly income, cash on hand and other monthly debts. We compare your "
            "likely house payment to your income using the same yardstick lenders use — the "
            "<b>28/36 rule</b> (housing comfortably under about 28% of income; housing plus all "
            "debts under about 36%). Under comfortable = green. A stretch = amber. Over the line "
            "lenders usually allow = red.",
            "We judge against the <b>middle</b> of the cost range — never the rosy low end, never "
            "the scary high end. We also check whether your cash actually covers the cash-to-close, "
            "and if you're short, we say by how much and drop the verdict to at least amber. Then "
            "we tell you the human number: roughly how much you'd have <b>left over each month</b> "
            "after the house and your debts.",
            "One thing we take seriously: your income, savings and debts are used only to answer "
            "your question. The math runs and the numbers are gone — they aren't logged or printed "
            "to power this.",
        ],
        eg="<b>Example:</b> “Green — after the house payment and your other debts, you'd have "
           "roughly <b>$400–$900 left each month</b>.”",
        sources=["Standard lender 28/36 DTI guidance", "Your true monthly cost",
                 "Your cash-to-close"],
        trust="The 28/36 rule is the standard lenders apply, not a number we invented — and we "
              "judge against the honest midpoint, so the verdict is neither sugar-coated nor "
              "alarmist.",
        caveat="This is a budgeting guide, not a pre-approval. A real lender looks at your full "
               "credit and finances — get pre-approved before you make an offer.",
        more=[("home-affordability-calculator.html", "Try the affordability calculator (free)"),
              ("how-true-monthly-cost-works.html", "The true monthly cost"),
              ("how-cash-to-keys-works.html", "The real cash to the keys")],
    ),
    dict(
        file="how-foreclosures-work.html",
        title="Free Nationwide Foreclosure Listings (HUD & USDA Homes) | Underlisted",
        meta="Underlisted pulls real, free, government foreclosure listings nationwide — HUD FHA "
             "bank-owned homes plus USDA rural re-sales — into one simple feed. No price is ever "
             "invented. See how.",
        kicker="Feature · Foreclosures, nationwide",
        h1="Real foreclosures, nationwide — straight from <em>government feeds</em>",
        lede="Thousands of government-owned homes, <b>refreshed for free</b> — folded into the same "
             "scored feed as everything else.",
        what="Foreclosure data is usually locked behind pricey subscriptions. We start with the "
             "real, free, public source: homes the U.S. government itself took back and is "
             "re-selling.",
        how=[
            "When the FHA pays out on a defaulted loan, it takes the home back and re-sells it. "
            "<b>HUD</b> publishes that whole inventory as a free public feed — thousands of "
            "bank-owned homes across the country (over five thousand at last refresh). We pull the "
            "full list and fold it into the same feed as every other home.",
            "HUD's feed is mostly metro homes, so we add the <b>USDA</b> rural-development re-sale "
            "list — the same kind of government-owned homes, in the small towns HUD's list misses. "
            "Together they cover both city and country. Both are free, public, and legally licensed "
            "for this use — we don't scrape anyone's portal.",
            "The honest part: HUD's feed gives the address but no price, so we <b>never invent "
            "one</b>. The home flows into the feed marked “awaiting a value estimate,” and our "
            "cost-controlled value worker prices it later. You'll never see a made-up number on a "
            "foreclosure.",
        ],
        sources=["HUD FHA foreclosure feed (U.S. government)",
                 "USDA rural re-sale list (U.S. government)",
                 "Pre-foreclosure & auctions — planned add-on"],
        trust="These are official government re-sale listings, not a reseller's repackaged data. "
              "When a price isn't known yet, we say so plainly rather than guessing.",
        caveat="The USDA rural file is a periodic government snapshot, so treat it as a “refresh "
               "occasionally” bonus, not a live feed. Always confirm a foreclosure's current "
               "status and price with the listing before acting.",
        more=[("learn.html#what-is-reo", "What is an REO / bank-owned home?"),
              ("how-deal-score-works.html", "How we score every home"),
              ("learn.html", "Learn the basics")],
    ),
    dict(
        file="how-free-calculators-work.html",
        title="Free Home-Buying Calculators (No Signup) — Payoff, Affordability & More | Underlisted",
        meta="Free, no-signup calculators from Underlisted: loan payoff, affordability, "
             "rent-vs-buy and cash to close — pure math that runs instantly and agrees with the "
             "rest of the app.",
        kicker="Feature · Free calculators",
        h1="Free calculators — no signup, and they all <em>agree</em> with each other",
        lede="Pure math you can run on any number, instantly. Type a number, get an answer — "
             "<b>no account, nothing stored</b>.",
        what="Some sites lock the basic math behind a login. Ours are free and need no account. "
             "And because they share one engine, the numbers never contradict each other.",
        how=[
            "Each calculator is plain arithmetic that runs the moment you type — no data is "
            "fetched, nothing is billed, nothing is stored. The set covers the questions beginners "
            "actually ask: <b>loan payoff</b> (the real payment and how it shrinks over time), "
            "<b>affordability</b> (the 28/36 check), <b>rent vs. buy</b>, and <b>cash to close</b>.",
            "The important detail: the calculators reuse the very same cost engine that powers the "
            "true monthly cost and the afford check. So the closing costs in the calculator match "
            "the closing costs on a listing — there's <b>one source of truth</b>, not three "
            "slightly different answers.",
        ],
        sources=["Live 30-year mortgage rate (Freddie Mac)", "The shared Underlisted cost engine"],
        trust="It's transparent math, free, and consistent everywhere it appears. No login wall, "
              "no upsell to see your own numbers, and no surprise where two tools disagree.",
        caveat="Calculators give you a clear estimate to plan with — not a loan offer or financial "
               "advice. Confirm the real figures with a lender before you commit.",
        more=[("free-tools.html", "Open the free calculators"),
              ("how-true-monthly-cost-works.html", "The true monthly cost"),
              ("how-afford-check-works.html", "Can I afford it?")],
    ),
]


def deepdive_page(d: dict) -> str:
    """Render one 'See how it works' deep-dive page in Ivory & Gold. No waitlist
    form, no Payhip button — a pure trust/explainer page (Quill's honest copy)."""
    # "How we work it out" paragraphs
    how_paras = "".join(f"<p>{p}</p>" for p in d["how"])

    # optional score key (Deal Score page)
    scorekey = ""
    if d.get("scorekey"):
        scorekey = (
            "<div class='dd-scorekey'>"
            f"<span style='background:{GOOD}'>70–100 · Good deal</span>"
            f"<span style='background:{OKAY}'>45–69 · Okay, look closer</span>"
            f"<span style='background:{WEAK}'>0–44 · Weak</span>"
            "</div>"
        )

    # optional worked example
    eg = ""
    if d.get("eg"):
        eg = f"<div class='dd-eg'><span class='tag'>Worked example</span>{d['eg']}</div>"

    # named data sources
    src_chips = "".join(
        f"<span class='chip'>{svg('check', w=14)}{s}</span>" for s in d["sources"]
    )

    # cross-links
    more_links = (f"<span class='sep'>·</span>".join(
        f"<a href='{href}'>{label}</a>" for href, label in d["more"]
    ))

    body = (
        # back nav (consistent with .pagelinks idiom)
        "<div class='wrap'><p class='dd-back'>"
        f"<a href='index.html'>← Back to deals</a><span class='sep'>·</span>"
        "<a href='index.html#galaxy-title'>All features</a>"
        "</p></div>"
        # hero
        "<section class='masthead' style='padding:14px 0 0'><div class='wrap'>"
        "<div class='dd-hero reveal in'>"
        f"<div class='kicker'><span class='dot'></span>{d['kicker']}</div>"
        f"<h1>{d['h1']}</h1>"
        f"<p class='lede'>{d['lede']}</p>"
        "</div></div></section>"
        # body
        "<section class='sec' style='padding:24px 0 60px'><div class='wrap'>"
        "<div class='dd'>"
        # what it is
        "<div class='dd-block'>"
        "<div class='dd-eyebrow'><span class='n'>01</span> What it is</div>"
        f"<p>{d['what']}</p>"
        "</div>"
        # how we work it out
        "<div class='dd-block'>"
        "<div class='dd-eyebrow'><span class='n'>02</span> How we work it out</div>"
        f"{how_paras}{scorekey}{eg}"
        f"<div class='dd-sources'>{src_chips}</div>"
        "</div>"
        "</div>"
        # trust close
        "<div class='dd-trust reveal'>"
        "<div class='dd-eyebrow'>Why you can trust this</div>"
        f"<p>{d['trust']}</p>"
        "</div>"
        # honest caveat
        "<div class='dd-caveat'><span class='ic'>&#9888;</span>"
        f"<span><b>Honest caveat:</b> {d['caveat']}</span></div>"
        # cross-links
        f"<div class='dd-more'>Keep exploring: {more_links}</div>"
        "</div></section>"
    )
    return shell(d["title"], d["meta"], body, here="", extra_head=DEEPDIVE_CSS)


# ──────────────────────────────────────────────────────────────────────────────
def build() -> dict:
    rows, _ = sample_data.display_rows()
    by_city: dict[str, list] = {}
    for r in rows:
        by_city.setdefault(r["listing"].city or "Other", []).append(r)

    OUT.mkdir(exist_ok=True)
    written = []

    # Ship the owner's hero animation + poster with the site.
    assets = OUT / "assets"
    assets.mkdir(exist_ok=True)
    if HERO_VIDEO_SRC.exists():
        shutil.copy2(HERO_VIDEO_SRC, assets / "hero.mp4")
        print(f"Copied hero video -> {assets / 'hero.mp4'} "
              f"({HERO_VIDEO_SRC.stat().st_size/1_000_000:.1f} MB)")
    else:
        print(f"WARNING: hero video not found at {HERO_VIDEO_SRC} — "
              "index falls back to the poster still.")
    if HERO_POSTER_SRC.exists():
        shutil.copy2(HERO_POSTER_SRC, assets / "hero_usa_map.jpg")
        print(f"Copied hero poster -> {assets / 'hero_usa_map.jpg'}")
    else:
        print(f"WARNING: hero poster not found at {HERO_POSTER_SRC}.")
    # The dark cinematic homepage hero photo (real dusk house).
    if HERO_HOUSE_SRC.exists():
        shutil.copy2(HERO_HOUSE_SRC, assets / "hero_house.jpg")
        print(f"Copied cinematic hero photo -> {assets / 'hero_house.jpg'} "
              f"({HERO_HOUSE_SRC.stat().st_size/1_000_000:.1f} MB)")
    else:
        print(f"WARNING: cinematic hero photo not found at {HERO_HOUSE_SRC} — "
              "the dark hero will show its navy fallback field.")
    # The cinematic homepage hero VIDEO (couple at their new home) + poster still.
    if HERO_COUPLE_VIDEO_SRC.exists():
        shutil.copy2(HERO_COUPLE_VIDEO_SRC, assets / "hero_couple.mp4")
        print(f"Copied cinematic hero video -> {assets / 'hero_couple.mp4'} "
              f"({HERO_COUPLE_VIDEO_SRC.stat().st_size/1_000_000:.1f} MB)")
    else:
        print(f"WARNING: cinematic hero video not found at {HERO_COUPLE_VIDEO_SRC} — "
              "the dark hero falls back to its poster still.")
    if HERO_COUPLE_POSTER_SRC.exists():
        shutil.copy2(HERO_COUPLE_POSTER_SRC, assets / "hero_couple_poster.jpg")
        print(f"Copied cinematic hero poster -> {assets / 'hero_couple_poster.jpg'} "
              f"({HERO_COUPLE_POSTER_SRC.stat().st_size/1_000:.0f} KB)")
    else:
        print(f"WARNING: cinematic hero poster not found at {HERO_COUPLE_POSTER_SRC}.")

    # ── City pages ──
    for city, crows in by_city.items():
        crows.sort(key=lambda r: -r["score"].total)
        st = crows[0]["listing"].state or ""
        body = (
            "<section class='masthead' style='padding-bottom:0'><div class='wrap'>"
            "<div class='pagehero reveal in'>"
            "<div class='kicker'>Best deals · Updated from live data</div>"
            f"<h1>Best home deals in <em>{city}</em>, {st}.</h1>"
            f"<p>{len(crows)} home{'' if len(crows) == 1 else 's'} scored 0–100 for value — "
            "the best deals first, in plain "
            "English, with fire/flood insurance risk built in.</p>"
            "<div class='cta-row'>"
            f"<a class='btn-fill' href='#early-access'>Get early access {svg('arrow', w=18)}</a>"
            "<a class='btn-line' href='report-underpriced.html'>Most underpriced <span class='ar'>→</span></a>"
            "</div></div>"
            f"<div class='deal-list'>{''.join(card_html(r) for r in crows)}</div>"
            "<p class='pagelinks'><a href='index.html'>← All cities</a> · "
            "<a href='report-underpriced.html'>Most underpriced homes →</a></p>"
            "</div></section>"
            + WAITLIST
        )
        f = OUT / f"deals-in-{slug(city)}.html"
        f.write_text(shell(
            f"Best home deals in {city}, {st} | Underlisted",
            f"Underpriced and foreclosure homes in {city}, {st}, scored 0–100 with value, "
            "rent, and fire/flood insurance risk.",
            body, here="index"), encoding="utf-8")
        written.append(f.name)

    # ── Underpriced report (PR asset) ──
    ranked = sorted((r for r in rows if (_discount(r) or 0) > 0),
                    key=lambda r: -_discount(r))[:25]
    body = (
        "<section class='masthead' style='padding-bottom:0'><div class='wrap'>"
        "<div class='pagehero reveal in'>"
        "<div class='kicker'>Data report · Nationwide</div>"
        "<h1>The most <em>underpriced</em> homes right now.</h1>"
        "<p>Homes listed furthest below their estimated value — across every area we track. "
        "A data snapshot from Underlisted.</p></div>"
        f"<div class='deal-list'>{''.join(card_html(r) for r in ranked)}</div>"
        "<p class='pagelinks'><a href='index.html'>← Home</a></p>"
        "</div></section>"
        + WAITLIST
    )
    (OUT / "report-underpriced.html").write_text(shell(
        "Most underpriced homes in America right now | Underlisted",
        "A data report of the most underpriced homes right now, scored by how far below "
        "estimated value they're listed.",
        body, here="report"), encoding="utf-8")
    written.append("report-underpriced.html")

    # ── Index hub — the full brand homepage ──
    city_chips = "".join(
        f"<a href='deals-in-{slug(c)}.html'>{c} · {len(rs)} home{'' if len(rs) == 1 else 's'}</a>"
        for c, rs in sorted(by_city.items()))
    city_chips = f"<div class='toc' style='margin-top:0'>{city_chips}</div>"
    (OUT / "index.html").write_text(index_page(city_chips), encoding="utf-8")
    written.append("index.html")

    # ── Free Tools hub + the four calculators (Google entry points → waitlist) ──
    (OUT / "free-tools.html").write_text(free_tools_hub_page(), encoding="utf-8")
    written.append("free-tools.html")
    for c in CALCULATORS:
        page = calc_shell(
            c["title"], c["meta"],
            h1=c["h1"], intro=c["intro"], body=c["body"](), here="tools",
        )
        (OUT / c["file"]).write_text(page, encoding="utf-8")
        written.append(c["file"])

    # ── Learn the basics — free glossary (no waitlist) ──
    (OUT / "learn.html").write_text(learn_page(), encoding="utf-8")
    written.append("learn.html")

    # ── "See how it works" deep-dives — one per galaxy feature (no waitlist) ──
    for d in DEEPDIVES:
        (OUT / d["file"]).write_text(deepdive_page(d), encoding="utf-8")
        written.append(d["file"])

    # ── Thank-you page — waitlist redirect target ──
    (OUT / "thanks.html").write_text(thanks_page(), encoding="utf-8")
    written.append("thanks.html")

    return {"pages": written, "cities": list(by_city)}


if __name__ == "__main__":
    res = build()
    print("Wrote", len(res["pages"]), "pages to site/ :", ", ".join(res["pages"]))
    print("Cities:", res["cities"])

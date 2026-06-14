"""
Static-site generator — the SEO + PR engine.

Reads our cached, scored listings (deal score, value discount, FEMA risk, FHFA
price trend) and writes plain STATIC HTML you can host anywhere:
  * site/index.html                  — hub linking every city page + the report
  * site/deals-in-<city>.html        — "Best home deals in <City>" (one per city)
  * site/report-underpriced.html     — "Most underpriced homes right now" (PR asset)

Why static HTML (not a Streamlit page): search engines index static pages with real
URLs + titles; a Streamlit app does not rank. Host these on any web host/CDN and they
become millions of search entry points over time. FREE to generate (no API calls).

Run:  .venv\\Scripts\\python.exe tools\\gen_site.py
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Owner's Kling animation — shipped as the website hero video.
HERO_VIDEO_SRC = ROOT / "Smoothly_animate_from_the_firs_Kling_30__78676.mp4"

from app import sample_data            # noqa: E402  (no streamlit imported here)
from src.data_sources import market    # noqa: E402
from src import glossary                # noqa: E402  (shared term wording: app + site)

OUT = ROOT / "site"
GREEN, DEEP, INK, MUTED, AMBER, RED = "#1D9E75", "#0F6E56", "#1F2933", "#667085", "#E08A00", "#C0392B"


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


CSS = f"""
<style>
 body{{margin:0;background:#F2F4F5;color:{INK};font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif}}
 .wrap{{max-width:900px;margin:0 auto;padding:22px}}
 a{{color:{DEEP}}}
 .hero{{background:linear-gradient(135deg,{DEEP},{GREEN});color:#fff;border-radius:18px;padding:26px 22px}}
 .hero h1{{margin:.2rem 0;font-size:1.8rem}} .hero p{{color:#EAFBF4;margin:.2rem 0}}
 /* Video hero: the owner's animation as a full-bleed background with a warm
    gradient scrim so the headline + CTA stay crisp over any video frame. */
 .hero-video{{position:relative;overflow:hidden;border-radius:22px;background:linear-gradient(135deg,{DEEP},{GREEN});
   color:#fff;min-height:360px;display:flex;align-items:flex-end;
   box-shadow:0 18px 50px rgba(15,110,86,.28)}}
 .hero-video video{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0}}
 .hero-video .scrim{{position:absolute;inset:0;z-index:1;
   background:linear-gradient(180deg,rgba(15,110,86,.10) 0%,rgba(15,110,86,.30) 45%,rgba(11,42,33,.82) 100%)}}
 .hero-video .hero-content{{position:relative;z-index:2;padding:30px 26px;max-width:640px}}
 .hero-video h1{{margin:.1rem 0;font-size:2.3rem;line-height:1.12;
   text-shadow:0 2px 18px rgba(0,0,0,.35)}}
 .hero-video p{{color:#F1FBF7;margin:.5rem 0 0;font-size:1.08rem;
   text-shadow:0 1px 10px rgba(0,0,0,.35)}}
 .hero-video .cta{{margin-top:16px;font-size:1.05rem;padding:13px 22px;
   box-shadow:0 8px 22px rgba(29,158,117,.5)}}
 @media (max-width:640px){{
   .hero-video{{min-height:300px}}
   .hero-video h1{{font-size:1.7rem}}
   .hero-video .hero-content{{padding:22px 18px}}
 }}
 .card{{background:#fff;border:1px solid #E4E7EC;border-radius:14px;padding:14px;margin:12px 0;display:flex;gap:14px;align-items:center}}
 .gauge{{width:54px;height:54px;border-radius:12px;color:#fff;font-weight:800;display:flex;align-items:center;justify-content:center;font-size:1.2rem;flex:0 0 auto}}
 .price{{font-size:1.25rem;font-weight:800;color:{DEEP}}}
 .muted{{color:{MUTED};font-size:.9rem}}
 .pill{{display:inline-block;border-radius:999px;padding:2px 9px;font-size:.78rem;font-weight:700;margin-right:6px}}
 .good{{background:#E1F5EE;color:{DEEP}}} .warn{{background:#FBE9E4;color:{RED}}}
 .cta{{display:inline-block;background:{GREEN};color:#fff;text-decoration:none;padding:10px 16px;border-radius:10px;font-weight:700;margin-top:8px}}
 .grid a{{display:block;background:#fff;border:1px solid #E4E7EC;border-radius:12px;padding:14px;margin:8px 0;text-decoration:none;color:{INK};font-weight:700}}
 .waitlist{{background:#E1F5EE;border:1px solid #C7EBDD;border-radius:16px;padding:20px;margin:18px 0;text-align:center}}
 .waitlist h3{{margin:.2rem 0;color:{DEEP};font-size:1.25rem}}
 .waitlist p{{color:{INK};margin:.3rem 0 .9rem}}
 .waitlist form{{display:flex;gap:8px;flex-wrap:wrap;justify-content:center}}
 .waitlist input[type=email]{{flex:1;min-width:220px;padding:12px;border:1px solid {DEEP};border-radius:10px;font-size:1rem}}
 .waitlist button{{background:{GREEN};color:#fff;border:0;padding:12px 18px;border-radius:10px;font-weight:700;font-size:1rem;cursor:pointer}}
 .foot{{color:#9AA4AC;font-size:.8rem;margin:24px 0;text-align:center}}
 /* Top nav — same on every page so people can always find "Learn the basics". */
 .nav{{display:flex;align-items:center;gap:18px;flex-wrap:wrap;padding:6px 2px 14px}}
 .nav .brand{{font-weight:800;font-size:1.15rem;color:{DEEP};text-decoration:none;margin-right:auto}}
 .nav a{{text-decoration:none;color:{INK};font-weight:600;font-size:.96rem}}
 .nav a:hover{{color:{DEEP}}}
 .nav a.here{{color:{DEEP};border-bottom:2px solid {GREEN};padding-bottom:2px}}
 /* Learn page — warm, friendly teaching cards. */
 .learn-intro{{background:#FFF8EE;border:1px solid #F3E2C4;border-radius:16px;padding:20px 22px;margin:8px 0 18px}}
 .learn-intro h1{{margin:.1rem 0 .4rem;font-size:1.85rem;color:{DEEP}}}
 .learn-intro p{{margin:.3rem 0;color:{INK};font-size:1.05rem;line-height:1.5}}
 .toc{{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 6px}}
 .toc a{{display:inline-block;background:#fff;border:1px solid #E4E7EC;border-radius:999px;
   padding:7px 13px;font-size:.88rem;font-weight:600;color:{DEEP};text-decoration:none}}
 .toc a:hover{{background:#E1F5EE;border-color:#C7EBDD}}
 .term{{background:#fff;border:1px solid #E4E7EC;border-left:5px solid {GREEN};border-radius:14px;
   padding:16px 18px;margin:12px 0;scroll-margin-top:14px}}
 .term h2{{margin:.1rem 0 .5rem;font-size:1.22rem;color:{INK};display:flex;align-items:center;gap:9px}}
 .term .ic{{font-size:1.3rem;line-height:1}}
 .term p{{margin:.35rem 0;color:{INK};line-height:1.55;font-size:1.02rem}}
 .term .eg{{background:#F6FBF9;border:1px dashed #BFE6D6;border-radius:10px;padding:9px 12px;
   margin:.6rem 0 .1rem;color:#33524A;font-size:.97rem}}
 .term .eg b{{color:{DEEP}}}
 .term.warnterm{{border-left-color:{AMBER}}}
 .term.warnterm .eg{{background:#FFF8EE;border-color:#F3D9A8;color:#6b5320}}
 .term.warnterm .eg b{{color:{AMBER}}}
 .scorekey{{display:flex;gap:8px;flex-wrap:wrap;margin:.5rem 0 .2rem}}
 .scorekey span{{display:inline-flex;align-items:center;gap:7px;border-radius:999px;
   padding:5px 12px;font-weight:700;font-size:.9rem;color:#fff}}
 .scorekey .dot{{width:11px;height:11px;border-radius:50%;background:rgba(255,255,255,.85);display:inline-block}}
</style>"""


# Free email capture via Netlify Forms (no backend): Netlify auto-detects this
# static <form> at deploy and stores every submission (view/export in the Netlify
# dashboard → Forms). honeypot 'bot-field' blocks spam bots; action redirects to
# our own thank-you page.
WAITLIST = (
    "<div class='waitlist' id='early-access'>"
    "<h3>🔑 Get early access</h3>"
    "<p>Be first in line when we open up — and lock in <b>$12.99/mo for a year</b> "
    "(the price is rising to $44.99 soon). No spam, just your invite.</p>"
    "<form name='waitlist' method='POST' data-netlify='true' "
    "netlify-honeypot='bot-field' action='/thanks.html'>"
    "<input type='hidden' name='form-name' value='waitlist'/>"
    "<p style='display:none'><label>Leave blank: <input name='bot-field'/></label></p>"
    "<input type='email' name='email' placeholder='you@email.com' required/>"
    "<button type='submit'>Join the waitlist →</button>"
    "</form></div>"
)


def _score_color(s):
    return GREEN if s >= 70 else (AMBER if s >= 45 else RED)


def card_html(row) -> str:
    l, s = row["listing"], row["score"]
    disc = _discount(row)
    risk = row.get("risk")
    pills = ""
    if disc and disc > 0:
        pills += f"<span class='pill good'>{disc:.0f}% below value</span>"
    if risk and getattr(risk, "flood_zone", "") == "High":
        pills += "<span class='pill warn'>Flood zone</span>"
    if risk and getattr(risk, "fire_zone", "") in ("High", "Moderate"):
        pills += f"<span class='pill warn'>{risk.fire_zone} fire risk</span>"
    trend = market.price_trend(l.zip_code)
    tr = ""
    if trend and trend.get("change") is not None:
        up = trend["change"] >= 0
        tr = (f"<div class='muted'>Area prices {'▲' if up else '▼'} "
              f"{abs(trend['change']):.1f}% ({trend['year']})</div>")
    return (f"<div class='card'><div class='gauge' style='background:{_score_color(s.total)}'>"
            f"{s.total}</div><div><div class='price'>{money(l.list_price)}</div>"
            f"<div style='font-weight:700'>{l.address or '—'}</div>{pills}{tr}</div></div>")


# Shared top nav. `here` = the slug of the current page so we can underline it.
def nav_html(here: str = "") -> str:
    def cls(slug):
        return " class='here'" if here == slug else ""
    return (
        "<nav class='nav'>"
        "<a class='brand' href='index.html'>Underlisted</a>"
        f"<a href='index.html'{cls('index')}>Deals</a>"
        f"<a href='report-underpriced.html'{cls('report')}>Most underpriced</a>"
        f"<a href='learn.html'{cls('learn')}>Learn the basics</a>"
        "<a href='index.html#early-access'>Get early access</a>"
        "</nav>"
    )


# The plain-English glossary now lives in ONE place: src/glossary.py (shared by
# this site generator AND the app's in-app "What does this mean?" tooltips, so the
# website and the app teach with identical wording). Edit the words there.
#
# The Deal Score card gets a small colored key (a website-only flourish), keyed by
# the glossary term id so it stays attached to the right card.
LEARN_EXTRA_EG = {
    "deal-score":
        "<div class='scorekey'><span style='background:#1D9E75'><span class='dot'>"
        "</span>70–100 Good</span><span style='background:#E08A00'><span class='dot'>"
        "</span>45–69 Okay</span><span style='background:#C0392B'><span class='dot'>"
        "</span>0–44 Weak</span></div>",
}


def learn_page_body() -> str:
    toc = "".join(
        f"<a href='#{t.key}'>{t.label}</a>" for t in glossary.TERMS
    )
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
    return (
        "<div class='learn-intro'>"
        "<h1>Learn the basics — in plain English</h1>"
        "<p>Buying a home comes with a lot of confusing words. Here's every term we "
        "show you, explained simply — like we're chatting at the kitchen table. "
        "No jargon, no pressure. This page is free.</p>"
        "<p style='color:#7a6a4a;font-size:.95rem'>Tap a word to jump to it 👇</p>"
        f"<div class='toc'>{toc}</div>"
        "</div>"
        + "".join(cards)
        + "<p style='margin:18px 2px;color:#667085'>That's the whole glossary. "
        "When you see any of these inside Underlisted, you'll know exactly what it means. "
        "<a href='index.html'>← Back to the deals</a></p>"
    )


def page(title: str, desc: str, body: str, here: str = "", waitlist: bool = True) -> str:
    tail = WAITLIST if waitlist else ""
    return (f"<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{title}</title><meta name='description' content='{desc}'>{CSS}</head>"
            f"<body><div class='wrap'>{nav_html(here)}{body}{tail}"
            f"<p class='foot'>Estimates only — a screening tool, not advice. "
            f"Fair Housing: scoring never uses demographic or neighborhood-quality signals.</p>"
            f"</div></body></html>")


def build() -> dict:
    rows, _ = sample_data.display_rows()
    by_city: dict[str, list] = {}
    for r in rows:
        by_city.setdefault(r["listing"].city or "Other", []).append(r)

    OUT.mkdir(exist_ok=True)
    written = []

    # Ship the owner's hero animation with the site (site/assets/hero.mp4).
    assets = OUT / "assets"
    assets.mkdir(exist_ok=True)
    if HERO_VIDEO_SRC.exists():
        shutil.copy2(HERO_VIDEO_SRC, assets / "hero.mp4")
        print(f"Copied hero video -> {assets / 'hero.mp4'} "
              f"({HERO_VIDEO_SRC.stat().st_size/1_000_000:.1f} MB)")
    else:
        print(f"WARNING: hero video not found at {HERO_VIDEO_SRC} — "
              "index will fall back to the gradient background.")

    # City pages
    for city, crows in by_city.items():
        crows.sort(key=lambda r: -r["score"].total)
        st = crows[0]["listing"].state or ""
        body = (f"<div class='hero'><h1>Best home deals in {city}, {st}</h1>"
                f"<p>{len(crows)} homes scored 0–100 for value — best deals first. "
                f"Updated from live data.</p>"
                f"<a class='cta' href='#early-access'>"
                f"Get early access →</a></div>"
                + "".join(card_html(r) for r in crows)
                + "<p><a href='index.html'>← All cities</a> · "
                "<a href='report-underpriced.html'>Most underpriced homes →</a></p>")
        f = OUT / f"deals-in-{slug(city)}.html"
        f.write_text(page(f"Best home deals in {city}, {st} | Underlisted",
                          f"Underpriced and foreclosure homes in {city}, {st}, scored 0–100 "
                          "with value, rent, and fire/flood insurance risk.", body),
                     encoding="utf-8")
        written.append(f.name)

    # Underpriced report (PR asset)
    ranked = sorted((r for r in rows if (_discount(r) or 0) > 0),
                    key=lambda r: -_discount(r))[:25]
    body = ("<div class='hero'><h1>Most underpriced homes right now</h1>"
            "<p>Homes listed furthest below their estimated value — across every area "
            "we track. A data snapshot from Underlisted.</p></div>"
            + "".join(card_html(r) for r in ranked)
            + "<p><a href='index.html'>← Home</a></p>")
    (OUT / "report-underpriced.html").write_text(
        page("Most underpriced homes in America right now | Underlisted",
             "A data report of the most underpriced homes right now, scored by how far "
             "below estimated value they're listed.", body, here="report"), encoding="utf-8")
    written.append("report-underpriced.html")

    # Index hub
    links = "".join(f"<a href='deals-in-{slug(c)}.html'>Best deals in {c} "
                    f"<span class='muted'>({len(rs)} homes)</span></a>"
                    for c, rs in sorted(by_city.items()))
    body = ("<div class='hero-video'>"
            "<video autoplay muted loop playsinline preload='auto' "
            "aria-label='Underlisted — finding under-priced U.S. homes'>"
            "<source src='assets/hero.mp4' type='video/mp4'>"
            "</video>"
            "<div class='scrim'></div>"
            "<div class='hero-content'>"
            "<h1>Find under-priced U.S. homes</h1>"
            "<p>Every home gets a plain-English deal score (0–100) — with fire/flood "
            "insurance risk and the cash you'd really need. No spreadsheets.</p>"
            "<a class='cta' href='#early-access'>Get early access →</a>"
            "</div></div>"
            "<p style='margin:6px 0'><a href='report-underpriced.html'>"
            "See the most underpriced homes right now →</a></p>"
            "<p style='margin:6px 0'><a href='learn.html'>"
            "New to all this? Learn the basics in plain English (free) →</a></p>"
            f"<h3>Deals by city</h3><div class='grid'>{links}</div>")
    (OUT / "index.html").write_text(
        page("Underlisted — under-priced & foreclosure homes across the U.S.",
             "Find under-priced and foreclosure homes across the U.S., scored 0–100 with "
             "value, rent, cash-needed, and fire/flood insurance risk.", body, here="index"),
        encoding="utf-8")
    written.append("index.html")

    # Learn the basics — a FREE, friendly plain-English glossary (teaching page,
    # not a sales page → no waitlist form). Helps first-time buyers AND ranks for
    # "what is a deal score / PMI / HOA / cash to close" style searches.
    (OUT / "learn.html").write_text(
        page("Learn the basics — home-buying words in plain English | Underlisted",
             "A free, plain-English glossary for first-time home buyers: deal score, "
             "underpriced, estimated value, true monthly cost, PMI, HOA, property tax, "
             "cash to close, days on market, mortgage rate and insurance risk — explained "
             "simply.",
             learn_page_body(), here="learn", waitlist=False),
        encoding="utf-8")
    written.append("learn.html")

    # Thank-you page — where the waitlist form redirects after a successful submit.
    # Built without the page() wrapper so it doesn't show the signup form again.
    thanks = (f"<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>"
              f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
              f"<title>You're on the list | Underlisted</title>"
              f"<meta name='robots' content='noindex'>{CSS}</head>"
              f"<body><div class='wrap'><div class='hero'><h1>🎉 You're on the list!</h1>"
              f"<p>Thanks! You'll be first to know when we open — and your "
              f"<b>$12.99/mo founding price</b> is reserved.</p>"
              f"<a class='cta' href='index.html'>← Back to the deals</a></div>"
              f"<p class='foot'>Estimates only — a screening tool, not advice.</p>"
              f"</div></body></html>")
    (OUT / "thanks.html").write_text(thanks, encoding="utf-8")
    written.append("thanks.html")
    return {"pages": written, "cities": list(by_city)}


if __name__ == "__main__":
    res = build()
    print("Wrote", len(res["pages"]), "pages to site/ :", ", ".join(res["pages"]))
    print("Cities:", res["cities"])

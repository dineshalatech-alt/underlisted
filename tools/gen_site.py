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
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import sample_data            # noqa: E402  (no streamlit imported here)
from src.data_sources import market    # noqa: E402

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


def page(title: str, desc: str, body: str) -> str:
    return (f"<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{title}</title><meta name='description' content='{desc}'>{CSS}</head>"
            f"<body><div class='wrap'>{body}{WAITLIST}"
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
             "below estimated value they're listed.", body), encoding="utf-8")
    written.append("report-underpriced.html")

    # Index hub
    links = "".join(f"<a href='deals-in-{slug(c)}.html'>Best deals in {c} "
                    f"<span class='muted'>({len(rs)} homes)</span></a>"
                    for c, rs in sorted(by_city.items()))
    body = ("<div class='hero'><h1>Find under-priced U.S. homes</h1>"
            "<p>Browse the best home deals by city — scored 0–100, with fire/flood "
            "insurance risk and the cash you'd really need.</p>"
            "<a class='cta' href='#early-access'>Get early access →</a></div>"
            "<p style='margin:6px 0'><a href='report-underpriced.html'>"
            "See the most underpriced homes right now →</a></p>"
            f"<h3>Deals by city</h3><div class='grid'>{links}</div>")
    (OUT / "index.html").write_text(
        page("Underlisted — under-priced & foreclosure homes across the U.S.",
             "Find under-priced and foreclosure homes across the U.S., scored 0–100 with "
             "value, rent, cash-needed, and fire/flood insurance risk.", body),
        encoding="utf-8")
    written.append("index.html")

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

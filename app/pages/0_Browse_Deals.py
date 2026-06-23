"""
Browse Deals — the polished nationwide (U.S.) feed + detail screen.

Pure visual pass: NO API calls. Uses real cached listings (or clearly-marked
SAMPLE listings if the cache is empty). Photos are grey placeholders with a house
icon. Icons come from the Tabler set (app/icons.py).
"""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote as _url_quote

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402

from config.settings import settings  # noqa: E402
from src import metrics  # noqa: E402
from src import glossary  # noqa: E402  (shared plain-English wording: app + site)
from src.models import listing_contact  # noqa: E402
from src.data_sources import rentcast, market  # noqa: E402
from src.financing import cash_needed  # noqa: E402
from src.affordability import afford  # noqa: E402
from src.cache import db  # noqa: E402
from app.assets.theme import (APP_CSS, DEEP_GREEN, PRIMARY_GREEN, LIGHT_FILL,  # noqa: E402
                              MUTED, AMBER, RED, score_color)
from app.assets import deal_visual as dv  # noqa: E402  (approved "Trusted morning" deal page)
from app.icons import TABLER_CSS, ic  # noqa: E402
from app.helpers import (money, number, dom_label, gmaps_link, pct,  # noqa: E402
                         favicon_path, wait_message, random_tip)
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
  .afford {{ border-radius:14px; padding:14px 16px; margin:6px 0 4px; }}
  .afford .verdict {{ font-size:1.25rem; font-weight:850; }}
  .afford .sub {{ font-size:1.0rem; margin-top:2px; }}
  .costrow {{ display:flex; justify-content:space-between; align-items:baseline;
              padding:7px 0; border-bottom:1px solid #EEE8DF; }}
  .costrow .lbl {{ font-weight:700; color:#1F2933; }}
  .costrow .amt {{ font-weight:800; color:{DEEP_GREEN}; white-space:nowrap; }}
  .costtot {{ display:flex; justify-content:space-between; align-items:baseline;
              padding:10px 0 2px; font-size:1.15rem; }}
  .costtot .lbl {{ font-weight:850; }}
  .costtot .amt {{ font-weight:850; color:{DEEP_GREEN}; }}
</style>
"""
st.markdown(APP_CSS + TABLER_CSS + FEED_CSS, unsafe_allow_html=True)

st.session_state.setdefault("open_id", None)

FACTOR_COLORS = {"value_discount": "#1D9E75", "rent_yield": "#2E86C1",
                 "days_on_market": "#8E44AD", "risk": "#F39C12"}


# --- In-app teaching: "What does this mean?" helpers -----------------------
# The SAME kid-simple wording the website's "Learn the basics" page uses, placed
# right where people get confused. Tucked inside a small popover so the screen
# stays calm and airy — the teaching only appears when someone taps for it.
def _explain(term_key: str, *, label: str = "What does this mean?",
             example: bool = True) -> None:
    """Render a small tucked-away popover explaining one glossary term.

    Pulls plain-English text from src/glossary.py (one source of truth shared with
    the website), so the app and site teach identically. Stays out of the way
    until tapped — no clutter.
    """
    t = glossary.get(term_key)
    with st.popover(label, use_container_width=False):
        st.markdown(f"**{t.icon} {t.title}**")
        st.markdown(glossary.app_tip(term_key, include_example=example))


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


def _why_in_plain_english(score) -> str:
    """One plain sentence: the single biggest reason behind the score."""
    used = [f for f in score.used_factors if f.points > 0]
    if not used:
        return ("We don't have enough data on this home yet to score it well — "
                "treat the number as a rough first look.")
    top = max(used, key=lambda f: f.points)
    lead = {
        "value_discount": "Mostly because it's listed below its estimated value",
        "rent_yield": "Mostly because the rent it could earn is strong for the price",
        "days_on_market": "Mostly because it's sat on the market a while "
                          "(more room to negotiate)",
        "risk": "Helped by low fire/flood risk here",
    }.get(top.key, f"Mostly from: {top.label}")
    if score.total >= score.threshold:
        verdict = "this looks like a good deal."
    elif score.total >= 45:
        verdict = "it's worth a look, but not a standout."
    else:
        verdict = "it's a below-average deal at this price."
    return f"{lead} — {verdict}"


def _photo_placeholder() -> str:
    return f"<div class='photo'>{ic('home', 46, MUTED)}</div>"


def _facts_html(l) -> str:
    return (f"<div class='facts'>{ic('beds')} {number(l.beds)} bd &nbsp; "
            f"{ic('baths')} {number(l.baths)} ba &nbsp; "
            f"{ic('sqft')} {number(l.sqft)} sqft &nbsp; "
            f"{ic('year')} {number(l.year_built)}</div>")


# --- Foreclosure / bank-owned helpers --------------------------------------
GOV_LINKS = [
    ("HUD HomeStore", "https://www.hudhomestore.gov"),
    ("HomePath", "https://homepath.fanniemae.com"),
    ("HomeSteps", "https://www.homesteps.com"),
]


def _bank_badge() -> str:
    return (f"<span class='badge badge-bank'>{ic('bank',15,'#344054')} "
            "Bank-owned · foreclosure</span>")


def _discount_html(val, price) -> str:
    """Foreclosure deal signal: the bid vs the lender's estimated value."""
    avm = getattr(val, "avm", None)
    if not avm or not price:
        return ("<div class='facts'>Estimated value not available — "
                "verify before bidding.</div>")
    diff = avm - price
    pctv = abs(diff) / avm * 100
    if diff > 0:
        return (f"<div class='facts'>{ic('value',16,PRIMARY_GREEN)} Bid "
                f"<b>{money(price)}</b> vs est. value <b>{money(avm)}</b> — "
                f"<b style='color:{PRIMARY_GREEN}'>{pctv:.0f}% below value</b></div>")
    return (f"<div class='facts'>{ic('value',16,MUTED)} Bid <b>{money(price)}</b> vs "
            f"est. value <b>{money(avm)}</b> — {pctv:.0f}% above value</div>")


# --- Nationwide search: match cached rows + load new areas on demand --------
def _parse_area(q: str):
    """Turn a search string into (city, state, zip)."""
    q = q.strip()
    if q.isdigit():
        return None, None, q                          # ZIP
    if "," in q:
        city, st_ = [p.strip() for p in q.split(",", 1)]
        return city, (st_[:2].upper() or None), None   # "City, ST"
    return q, None, None                              # city only


def _matches_area(listing, q: str) -> bool:
    """Does a cached listing match the search box? (empty query = show all)."""
    q = (q or "").strip().lower()
    if not q:
        return True
    if q.isdigit():
        return (listing.zip_code or "").startswith(q)
    city_q = q.split(",")[0].strip()
    return city_q in (listing.city or "").lower()


def _offer_area_load(q: str) -> None:
    """When a searched area isn't cached, offer to fetch it (one billable call)."""
    st.markdown(f"<div style='background:{LIGHT_FILL};color:{DEEP_GREEN};padding:10px "
                f"14px;border-radius:10px;font-weight:600'>No listings cached for "
                f"“{q}” yet.</div>", unsafe_allow_html=True)
    if not settings.has_rentcast:
        st.warning("Add your RentCast key to .env to load new areas.")
        return
    city, state, zipc = _parse_area(q)
    if st.button(f"Load listings for {q}  (uses 1 RentCast lookup)",
                 type="primary", key="loadarea"):
        tip = st.empty()
        tip.caption(random_tip())
        with st.spinner(wait_message(q)):
            summary = rentcast.sync_area(city=city, state=state, zip_code=zipc)
        tip.empty()
        if summary.get("errors"):
            st.error("Couldn't load: " + "; ".join(summary["errors"]))
        elif summary.get("total_seen", 0) == 0:
            st.warning(f"No active listings found for “{q}”. Try a nearby ZIP or "
                       "the “City, ST” format.")
        else:
            st.success(f"Loaded {summary['new'] + summary['updated']} listing(s) "
                       f"for {q}.")
            st.rerun()


# --- Risk flags (fire / flood) — the differentiator ------------------------
def _risk_badges(risk) -> str:
    """Small fire/flood pills, shown only when there's real risk worth flagging."""
    if not risk:
        return ""
    pills = []
    if (risk.fire_zone or "") in ("High", "Moderate"):
        c = RED if risk.fire_zone == "High" else AMBER
        pills.append(f"<span class='badge' style='background:#FBE9E4;color:{c}'>"
                     f"{ic('fire',14,c)} {risk.fire_zone} fire risk</span>")
    if (risk.flood_zone or "") == "High":
        pills.append(f"<span class='badge' style='background:#FBE9E4;color:{RED}'>"
                     f"{ic('flood',14,RED)} Flood zone</span>")
    return " ".join(pills)


# --- "Can I Afford It?" — the affordability moat (zero API calls) ----------
_BAND_STYLE = {
    "green": (PRIMARY_GREEN, LIGHT_FILL, "check"),
    "amber": (AMBER, "#FBE9C7", "shield"),
    "red":   (RED, "#FBE9E4", "shield"),
}


def _money_range(r) -> str:
    """A labelled low–high range like '$1,800–$2,300/mo' (never false precision)."""
    if abs(r.high - r.low) < 1:
        return f"{money(r.low)}/mo"
    return f"{money(r.low)}–{money(r.high)}/mo"


def _verdict_badge(v) -> str:
    color, bg, icon = _BAND_STYLE.get(v.band, _BAND_STYLE["amber"])
    return (f"<div class='afford' style='background:{bg};border:1px solid {color}33'>"
            f"<div class='verdict' style='color:{color}'>{ic(icon,22,color)} "
            f"{v.headline}</div>"
            f"<div class='sub' style='color:#475467'>"
            + " ".join(v.reasons) + "</div></div>")


def _cost_rows(mc) -> str:
    """Surprise-cost panel rows: P&I + each labelled range. Honest ranges only."""
    rows = [f"<div class='costrow'><span class='lbl'>Loan payment "
            f"(principal + interest)</span>"
            f"<span class='amt'>{money(mc.principal_interest)}/mo</span></div>"]
    for it in mc.items:
        if not it.counts_in_payment:
            continue
        rows.append(f"<div class='costrow'><span class='lbl'>{it.label}</span>"
                    f"<span class='amt'>{_money_range(it.monthly)}</span></div>")
    hp = mc.housing_payment
    rows.append(f"<div class='costtot'><span class='lbl'>True monthly cost</span>"
                f"<span class='amt'>{_money_range(hp)}</span></div>")
    return "".join(rows)


def _render_credit_impact(price, occupancy, loan_type, band) -> None:
    """Plain 'what your credit score means for THIS home' — in real dollars.

    Pure math (afford.credit_impact), zero API calls. Turns the credit dropdown
    from a silent rate-tweak into a visible, motivating number: what a top score
    would save, and what improving by one band is worth.
    """
    if not price:
        return
    ci = afford.credit_impact(price, occupancy=occupancy, loan_type=loan_type,
                              credit_band=band)
    if ci.is_best:
        st.success(
            f"{ic('check',18,PRIMARY_GREEN)} Your credit ({ci.current_band}) gets the "
            f"**best rate lenders offer (~{pct(ci.current_rate)})** — the lowest "
            f"payment on this home, about **{money(ci.current_payment)}/mo** "
            "(loan only). Nice.", icon=None)
    else:
        msg = (
            f"At **{ci.current_band}** your rate is about **{pct(ci.current_rate)}** "
            f"(~{money(ci.current_payment)}/mo loan payment). Buyers with top credit "
            f"(740+) get ~{pct(ci.best_rate)} — about **{money(ci.monthly_saving_to_best)}/mo "
            "less** for the very same home.")
        if ci.next_band and ci.monthly_saving_to_next >= 1:
            msg += (f" Even nudging up to **{ci.next_band}** could save roughly "
                    f"**{money(ci.monthly_saving_to_next)}/mo** "
                    f"(~{money(ci.lifetime_saving_to_next)} over the loan).")
        st.info(msg, icon=None)
    _explain("credit-score", label="What does my credit score mean?")


def _render_afford(l, occupancy, loan_type, band, risk, *, mc, hoa_val) -> None:
    """The 'Can YOU afford it?' moat: a personal traffic-light verdict.

    The true-monthly-cost panel now renders ABOVE this (the visual stacked bar),
    so here we only collect the buyer's income/cash/debts and show the verdict
    using the approved traffic-light card. Pure logic — NO API calls. Personal
    inputs are kept out of logs; saved only (opt-in) to the per-user prefs row.
    """
    price = l.list_price or 0
    st.markdown(f"<div class='uv' style='margin-top:16px'><h4 style='font-family:\"Cormorant Garamond\",serif;"
                f"font-weight:600;font-size:1.4rem;color:{dv.T.TV_INK}'>Can <span "
                f"style='font-style:italic;color:{dv.T.TV_GOLD}'>you</span> "
                f"afford it?</h4></div>", unsafe_allow_html=True)
    _explain("afford", label="What does 'Can I afford it?' mean?")

    prefs = db.get_user_prefs(settings.current_user_id) or {}
    st.caption("Enter your numbers for a personal yes / maybe / no for THIS home. "
               "Private — never stored unless you ask.")
    a, b, c = st.columns(3)
    income = a.number_input("Your gross monthly income ($)", min_value=0,
                            max_value=200000, step=250,
                            value=int(prefs.get("gross_monthly_income", 0) or 0),
                            key=f"inc_{l.id}",
                            help="Before taxes. Add a co-buyer's income too.")
    cash = b.number_input("Cash you have for buying ($)", min_value=0,
                          max_value=5000000, step=1000,
                          value=int(prefs.get("cash_available", 0) or 0),
                          key=f"cash_{l.id}",
                          help="Savings you can put toward down payment + closing.")
    debts = c.number_input("Other monthly debts ($)", min_value=0,
                           max_value=100000, step=50,
                           value=int(prefs.get("monthly_debts", 0) or 0),
                           key=f"debt_{l.id}",
                           help="Car, student loans, credit cards, etc. NOT this home.")

    if income > 0:
        v = afford.verdict(price, gross_monthly_income=income,
                           cash_available=(cash if cash > 0 else None),
                           monthly_debts=debts, occupancy=occupancy,
                           loan_type=loan_type, credit_band=band, risk=risk,
                           hoa_monthly=hoa_val)
        st.markdown(dv.afford_light(v), unsafe_allow_html=True)
        st.caption("A rough screen, not a loan decision. Lenders look at your full "
                   "picture — talk to one before you commit.")
        if st.checkbox("Remember my numbers on this device", key=f"save_{l.id}"):
            # Stored to persist convenience; never logged or printed.
            db.save_user_prefs(settings.current_user_id, {
                "gross_monthly_income": income, "cash_available": cash,
                "monthly_debts": debts})
    else:
        st.info("Enter your monthly income above to see if this home fits your budget.")


# ===========================================================================
# DETAIL
# ===========================================================================
def _render_agent_contact(l) -> None:
    """Show a 'Call / Email the listing agent' block.

    The BUYER initiates contact: the buttons are plain tel:/mailto: links that
    open the buyer's OWN phone or email app. We never auto-send or message agents.
    RentCast's terms allow displaying this contact info to our paid users.

    Graceful fallback (agent -> brokerage office -> neutral "ask a local agent"):
    we always show something useful, never an empty/broken box.
    """
    c = listing_contact(l)

    # Build the tel:/mailto:/site hrefs here (where URL quoting + the real
    # listing data live), then hand them to the visual card renderer.
    tel_href = mailto_href = site_href = None
    if c.get("phone"):
        tel_href = "tel:" + "".join(ch for ch in c["phone"]
                                    if ch.isdigit() or ch == "+")
    if c.get("email"):
        subj = f"Question about {l.address or 'your listing'}"
        mailto_href = f"mailto:{c['email']}?subject={_url_quote(subj)}"
    if c.get("website"):
        site = c["website"]
        if not site.lower().startswith(("http://", "https://")):
            site = "https://" + site
        site_href = site

    st.markdown(dv.agent(contact=c, address=l.address, office_name=l.office_name,
                         tel_href=tel_href, mailto_href=mailto_href,
                         site_href=site_href), unsafe_allow_html=True)
    st.caption("You contact the agent directly from your own phone or email — "
               "Underlisted never messages agents for you.")


def _hero_why_html(score, val, row) -> str:
    """Plain one-paragraph 'why' for the dial hero, from REAL score factors."""
    facs = {f.key: f for f in score.used_factors}
    bits = []
    vd = facs.get("value_discount")
    if vd and vd.points > 0 and val and val.avm and row["listing"].list_price:
        diff = (val.avm - row["listing"].list_price) / val.avm * 100
        if diff >= 1:
            agree = " and two independent estimates agree" if row.get("attom_value") else ""
            bits.append(f"Listed about <b>{abs(diff):.0f}% below</b> what it's worth{agree}")
    dom = row["listing"].days_on_market
    if dom is not None and dom >= 30:
        bits.append(f"it's been waiting <b>{dom} days</b> — room to make an offer")
    if not bits:
        # Fall back to the existing plain-English summary sentence.
        return _esc_plain(_why_in_plain_english(score))
    return ". ".join(b[0].upper() + b[1:] if i == 0 else b
                     for i, b in enumerate(bits)) + "."


def _esc_plain(s: str) -> str:
    return s.replace("<", "&lt;").replace(">", "&gt;")


def render_detail(row) -> None:
    # Lazily fetch ATTOM's independent second opinion (AVM + last sale) for THIS
    # opened home only — cache-first, capped, never on the feed. Re-scores with
    # the blended value. No-op if ATTOM isn't configured or it's a sample home.
    row = sample_data.attom_second_opinion(row)
    l = row["listing"]
    val, rent, score = row["value"], row["rent"], row["score"]
    attom_val = row.get("attom_value")
    last_sale = row.get("attom_last_sale")

    # Inject the approved "Trusted morning" page styles once.
    st.markdown(dv.page_css(), unsafe_allow_html=True)

    if st.button("← Back to listings", key="back"):
        st.session_state.open_id = None
        st.rerun()

    # Foreclosure rows keep the older simple layout (no beds/baths/rent/afford).
    if row.get("foreclosure"):
        _render_foreclosure_detail(row)
        return

    # ===================== HERO: the Deal Dial (signature) =====================
    why = _hero_why_html(score, val, row)
    st.markdown(dv.hero(address=l.address or f"{l.city} {l.zip_code}",
                        score=score.total, why_html=why), unsafe_allow_html=True)

    # Facts + map link sit quietly under the hero.
    st.markdown(f"<div class='facts' style='margin-top:12px'>{_facts_inline(l)}</div>",
                unsafe_allow_html=True)
    link = gmaps_link(l.address)
    pt = market.price_trend(l.zip_code)
    meta = []
    if link:
        meta.append(f"<a href='{link}' target='_blank' style='color:{dv.T.TV_TEAL};"
                    f"font-weight:600'>Open in Google Maps</a>")
    if pt and pt.get("change") is not None:
        up = pt["change"] >= 0
        col = dv.T.TV_GOOD if up else dv.T.TV_WALK
        arrow = "▲" if up else "▼"
        meta.append(f"Prices in {l.zip_code}: <b style='color:{col}'>{arrow} "
                    f"{abs(pt['change']):.1f}%</b> in {pt['year']} · FHFA")
    if meta:
        st.markdown(f"<div class='facts'>{' &nbsp;·&nbsp; '.join(meta)}</div>",
                    unsafe_allow_html=True)

    # Tucked-away teaching for the score (kept from before — popovers stay calm).
    with st.expander("How we got this score"):
        _explain("deal-score", label="What does the Deal Score mean?")
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

    # ===================== WHAT IT'S REALLY WORTH =====================
    # Blended value drives the bar so it matches the deal score's own value.
    from src.scoring.deal_score import blended_avm
    blended, src_label = blended_avm(val, attom_val)
    if blended:
        st.markdown(dv.worth(asking=l.list_price or 0, value=blended,
                             source_label=src_label), unsafe_allow_html=True)
        with st.expander("More on value & rent"):
            if val.avm:
                if val.value_low and val.value_high:
                    st.caption(f"RentCast value range {money(val.value_low)}–"
                               f"{money(val.value_high)} · {len(val.comps or [])} comps"
                               + (" · sample" if row['value_sample'] else ""))
                _explain("estimated-value", label="What does 'estimated value' mean?")
            if attom_val and attom_val.avm:
                st.markdown(f"Second opinion on value **{money(attom_val.avm)}** "
                            "· ATTOM, an independent source")
            if last_sale and last_sale.get("amount"):
                d = last_sale.get("date") or ""
                yr = f" in {d[:4]}" if len(d) >= 4 and d[:4].isdigit() else ""
                st.markdown(f"Last sold for **{money(last_sale['amount'])}**{yr} "
                            "· public sale record (ATTOM)")
            rsample = " (sample)" if row["rent_sample"] else ""
            st.markdown(f"Estimated rent **{money(rent)}/mo**{rsample}")

    # ===================== INSURANCE & DISASTER CHECK (moat) =====================
    rf = row.get("risk")
    risk_html = dv.risk(fire_zone=getattr(rf, "fire_zone", None),
                        flood_zone=getattr(rf, "flood_zone", None),
                        insurance_note=getattr(rf, "insurance_note", None))
    if risk_html:
        st.markdown(risk_html, unsafe_allow_html=True)
        _explain("insurance-risk", label="What does this warning mean?")

    # ===================== Your plan (drives cost + cash + afford) =====================
    st.markdown(f"<div class='uv' style='margin-top:16px'><h4 style='font-family:\"Cormorant Garamond\",serif;"
                f"font-weight:600;font-size:1.4rem;color:{dv.T.TV_INK}'>Set up your numbers</h4></div>",
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
    _render_credit_impact(l.list_price or 0, occupancy, loan_type, band)
    hoa_known = st.toggle("I know this home's HOA dues", key=f"hoatog_{l.id}")
    hoa_val = None
    if hoa_known:
        hoa_val = st.number_input("HOA dues ($/month)", min_value=0, max_value=5000,
                                  value=0, step=25, key=f"hoa_{l.id}")

    # ===================== TRUE MONTHLY COST (stacked bar) =====================
    mc = afford.monthly_costs(l.list_price or 0, occupancy=occupancy,
                              loan_type=loan_type, credit_band=band,
                              risk=rf, hoa_monthly=hoa_val)
    st.markdown(dv.monthly_cost(mc), unsafe_allow_html=True)
    h1, h2, h3 = st.columns(3)
    with h1:
        _explain("true-monthly-cost", label="True monthly cost?", example=False)
    with h2:
        _explain("pmi", label="What's PMI?")
    with h3:
        _explain("hoa", label="What's HOA?")

    # ===================== CASH YOU'D NEED UP FRONT =====================
    cn = cash_needed.compute(l.list_price or 0, occupancy=occupancy,
                             loan_type=loan_type, credit_band=band)
    st.markdown(dv.cash(cn), unsafe_allow_html=True)
    with st.expander("Money you keep (reserves) + the power-user breakdown"):
        st.markdown(f"{ic('reserves',18,PRIMARY_GREEN)} **Reserves: {money(cn.reserves)}** "
                    f"· {cn.reserves_months} months — cash the lender wants you to keep "
                    "in the bank after buying. You don't spend it.", unsafe_allow_html=True)
        st.markdown(f"**Grand total cash needed (with reserves): {money(cn.total)}**")
        _explain("cash-to-close", label="What is 'cash to close' / a down payment?")
        m = metrics.compute(l, val, type("R", (), {"monthly_rent": rent})(),
                            settings.financing)
        c = st.columns(3)
        c[0].metric("Monthly payment", money(cn.monthly_payment))
        c[1].metric("Est. rate", pct(cn.interest_rate))
        c[2].metric("Loan amount", money(cn.loan_amount))
        c2 = st.columns(3)
        c2[0].metric("Gross yield", pct(m.gross_yield_pct))
        c2[1].metric("1% rule", "Yes" if m.meets_one_percent_rule else "No")
        c2[2].metric("Cap rate", pct(m.cap_rate_pct))

    # ===================== CAN YOU AFFORD IT (traffic light) =====================
    _render_afford(l, occupancy, loan_type, band, rf, mc=mc, hoa_val=hoa_val)

    # ===================== AGENT CONTACT =====================
    _render_agent_contact(l)

    st.markdown(dv.footer_note(), unsafe_allow_html=True)
    st.markdown(
        f"<div style='background:{dv.T.TV_TEAL_SOFT};border-radius:12px;padding:12px 16px;"
        f"margin:8px 0 6px'>{ic('info',18,dv.T.TV_TEAL)} New to home-buying words? "
        f"<a href='{glossary.LEARN_URL_PUBLIC}' target='_blank' "
        f"style='color:{dv.T.TV_TEAL};font-weight:700'>Learn the basics →</a></div>",
        unsafe_allow_html=True)
    return


def _facts_inline(l) -> str:
    return (f"{ic('beds')} {number(l.beds)} bd &nbsp; {ic('baths')} {number(l.baths)} ba "
            f"&nbsp; {ic('sqft')} {number(l.sqft)} sqft &nbsp; "
            f"{ic('clock')} {dom_label(l.days_on_market)} &nbsp; "
            f"{ic('location')} {l.city} {l.zip_code}")


def _render_foreclosure_detail(row) -> None:
    """The simpler bank-owned/foreclosure detail (no beds/baths/rent/afford)."""
    l = row["listing"]
    val = row["value"]
    st.markdown(_photo_placeholder(), unsafe_allow_html=True)
    st.markdown(f"<div class='price'>{money(l.list_price)}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='addr'>{l.address or '—'}</div>", unsafe_allow_html=True)
    demo = " <span class='sampletag'>demo</span>" if row.get("demo_foreclosure") else ""
    st.markdown(_bank_badge() + demo, unsafe_allow_html=True)
    st.markdown(_discount_html(val, l.list_price), unsafe_allow_html=True)
    st.markdown(f"<div class='facts'>{ic('gavel',16,'#344054')} Sold as-is — may "
                "have liens or auction rules. Beds/baths aren't in foreclosure "
                "data; verify everything before bidding.</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='facts'>{ic('location')} {l.city} {l.zip_code}</div>",
                unsafe_allow_html=True)
    link = gmaps_link(l.address)
    if link:
        st.markdown(f"<a href='{link}' target='_blank' style='color:{DEEP_GREEN}'>"
                    f"{ic('location')} Open in Google Maps</a>", unsafe_allow_html=True)
    links = " · ".join(f"<a href='{u}' target='_blank' style='color:{DEEP_GREEN}'>"
                       f"{n}</a>" for n, u in GOV_LINKS)
    st.markdown(f"<div class='facts' style='margin-top:6px'>{ic('link',15,MUTED)} "
                f"Also check free government foreclosures: {links}</div>",
                unsafe_allow_html=True)
    st.divider()
    st.markdown(_score_badge(row["score"]), unsafe_allow_html=True)
    _render_agent_contact(l)


# ===========================================================================
# FEED
# ===========================================================================
def render_feed(rows, sample_mode) -> None:
    logo_title = "U.S. deals"
    st.markdown(f"<div class='app-header'>{ic('home',20)} {logo_title}"
                "<span style='font-weight:400;opacity:.85'> · best deals first"
                "</span></div>", unsafe_allow_html=True)

    if sample_mode:
        st.warning("Showing SAMPLE listings for design preview — no live data used.",
                   icon="🎨")

    # --- Search any U.S. city or ZIP (cache-first; new areas load on demand) ---
    q = st.text_input("Search any U.S. city or ZIP",
                      placeholder="e.g.  Austin, TX   or   78701",
                      key="area_query").strip()

    with st.expander("Filters"):
        good_only = st.toggle("Good deals only (score ≥ "
                              f"{settings.scoring.get('good_deal_threshold',70)})")
        fc_only = st.toggle("Bank-owned / foreclosures only")

    shown = [r for r in rows
             if _matches_area(r["listing"], q)
             and (not good_only or r["score"].is_good_deal)
             and (not fc_only or r.get("foreclosure"))]
    shown.sort(key=lambda r: -r["score"].total)
    st.markdown(f"<div class='facts' style='margin:6px 0'>{ic('search')} "
                f"{len(shown)} home(s)" + (f" for “{q}”" if q else "") + "</div>",
                unsafe_allow_html=True)
    if any(r.get("demo_foreclosure") for r in shown):
        st.caption("Bank-owned examples are DEMO placeholders — live foreclosure data "
                   "connects after the $1-trial key is added.")

    if q and not shown:          # searched an area we haven't cached yet
        _offer_area_load(q)

    for r in shown:
        l, score = r["listing"], r["score"]
        with st.container(border=True):
            st.markdown(_photo_placeholder(), unsafe_allow_html=True)
            if r.get("foreclosure"):
                demo = (" <span class='sampletag'>demo</span>"
                        if r.get("demo_foreclosure") else "")
                st.markdown(_bank_badge() + demo, unsafe_allow_html=True)
                st.markdown(_score_badge(score), unsafe_allow_html=True)
                st.markdown(f"<div class='price'>{money(l.list_price)}</div>",
                            unsafe_allow_html=True)
                st.markdown("<div class='facts' style='margin-top:-4px'>opening bid / "
                            "list price</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='addr'>{ic('location',16,MUTED)} "
                            f"{l.address or '—'}</div>", unsafe_allow_html=True)
                st.markdown(_discount_html(r["value"], l.list_price),
                            unsafe_allow_html=True)
                st.markdown(f"<div class='facts'>{ic('gavel')} Sold as-is — verify "
                            "details</div>", unsafe_allow_html=True)
            else:
                st.markdown(_score_badge(score), unsafe_allow_html=True)
                st.markdown(f"<div class='price'>{money(l.list_price)}</div>",
                            unsafe_allow_html=True)
                st.markdown(f"<div class='addr'>{ic('location',16,MUTED)} "
                            f"{l.address or '—'}</div>", unsafe_allow_html=True)
                st.markdown(_facts_html(l), unsafe_allow_html=True)
                rs = " <span class='sampletag'>sample</span>" if r["rent_sample"] else ""
                st.markdown(f"<div class='facts'>{ic('rent')} ~{money(r['rent'])}/mo "
                            f"rent{rs}</div>", unsafe_allow_html=True)
                rb = _risk_badges(r.get("risk"))
                if rb:
                    st.markdown(rb, unsafe_allow_html=True)
            if st.button("See details", key=f"o_{l.id}", use_container_width=True,
                         type="primary"):
                st.session_state.open_id = l.id
                st.rerun()

    st.divider()
    st.caption("Deal scores are ESTIMATES — a screening tool, not financial advice. "
               "Nationwide across the U.S.")


# ---- Router ----
rows, sample_mode = sample_data.display_rows()
by_id = {r["listing"].id: r for r in rows}
if st.session_state.open_id and st.session_state.open_id in by_id:
    render_detail(by_id[st.session_state.open_id])
else:
    render_feed(rows, sample_mode)

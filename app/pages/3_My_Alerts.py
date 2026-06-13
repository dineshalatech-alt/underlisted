"""
My Alerts — saved searches + deal alerts (the retention engine).

Save a search ("cheap Sacramento homes under $300k, score >= 70"); the background
worker matches new deals and records them here. Email sending is DORMANT until a
(free) email account is added — the save/match logic is fully real.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402

from config.settings import settings  # noqa: E402
from src.cache import db  # noqa: E402
from app.assets.theme import APP_CSS, PRIMARY_GREEN  # noqa: E402
from app.icons import TABLER_CSS, ic  # noqa: E402
from app.helpers import money, favicon_path  # noqa: E402

st.set_page_config(page_title="My Alerts", page_icon=favicon_path(), layout="centered")
st.markdown(APP_CSS + TABLER_CSS, unsafe_allow_html=True)

user = settings.current_user_id

st.markdown(f"## {ic('bolt',26,PRIMARY_GREEN)} My deal alerts", unsafe_allow_html=True)
if settings.has_resend:
    st.caption("Save a search and we'll **email you** the moment a matching deal "
               "appears. Add your email below to get alerts.")
else:
    st.caption("Save a search and we'll watch for matching deals. Email sending turns "
               "on once a free email account is added — for now, matches show below.")

with st.form("new_alert", clear_on_submit=True):
    name = st.text_input("Name this alert", placeholder="Cheap Sacramento homes")
    email = st.text_input("Email me at (optional)",
                          placeholder="you@example.com",
                          help="We'll email matching deals here. Leave blank to just "
                               "see them on this page.")
    c = st.columns(2)
    city = c[0].text_input("City (optional)")
    zipc = c[1].text_input("ZIP (optional)")
    c2 = st.columns(2)
    max_price = c2[0].number_input("Max price ($, 0 = any)", min_value=0, value=0,
                                   step=10000)
    min_score = c2[1].slider("Minimum deal score", 0, 100, 70)
    fconly = st.toggle("Foreclosures / bank-owned only")
    if st.form_submit_button("Save alert", type="primary"):
        if not name.strip():
            st.warning("Give your alert a name.")
        else:
            db.add_saved_search(user, name.strip(), city.strip() or None,
                                zipc.strip() or None, max_price or None, min_score,
                                fconly, email.strip() or None)
            if email.strip() and not settings.has_resend:
                st.success("Saved. We'll email you once the email service is switched "
                           "on — for now, matches show below.")
            elif email.strip():
                st.success("Saved. We'll email you when a matching deal appears.")
            else:
                st.success("Saved. The worker will start matching deals on its next run.")
            st.rerun()

st.divider()
searches = db.list_saved_searches(user)
if not searches:
    st.info("No alerts yet — create one above.")
for s in searches:
    with st.container(border=True):
        st.markdown(f"**{s['name']}**")
        bits = []
        if s.get("city"):
            bits.append(s["city"])
        if s.get("zip_code"):
            bits.append("ZIP " + str(s["zip_code"]))
        if s.get("max_price"):
            bits.append("≤ " + money(s["max_price"]))
        bits.append(f"score ≥ {s.get('min_score', 0)}")
        if s.get("foreclosures_only"):
            bits.append("foreclosures only")
        if s.get("email"):
            bits.append(f"📧 {s['email']}")
        st.caption(" · ".join(bits))
        if st.button("Delete", key="del_" + s["id"]):
            db.delete_saved_search(s["id"])
            st.rerun()

st.divider()
st.subheader("Recent matches")
alerts = db.list_alerts(user)
if not alerts:
    st.caption("No matches yet — the background worker fills these in as deals appear.")
for a in alerts[:20]:
    st.markdown(f"{ic('home',14,PRIMARY_GREEN)} **{a['address'] or '—'}** — "
                f"score {a['score']}", unsafe_allow_html=True)

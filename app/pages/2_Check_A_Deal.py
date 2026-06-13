"""
Free 'Is it a good deal?' page — the top-of-funnel. Anyone can type a city/ZIP and
see the best-scored homes there, free, no signup. Cache-first (no API calls here).
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402

from app.assets.theme import APP_CSS, PRIMARY_GREEN, MUTED, score_color  # noqa: E402
from app.icons import TABLER_CSS, ic  # noqa: E402
from app.helpers import money, favicon_path  # noqa: E402
from app import sample_data  # noqa: E402

st.set_page_config(page_title="Is it a good deal?", page_icon=favicon_path(),
                   layout="centered")
st.markdown(APP_CSS + TABLER_CSS, unsafe_allow_html=True)

st.markdown(f"## {ic('gauge',26,PRIMARY_GREEN)} Is it a good deal?", unsafe_allow_html=True)
st.caption("Type a U.S. city or ZIP — see the best-scored homes there, free. No signup.")

q = st.text_input("City or ZIP", placeholder="e.g.  Sacramento   or   95827").strip()


def _match(l, q: str) -> bool:
    ql = q.lower()
    if ql.isdigit():
        return (l.zip_code or "").startswith(ql)
    return ql.split(",")[0].strip() in (l.city or "").lower()


if not q:
    st.info("Enter a city or ZIP to check.")
else:
    rows, _ = sample_data.display_rows()
    shown = sorted([r for r in rows if _match(r["listing"], q)],
                   key=lambda r: -r["score"].total)
    if not shown:
        st.info(f"No homes cached for “{q}” yet. Open **Browse Deals** and use the "
                "“Load” button to fetch that area.")
    else:
        top = shown[0]
        l, s = top["listing"], top["score"]
        c = score_color(s.total)
        v = top["value"].avm
        disc = ((v - l.list_price) / v * 100) if v and l.list_price else None
        verdict = ("Great deal" if s.total >= 70 else
                   "Worth a look" if s.total >= 45 else "Below average")
        st.markdown(
            f"<div style='display:flex;gap:16px;align-items:center;margin-top:6px'>"
            f"<div style='background:{c};color:#fff;font-weight:800;font-size:1.8rem;"
            f"border-radius:16px;padding:12px 20px'>{s.total}</div>"
            f"<div><div style='font-size:1.3rem;font-weight:800;color:{c}'>{verdict}</div>"
            f"<div class='muted'>Top home in {q}</div></div></div>", unsafe_allow_html=True)
        st.markdown(f"### {money(l.list_price)} — {l.address or '—'}")
        if disc and disc > 0:
            st.markdown(f"{ic('value',18,PRIMARY_GREEN)} Listed **{disc:.0f}% below** "
                        "estimated value.", unsafe_allow_html=True)
        if st.button("See full details, cash needed & risk →", type="primary"):
            st.session_state.open_id = l.id
            st.switch_page("pages/0_Browse_Deals.py")
        if len(shown) > 1:
            st.divider()
            st.markdown(f"**{len(shown) - 1} more** in {q}:")
            for r in shown[1:6]:
                rl = r["listing"]
                st.markdown(f"- {ic('home',14,MUTED)} **{money(rl.list_price)}** — "
                            f"{rl.address or '—'} <span style='color:"
                            f"{score_color(r['score'].total)};font-weight:700'>score "
                            f"{r['score'].total}</span>", unsafe_allow_html=True)

st.divider()
st.caption("Estimates only — a screening tool, not advice.")

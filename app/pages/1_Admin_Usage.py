"""
Admin / Usage — watch your API cost as customers grow.

Shows: billable calls by source, image fetches, the cache HIT RATE (proof the
shared cache is saving you calls), estimated $ spent, and per-user usage vs the
monthly cap. Everything here reads counters from the local cache — it makes no
API calls.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402

from config.settings import settings  # noqa: E402
from src.cache import db, backend  # noqa: E402
from src import cost  # noqa: E402
from src.data_sources import rentcast  # noqa: E402
from worker import refresh_worker  # noqa: E402
from app.assets.theme import APP_CSS  # noqa: E402

st.set_page_config(page_title="Admin / Usage", page_icon="💰", layout="wide")
st.markdown(APP_CSS, unsafe_allow_html=True)
st.markdown('<div class="app-header">💰 Admin / Usage</div>', unsafe_allow_html=True)

st.caption(f"Reading from **{backend.backend_name()}** (shared cache). "
           "This page makes no API calls.")

# --- Top-line numbers ------------------------------------------------------
usage = db.usage_summary()
stats = db.cache_stats()
costs = cost.estimated_cost()

total_calls = costs["total"]["calls"]
total_cost = costs["total"]["cost"]
image_fetches = usage.get("streetview", 0) + usage.get("aerial", 0)
overall_hit = stats["overall"]["hit_rate"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Billable calls", f"{total_calls:,}")
c2.metric("Image fetches", f"{image_fetches:,}")
c3.metric("Cache hit rate", f"{overall_hit * 100:.0f}%")
c4.metric("Est. spend", f"${total_cost:,.2f}")

st.caption(f"Last sync: {rentcast.last_sync_time() or 'never'}")
st.divider()

# --- Background worker -----------------------------------------------------
st.subheader("Background worker")
st.caption("The automated job that refreshes the shared cache on a schedule, so "
           "users only ever read from cache. You can also trigger it manually — "
           "it's safe to run repeatedly (it won't duplicate data or double-bill).")

if st.button("▶️ Run worker now", type="primary"):
    with st.status("Running worker…", expanded=True) as box:
        result = refresh_worker.run_once(progress=lambda m: box.write(m))
        box.update(label="Worker finished", state="complete")
    st.success(
        f"new {result['new_count']} · updated {result['updated_count']} · "
        f"estimates {result['estimates_updated']} · billable calls "
        f"{result['billable_calls']} · status {result['status']}")

history = db.worker_run_history(limit=20)
if history:
    rows = [{
        "Started": (h.get("started_at") or "")[:19].replace("T", " "),
        "Status": h.get("status"),
        "Cities": h.get("cities"),
        "New": h.get("new_count"),
        "Updated": h.get("updated_count"),
        "Estimates": h.get("estimates_updated"),
        "Billable calls": h.get("billable_calls"),
    } for h in history]
    st.dataframe(rows, use_container_width=True, hide_index=True)
    notes = [h for h in history if (h.get("notes") or "").strip()]
    if notes:
        with st.expander("Run notes / errors"):
            for h in notes:
                st.write(f"**{(h.get('started_at') or '')[:19]}** — {h['notes']}")
else:
    st.info("No worker runs yet. Click **Run worker now**, or schedule it "
            "(see README).")

st.divider()

# --- Billable calls + cost by source --------------------------------------
st.subheader("Billable calls & estimated cost, by source")
if usage:
    rows = []
    for source, info in costs.items():
        if source == "total":
            continue
        rows.append({
            "Source": source,
            "Billable calls": info["calls"],
            "$ per call": f"${info['unit']:.4f}",
            "Est. cost": f"${info['cost']:.2f}",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.caption("Edit `$ per call` values in `config/cache.yaml` to match your plan.")
else:
    st.info("No billable calls recorded yet.")

st.divider()

# --- Cache hit rate (proof the shared cache works) -------------------------
st.subheader("Cache hit rate by source")
st.caption("A HIT means we served cached data and did NOT call the API. Higher is "
           "cheaper. This is where shared caching saves you money as users grow.")
hit_rows = []
for source, s in stats.items():
    if source == "overall":
        continue
    denom = s["hits"] + s["misses"]
    hit_rows.append({
        "Source": source,
        "Hits (free)": s["hits"],
        "Misses (fetched)": s["misses"],
        "Hit rate": f"{s['hit_rate'] * 100:.0f}%" if denom else "—",
    })
if hit_rows:
    st.dataframe(hit_rows, use_container_width=True, hide_index=True)
    o = stats["overall"]
    st.success(f"Overall: {o['hits']} hits vs {o['misses']} misses → "
               f"**{o['hit_rate'] * 100:.0f}%** served from cache.")
else:
    st.info("No cache activity yet. Open some listings to populate this.")

st.divider()

# --- Per-user monthly cap --------------------------------------------------
st.subheader("Per-user monthly usage")
cap = cost.cap_status()
st.progress(min(cap["pct"] / 100, 1.0),
            text=f"{cap['used']} / {cap['cap']} lookups this month "
                 f"({cap['pct']:.0f}%)")
st.caption(f"Cap is `monthly_lookups_per_user` in `config/cache.yaml` "
           f"(currently {settings.monthly_lookup_cap}). Today this tracks the "
           f"single local user; it becomes truly per-user once accounts exist.")

st.divider()
st.subheader("Cache freshness windows (TTL)")
ttl = settings.cache.get("ttl", {})
st.json(ttl)
st.caption("Listings refresh ~daily, value/rent ~weekly, images ~never — because "
           "a building's exterior doesn't change. Edit in `config/cache.yaml`.")

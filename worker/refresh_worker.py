"""
Background worker — the automated job that keeps the shared cache fresh.

This is NOT an AI agent. It's a plain scheduled job. On each run it:
  1. Incrementally fetches new/changed RentCast listings for your configured cities
     (edit the list in config/cities.yaml — nationwide, multi-state).
  2. Refreshes value & rent estimates that have gone stale (per the expiry windows).
  3. Writes everything to the SHARED cache. Users only ever READ from that cache.

It does NOT fetch images by default (photos stay lazy/on-demand) unless you set
worker.prewarm_photos: true in config/cache.yaml.

Run it locally:
    python -m worker.refresh_worker            # run once now (safe to repeat)
    python -m worker.refresh_worker --full     # full refresh (catches old-home changes)
    python -m worker.refresh_worker --loop      # keep running on the schedule

Re-running is safe (idempotent): listings upsert in place, and cached estimates
within their freshness window are reused — never re-billed.
"""

from __future__ import annotations

import argparse
import sys
import time
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings  # noqa: E402
from src.cache import backend, db  # noqa: E402
from src.data_sources import (  # noqa: E402
    rentcast, streetview, foreclosure, risk, market, mortgage_rates)
from src.notify import email_sender  # noqa: E402


def _wcfg() -> dict:
    return settings.cache.get("worker", {})


def _log(progress, msg: str):
    line = f"[worker] {msg}"
    print(line, flush=True)
    if progress:
        progress(line)


def run_once(*, full: bool = False, progress=None) -> dict:
    """Do one refresh cycle and record it in worker_runs. Returns a summary."""
    cfg = _wcfg()
    run_id = db.now_iso()  # unique per run -> idempotent record
    started = run_id
    calls_before = db.total_billable_calls()

    db.record_worker_run({
        "run_id": run_id, "started_at": started, "finished_at": None,
        "status": "running", "cities": 0, "new_count": 0, "updated_count": 0,
        "estimates_updated": 0, "billable_calls": 0, "notes": "",
    })

    _log(progress, f"Backend: {backend.backend_name()}")
    notes: list[str] = []
    estimates_updated = 0
    status = "ok"

    # 1) Listings — incremental unless --full.
    try:
        _log(progress, "Refreshing listings...")
        summary = rentcast.sync_listings(
            limit_per_area=int(cfg.get("max_listings_per_city", 200)),
            incremental=not full,
            progress=lambda m: _log(progress, m),
        )
        cities = len({c for c, _, _ in rentcast._iter_targets()})
        for err in summary["errors"]:
            notes.append(err)
    except Exception as exc:  # keep the worker alive; record the failure
        status = "error"
        notes.append(f"listings: {exc}")
        summary = {"new": 0, "updated": 0, "total_seen": 0, "price_drops": []}
        cities = 0

    # 1b) Foreclosure / bank-owned listings — separate source, same shared cache.
    #     Skipped silently until FORECLOSURE_API_KEY is set. A foreclosure hiccup
    #     is noted but does NOT fail the whole run.
    if (cfg.get("sync_foreclosure", True) and settings.has_foreclosure
            and status != "error"):
        try:
            _log(progress, "Refreshing foreclosure listings...")
            fc = foreclosure.sync_listings(
                limit_per_area=int(cfg.get("max_foreclosure_per_city", 100)),
                incremental=not full,
                progress=lambda m: _log(progress, m),
            )
            summary["new"] += fc["new"]
            summary["updated"] += fc["updated"]
            for err in fc["errors"]:
                notes.append(f"foreclosure {err}")
        except Exception as exc:
            notes.append(f"foreclosure: {exc}")

    # 1c) Risk flags — FREE FEMA fire/flood for cached listings (not billable).
    if cfg.get("update_risk", True) and status != "error":
        budget = int(cfg.get("max_risk_per_run", 300))
        done = 0
        _log(progress, f"Updating FEMA fire/flood risk (up to {budget})...")
        try:
            for listing in rentcast.load_cached_listings():
                if listing.latitude is None or listing.longitude is None:
                    continue
                try:
                    risk.get_risk(listing, cache_only=False)  # free; caches result
                except Exception as exc:
                    notes.append(f"risk {listing.id}: {exc}")
                done += 1
                if done >= budget:
                    break
        except Exception as exc:
            notes.append(f"risk loop: {exc}")

    # 1d) Market context — FREE FHFA ZIP price-trend file (refreshes ~yearly).
    if cfg.get("update_market", True) and status != "error":
        try:
            n = market.ensure_fresh()
            if n:
                _log(progress, f"Refreshed FHFA price-trend data ({n} ZIPs).")
        except Exception as exc:
            notes.append(f"market: {exc}")

    # 1d2) Mortgage rate — FREE Freddie Mac PMMS (weekly 30-yr), powers true monthly cost.
    if cfg.get("update_mortgage_rate", True) and status != "error":
        try:
            info = mortgage_rates.ensure_fresh(
                max_age_days=int(cfg.get("mortgage_rate_max_age_days", 7)))
            if info:
                _log(progress, f"Mortgage rate refreshed: {info.get('rate30')}% "
                               f"({info.get('source')}, as of {info.get('as_of')}).")
        except Exception as exc:
            notes.append(f"mortgage_rate: {exc}")

    # 1e) Saved-search alerts — match cached deals, record hits (email dormant).
    if cfg.get("update_alerts", True) and status != "error":
        try:
            from app import sample_data as _sd
            rows, _ = _sd.display_rows()
            new_total = 0
            for s in db.all_saved_searches():
                for r in rows:
                    l = r["listing"]
                    if s.get("city") and s["city"].lower() not in (l.city or "").lower():
                        continue
                    if s.get("zip_code") and not (l.zip_code or "").startswith(str(s["zip_code"])):
                        continue
                    if s.get("max_price") and l.list_price and l.list_price > s["max_price"]:
                        continue
                    if s.get("min_score") and r["score"].total < s["min_score"]:
                        continue
                    if s.get("foreclosures_only") and not r.get("foreclosure"):
                        continue
                    if db.record_alert_match(s["id"], l.id, l.address, r["score"].total,
                                             db.now_iso()):
                        new_total += 1
                db.set_search_checked(s["id"], db.now_iso())
            if new_total:
                tail = ("" if settings.has_resend
                        else " (email dormant until RESEND_API_KEY is added)")
                _log(progress, f"Alerts: {new_total} new matching deal(s) recorded{tail}.")
        except Exception as exc:
            notes.append(f"alerts: {exc}")

    # 1f) Email the new matches — one digest per saved search that has an email.
    #     Only runs when a Resend key is present; otherwise it's a no-op.
    if (cfg.get("send_alert_emails", True) and settings.has_resend
            and status != "error"):
        try:
            pending = db.unnotified_matches()
            # Group matches by the search they belong to.
            by_search: dict[str, dict] = {}
            for m in pending:
                g = by_search.setdefault(
                    m["search_id"],
                    {"email": m["email"], "name": m["search_name"], "items": []})
                g["items"].append(m)

            sent = 0
            for sid, g in by_search.items():
                res = email_sender.send_alert_digest(
                    g["email"], g["name"], g["items"],
                    app_url=settings.cache.get("app_url"))
                if res.get("ok"):
                    for m in g["items"]:
                        db.mark_notified(sid, m["listing_id"])
                    sent += 1
                else:
                    notes.append(f"email {sid}: {res.get('error') or res.get('reason')}")
            if sent:
                _log(progress, f"Alerts: emailed {sent} digest(s).")
        except Exception as exc:
            notes.append(f"email: {exc}")

    # 2) Value/rent — only stale ones bill (TTL), capped per run.
    if cfg.get("update_value_rent", True) and status != "error":
        budget = int(cfg.get("max_estimates_per_run", 50))
        _log(progress, f"Refreshing stale value/rent (up to {budget} properties)...")
        try:
            for listing in rentcast.load_cached_listings():
                calls_at_start = db.total_billable_calls()
                try:
                    # Each returns instantly from cache if still fresh (no bill);
                    # only stale estimates actually call RentCast.
                    rentcast.get_value_estimate(listing, count_against_user=False)
                    rentcast.get_rent_estimate(listing, count_against_user=False)
                except Exception as exc:
                    notes.append(f"estimate {listing.id}: {exc}")
                    continue
                if db.total_billable_calls() > calls_at_start:
                    estimates_updated += 1  # this property had >=1 stale estimate
                if estimates_updated >= budget:  # per-run cost guard
                    _log(progress, f"Hit estimate budget ({budget}); stopping.")
                    break
        except Exception as exc:
            notes.append(f"value/rent loop: {exc}")

    # 3) Optional photo pre-warm (off by default — images stay lazy).
    if cfg.get("prewarm_photos", False) and status != "error":
        top_n = int(cfg.get("prewarm_top_n", 0))
        if top_n > 0:
            _log(progress, f"Pre-warming photos for {top_n} newest listings...")
            for listing in rentcast.load_cached_listings(limit=top_n):
                try:
                    streetview.get_photo(listing, count_against_user=False)
                except Exception as exc:
                    notes.append(f"photo {listing.id}: {exc}")

    finished = db.now_iso()
    billable = db.total_billable_calls() - calls_before
    if notes and status == "ok":
        status = "ok_with_notes"  # finished, but some sources logged issues
    result = {
        "run_id": run_id, "started_at": started, "finished_at": finished,
        "status": status, "cities": cities, "new_count": summary["new"],
        "updated_count": summary["updated"], "estimates_updated": estimates_updated,
        "billable_calls": billable, "notes": " | ".join(notes)[:1000],
    }
    try:
        db.record_worker_run(result)
    except Exception as exc:
        _log(progress, f"WARNING: could not record run summary: {exc}")
    _log(progress, f"Done. new={summary['new']} updated={summary['updated']} "
                   f"estimates={estimates_updated} billable_calls={billable} "
                   f"status={status}")
    if notes:
        _log(progress, "Notes: " + " | ".join(notes)[:1500])
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Underlisted refresh worker.")
    parser.add_argument("--loop", action="store_true",
                        help="Keep running, refreshing every schedule_hours.")
    parser.add_argument("--full", action="store_true",
                        help="Full refresh (not incremental) this run.")
    args = parser.parse_args()

    if not args.loop:
        try:
            run_once(full=args.full)
        except Exception:
            # Never crash the scheduled job on an unexpected error — print the
            # full traceback for diagnosis, but exit 0 so the schedule keeps
            # running and partial data already saved is kept. Details also land
            # in the worker_runs notes (Admin / Usage page).
            print("[worker] FATAL — run did not complete cleanly:", flush=True)
            traceback.print_exc()
        return 0

    hours = float(_wcfg().get("schedule_hours", 24))
    print(f"[worker] Loop mode: refreshing every {hours} h. Ctrl+C to stop.")
    while True:
        run_once(full=args.full)
        print(f"[worker] Sleeping {hours} h...", flush=True)
        time.sleep(hours * 3600)


if __name__ == "__main__":
    raise SystemExit(main())

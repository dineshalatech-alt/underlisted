"""
Background worker — the automated job that keeps the shared cache fresh.

This is NOT an AI agent. It's a plain scheduled job. On each run it:
  1. Incrementally fetches new/changed RentCast listings for your NorCal cities.
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
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings  # noqa: E402
from src.cache import backend, db  # noqa: E402
from src.data_sources import rentcast, streetview  # noqa: E402


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

    # 2) Value/rent — only stale ones bill (TTL), capped per run.
    if cfg.get("update_value_rent", True) and status != "error":
        budget = int(cfg.get("max_estimates_per_run", 50))
        _log(progress, f"Refreshing stale value/rent (up to {budget} properties)...")
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
                estimates_updated += 1  # this property had at least one stale estimate
            if estimates_updated >= budget:  # per-run cost guard
                _log(progress, f"Hit estimate budget ({budget}); stopping.")
                break

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
    result = {
        "run_id": run_id, "started_at": started, "finished_at": finished,
        "status": status, "cities": cities, "new_count": summary["new"],
        "updated_count": summary["updated"], "estimates_updated": estimates_updated,
        "billable_calls": billable, "notes": " | ".join(notes)[:1000],
    }
    db.record_worker_run(result)
    _log(progress, f"Done. new={summary['new']} updated={summary['updated']} "
                   f"estimates={estimates_updated} billable_calls={billable} "
                   f"status={status}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="NorCal Deal Finder refresh worker.")
    parser.add_argument("--loop", action="store_true",
                        help="Keep running, refreshing every schedule_hours.")
    parser.add_argument("--full", action="store_true",
                        help="Full refresh (not incremental) this run.")
    args = parser.parse_args()

    if not args.loop:
        run_once(full=args.full)
        return 0

    hours = float(_wcfg().get("schedule_hours", 24))
    print(f"[worker] Loop mode: refreshing every {hours} h. Ctrl+C to stop.")
    while True:
        run_once(full=args.full)
        print(f"[worker] Sleeping {hours} h...", flush=True)
        time.sleep(hours * 3600)


if __name__ == "__main__":
    raise SystemExit(main())

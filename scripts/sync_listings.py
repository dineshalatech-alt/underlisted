"""
Fetch fresh listings from RentCast into the local cache — from the command line.

Run it from the project folder (with your .venv turned on):

    python scripts/sync_listings.py            # full refresh
    python scripts/sync_listings.py --days 7   # incremental: last 7 days only

You normally won't need this — the app has a "Refresh from RentCast" button —
but it's handy for testing or scheduling later.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Let this script find the project's packages.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_sources import rentcast  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync RentCast sale listings.")
    parser.add_argument(
        "--days", type=int, default=None,
        help="Only fetch listings this many days old or newer (incremental).",
    )
    parser.add_argument(
        "--limit", type=int, default=rentcast.MAX_LIMIT,
        help="Max listings per city/zip (default 500).",
    )
    args = parser.parse_args()

    print("Syncing listings from RentCast…\n")
    summary = rentcast.sync_listings(
        limit_per_area=args.limit,
        days_old=args.days,
        progress=lambda msg: print("  " + msg),
    )

    print("\n--- Summary ---")
    print(f"  Listings seen : {summary['total_seen']}")
    print(f"  New           : {summary['new']}")
    print(f"  Updated       : {summary['updated']}")
    print(f"  Price drops   : {len(summary['price_drops'])}")
    for drop in summary["price_drops"]:
        print(f"     ↓ {drop['address']}: ${drop['old']:,.0f} -> ${drop['new']:,.0f}")
    if summary["errors"]:
        print("  Errors:")
        for err in summary["errors"]:
            print(f"     ! {err}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

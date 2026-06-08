"""
Cost & per-user cap helpers.

Turns the raw counters in the cache into the numbers the sidebar and admin view
show: estimated $ spent, and how close a user is to their monthly lookup cap.
"""

from __future__ import annotations

from config.settings import settings
from src.cache import db


def cap_status(user_id: str | None = None) -> dict:
    """How many billable lookups this user has used this month vs. the cap."""
    user_id = user_id or settings.current_user_id
    used = db.user_lookup_count(user_id)
    cap = settings.monthly_lookup_cap
    pct = (used / cap * 100) if cap else 0.0
    return {
        "used": used,
        "cap": cap,
        "pct": pct,
        "near": pct >= settings.lookup_warn_pct,
        "over": used >= cap,
        "remaining": max(cap - used, 0),
    }


def can_spend(user_id: str | None = None) -> bool:
    """False once the user has hit their monthly cap (protects your bill)."""
    return not cap_status(user_id)["over"]


def estimated_cost() -> dict:
    """
    Estimated $ spent so far, by source, using cost_estimates_usd from cache.yaml.
    Returns {source: {"calls": n, "cost": $}, ...} plus a "total" key.
    """
    usage = db.usage_summary()
    breakdown: dict = {}
    total = 0.0
    for source, calls in usage.items():
        unit = settings.cost_per_call(source)
        cost = calls * unit
        total += cost
        breakdown[source] = {"calls": calls, "unit": unit, "cost": cost}
    breakdown["total"] = {"calls": sum(usage.values()), "cost": total}
    return breakdown

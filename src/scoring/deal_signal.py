"""
The simple, beginner-friendly "good deal" signal used by the feed.

It answers one plain question: is this home listed below, around, or above its
estimated value? No jargon, no 0-100 math yet — that's the later Deal Score phase,
which will build on this same idea. Deliberately based ONLY on price-vs-estimated-
value (no demographic or "neighborhood quality" inputs — Fair Housing).
"""

from __future__ import annotations

from typing import Optional

from config.settings import settings


def classify(value_vs_list_pct: Optional[float]) -> dict:
    """
    Turn the value-vs-list percentage into a plain-language badge.

    `value_vs_list_pct`: positive = listed ABOVE estimated value,
                         negative = listed BELOW estimated value.

    Returns: {level, label, color, plain}
      color is a theme badge class: 'good' | 'warn' | 'bad' | 'muted'.
    """
    cfg = settings.scoring.get("simple_deal_signal", {})
    great = float(cfg.get("great_below_pct", 8))
    good = float(cfg.get("good_below_pct", 3))

    if value_vs_list_pct is None:
        return {"level": "unknown", "label": "Checking…", "color": "muted",
                "plain": "We don't have an estimate for this home yet."}

    below = -value_vs_list_pct  # how far BELOW estimated value (positive = good)

    if below >= great:
        return {"level": "great", "label": "Great deal", "color": "good",
                "plain": f"Listed about {below:.0f}% below its estimated value — "
                         "that can be a strong sign."}
    if below >= good:
        return {"level": "good", "label": "Good deal", "color": "good",
                "plain": f"Listed about {below:.0f}% below its estimated value."}
    if below >= -good:
        return {"level": "fair", "label": "Around market", "color": "warn",
                "plain": "Listed close to its estimated value."}
    return {"level": "high", "label": "Above market", "color": "bad",
            "plain": f"Listed about {abs(below):.0f}% above its estimated value."}

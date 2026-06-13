"""Small display helpers shared by the screens (formatting money, numbers, etc.)."""

from __future__ import annotations

import base64
import random
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

_ASSETS = Path(__file__).resolve().parent / "assets"


# --- Friendly "please wait" messages ---------------------------------------
# Shown while a live area search is loading, so the wait feels warm and human
# (like Streamlit's own "your app is in the oven" screen). {q} = what they typed.
_WAIT_MESSAGES = [
    "🍳 Cooking up the best deals in {q}…",
    "🔎 Scanning {q} for under-priced homes…",
    "🏡 Lining up homes in {q} — best deals first…",
    "🧮 Crunching the real cost & cash for {q}…",
    "📬 Fetching fresh listings for {q}…",
    "✨ Hunting for hidden gems in {q}…",
]

# A useful homebuyer tip to read while they wait — teaches the app's value.
_WAIT_TIPS = [
    "💡 A green score (70+) means a home looks well under its estimated value.",
    "💡 We flag fire & flood risk — pricey insurance can sink a 'good deal'.",
    "💡 'Cash to close' = down payment + closing costs. Reserves you keep.",
    "💡 Homes listed a long time often have the most room to negotiate.",
    "💡 Always double-check estimates with a licensed lender and agent.",
    "💡 The deal score is a screening guide — a starting point, not a promise.",
]


def wait_message(q: str) -> str:
    """A warm, randomized 'loading' line for a searched area."""
    q = (q or "your area").strip() or "your area"
    return random.choice(_WAIT_MESSAGES).format(q=q)


def random_tip() -> str:
    """A short homebuyer tip to show under the spinner while waiting."""
    return random.choice(_WAIT_TIPS)


def favicon_path() -> str:
    p = _ASSETS / "favicon.png"
    return str(p) if p.exists() else "🏡"


def logo_data_uri() -> str:
    """Base64 data URI for the logo, so it embeds cleanly in HTML."""
    p = _ASSETS / "logo.png"
    if not p.exists():
        return ""
    enc = base64.b64encode(p.read_bytes()).decode()
    return f"data:image/png;base64,{enc}"


def gmaps_link(address: Optional[str]) -> Optional[str]:
    """A FREE Google Maps search link for an address — no API call, no cost."""
    if not address:
        return None
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(address)


def pct(value: Optional[float], digits: int = 1) -> str:
    """6.234 -> '6.2%'.  None -> '—'."""
    if value is None:
        return "—"
    try:
        return f"{float(value):.{digits}f}%"
    except (TypeError, ValueError):
        return "—"


def money(value: Optional[float]) -> str:
    """450000 -> '$450,000'.  None -> '—'."""
    if value is None:
        return "—"
    try:
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return "—"


def number(value: Optional[float], suffix: str = "") -> str:
    if value is None:
        return "—"
    try:
        f = float(value)
        text = f"{f:,.0f}" if f == int(f) else f"{f:,.1f}"
        return f"{text}{suffix}"
    except (TypeError, ValueError):
        return "—"


def beds_baths(beds: Optional[float], baths: Optional[float]) -> str:
    b = number(beds)
    ba = number(baths)
    return f"{b} bd · {ba} ba"


def dom_label(days: Optional[int]) -> str:
    if days is None:
        return "—"
    if days == 0:
        return "New today"
    if days == 1:
        return "1 day on market"
    return f"{days} days on market"

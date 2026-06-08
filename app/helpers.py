"""Small display helpers shared by the screens (formatting money, numbers, etc.)."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

_ASSETS = Path(__file__).resolve().parent / "assets"


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

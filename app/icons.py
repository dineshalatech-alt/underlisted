"""
ONE consistent icon set for the whole app: Tabler Icons (https://tabler.io/icons).

We load the Tabler web-font from a CDN once, then use `ic("beds")` anywhere to get
a crisp, consistent icon. One library, used everywhere — beds, baths, sqft, score,
price, rent, location, risk, filters, etc.

(Needs internet to fetch the icon font; if offline, icons simply don't render —
the layout still works.)
"""

from __future__ import annotations

from typing import Optional

# Injected once (it's part of the CSS each page already injects).
TABLER_CSS = (
    '<style>'
    '@import url("https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/'
    'dist/tabler-icons.min.css");'
    '.ti{vertical-align:-2px;line-height:1;}'
    '</style>'
)

# name -> Tabler class. (See the README/walkthrough for what each is used for.)
ICONS = {
    "beds": "ti-bed",
    "baths": "ti-bath",
    "sqft": "ti-ruler-2",
    "year": "ti-calendar",
    "score": "ti-gauge",
    "price": "ti-tag",
    "value": "ti-building-estate",
    "rent": "ti-cash",
    "location": "ti-map-pin",
    "fire": "ti-flame",
    "flood": "ti-droplet",
    "filter": "ti-filter",
    "search": "ti-search",
    "menu": "ti-menu-2",
    "home": "ti-home",
    "chevron": "ti-chevron-right",
    "info": "ti-info-circle",
    "wallet": "ti-wallet",          # cash to close
    "down": "ti-coins",             # down payment
    "closing": "ti-receipt",        # closing costs
    "reserves": "ti-pig-money",     # reserves
    "key": "ti-key",                # total cash to buy
    "check": "ti-circle-check",
    "star": "ti-star",
    "bolt": "ti-bolt",
    "shield": "ti-shield-check",
    "trending": "ti-trending-up",
    "clock": "ti-clock-hour-4",     # days on market
    "calc": "ti-calculator",
    "bank": "ti-building-bank",     # bank-owned / foreclosure
    "gavel": "ti-gavel",            # auction / sold as-is
    "link": "ti-external-link",     # outbound links (HUD/HomePath/HomeSteps)
    "phone": "ti-phone",            # call the listing agent
    "mail": "ti-mail",              # email the listing agent
    "globe": "ti-world",            # agent / brokerage website
    "user": "ti-user",              # listing agent / contact person
}


def ic(name: str, size: int = 18, color: Optional[str] = None) -> str:
    """Return inline HTML for an icon, e.g. ic('beds', 20, '#1D9E75')."""
    cls = ICONS.get(name, "ti-point")
    style = f"font-size:{size}px;"
    if color:
        style += f"color:{color};"
    return f"<i class='ti {cls}' style='{style}'></i>"

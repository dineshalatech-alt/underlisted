# Visual Polish — California Deal Finder

**Status:** ✅ Done (visual only — no API calls, no backend logic changed)
**Date:** 2026-06-07

This pass made the app *look* like a real, sellable product: a marketing
landing page, a polished mobile-first deal feed, and a clean detail screen with
a "how much cash you need" section. It used **zero** RentCast or Google quota —
real cached listings where available, realistic sample data otherwise, and grey
house-icon placeholders instead of live photos.

---

## How to view it

1. **In the browser:** open / refresh **http://localhost:8501**
   - You land on the **marketing page**.
   - Use the **`»` arrow (top-left)** to open the page menu and switch between:
     - **NorCal Deal Finder** — landing page
     - **Browse Deals** — the actual app (feed + detail)
     - **Admin / Usage** — backend, worker, cache hit-rate, spend
   - Or just tap the green CTA buttons on the landing page.

2. **As saved images:** full-page screenshots live in **`design_preview/`**
   - `design_preview/1_landing.png`
   - `design_preview/2_feed.png`
   - `design_preview/3_detail.png`

To (re)start the app:

```powershell
cd "c:\Users\dines\OneDrive\Documents\14. Real Estate"
.\.venv\Scripts\streamlit.exe run app\main.py
```

---

## What changed this pass (all visual)

- ✅ **Buttons are green** (were Streamlit's default red) — clean-green theme in
  `.streamlit/config.toml`.
- ✅ **Fixed a caption** that showed raw `<i>` HTML — the search/result icon now
  renders properly (`unsafe_allow_html=True`).
- ✅ **Removed the dev "Deploy" toolbar** (`toolbarMode = "minimal"`) and trimmed
  the big top gap (`.block-container { padding-top: 2rem }`).
- ✅ **One icon library** everywhere: **Tabler Icons** (web font via CDN).
- ✅ **Logo + favicon** (green house) generated offline → `app/assets/`.

---

## The three screens

**1. Landing** — green gradient hero, white house logo, headline *"Find
under-priced California homes in seconds,"* a pricing pill
**"$12.99/mo for your first 12 months, then $29.99 · cancel anytime,"** a green
**"Start 3-day free trial"** CTA, value-prop cards, how-it-works, pricing card.

**2. Feed** — single-column mobile cards, **best deal first**, each with a big
colored **deal-score gauge**, price, address, **beds/baths/sqft/year** with
icons, a rent line (with a clear amber **"sample"** tag when not from real
cache), grey **house-icon photo placeholders**, and a green **See details**
button.

**3. Detail** — house-placeholder photo, price/address/facts with icons,
**"Open in Google Maps"** link, the **deal-score gauge + tooltip**, a
**"Why it scored X"** segmented bar (green = value, purple = days-on-market,
orange = risk) with a per-factor list, plain **value & rent** lines with
tap-tooltips, and the **"How much cash you really need"** section (big total +
down payment / closing / cash-to-close / reserves, a live-in-vs-rent toggle, a
credit-band selector, and a "Full breakdown" expander).

---

## Icon mapping — one library: **Tabler Icons**

| Used for | Icon | Used for | Icon |
|---|---|---|---|
| beds | `ti-bed` | down payment | `ti-coins` |
| baths | `ti-bath` | cash to close | `ti-wallet` |
| sqft | `ti-ruler-2` | closing costs | `ti-receipt` |
| year built | `ti-calendar` | reserves | `ti-pig-money` |
| deal score | `ti-gauge` | total cash needed | `ti-key` |
| price | `ti-tag` | days on market | `ti-clock-hour-4` |
| estimated value | `ti-building-estate` | location / map | `ti-map-pin` |
| rent | `ti-cash` | filters / search | `ti-filter` / `ti-search` |
| logo / placeholder | `ti-home` | trial checks | `ti-circle-check` |
| fire risk | `ti-flame` | flood risk | `ti-droplet` |

(`ti-flame` / `ti-droplet` are defined and ready for when risk data is wired in.)

Plus the generated **logo + favicon** (green house) at
`app/assets/logo.png` and `app/assets/favicon.png`.

---

## Files touched

- `app/main.py` — landing / marketing page
- `app/pages/0_Browse_Deals.py` — polished feed + detail
- `app/icons.py` — Tabler CSS + icon map + `ic()` helper
- `app/sample_data.py` — real-cache-first, sample fallback
- `app/assets/theme.py` — colors + app CSS (trimmed chrome)
- `app/assets/logo.png`, `app/assets/favicon.png` — brand mark
- `.streamlit/config.toml` — green theme, minimal toolbar

---

## What's next (not started — awaiting your go-ahead)

- Risk flags (CalFire fire risk, FEMA flood) on cards/detail
- Map view
- AI "imagine remodeled" (Gemini)
- Accounts / payments / hosting

**Parked:** Google Street View / satellite photos (403) — see `MILESTONES.md`.

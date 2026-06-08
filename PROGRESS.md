# PROGRESS — NorCal Deal Finder

A running log of what we've built, the current state, and what's next.

---

## Current state (Visual polish: landing + feed + detail + icons) ✅ DONE

Pure visual pass — NO API calls. Multipage app: Landing (front door) → Browse
Deals (feed + detail) → Admin/Usage.

- `app/main.py` — marketing/landing: green gradient hero, logo, value props, how-
  it-works, pricing ("$12.99/mo first 12 months, then $29.99"), 3-day trial CTAs
  (→ Browse Deals via st.switch_page).
- `app/pages/0_Browse_Deals.py` — polished feed (deal-score gauge, price, address,
  beds/baths/sqft, rent, grey house-icon photo placeholders) + detail (score "why"
  breakdown, value/rent, **How much cash you really need**, tooltips).
- `src/financing/cash_needed.py` (new) — beginner cash breakdown (down/closing/
  reserves/total, live-in vs invest, credit band, rate). Pure math.
- `app/icons.py` (new) — ONE icon set: **Tabler** web-font, used everywhere.
- `app/sample_data.py` (new) — uses real cached listings; clearly-marked SAMPLE
  fallback if cache empty; "(sample)" tags on placeholder rent.
- `app/assets/logo.png` + `favicon.png` (new) — generated offline (green house).
- Verified: compiles; cash-needed math correct; 8 cached listings render; serves
  at localhost:8501.

---

## Previous state (Deal Score 0-100) ✅ DONE

The heart of the product: a transparent 0-100 Deal Score.

- `src/scoring/deal_score.py` (new) — weighted score from value-discount (50),
  rent yield (30), days-on-market (12), risk (8); all weights/scales editable in
  `config/scoring_weights.yaml`. No remodel/flip math, no protected-class signals.
  Missing inputs are EXCLUDED and the score rescales over available factors
  (honest), with a per-factor breakdown.
- `app/main.py` — feed cards show a colored score badge (green ≥70); sorted
  best-first; "good deals only" filter uses the score. Detail screen shows the
  score headline, a segmented "why it scored X" bar, a per-factor list (points /
  weight), plus the value range + comps behind it.
- Verified on the 8 cached Sacramento listings with NO new API calls: scores
  range 29–100 and rank sensibly (deepest discounts score highest). Rent yield is
  currently excluded (rent not cached); it joins when a listing is opened or the
  worker runs.

Live at localhost:8501.

---

## Previous state (Simple California Feed for first show) ✅ DONE (photos pending)

Stripped the UI to the simplest thing we can show real people: a mobile-first
scrolling feed of California listings with a plain "good deal" badge, and a
plain-language detail screen.

**Built:**
- `src/scoring/deal_signal.py` (new) — simple below-market badge
  (Great/Good/Around/Above market) from value-vs-estimate; config in
  `scoring_weights.yaml: simple_deal_signal`. Stand-in until the 0-100 Deal Score.
- `config/settings.py` — `active_state` / `active_state_name`; app reads the state
  from config (California today) so adding states later is easy.
- `app/main.py` — rebuilt: phone-shaped (`layout="centered"`), big text, big tap
  targets. Feed cards = photo, deal pill, price, address, beds/baths/sqft, "See
  details". Detail = its own screen: photo, plain value sentence, rent sentence,
  "what's this?" popovers, Google Maps link, optional "see it from above" aerial,
  and an advanced "More numbers" expander. Admin controls moved off the feed to
  the Admin/Usage page. No AI/accounts/payments in the UI; risk flags hidden
  (not built).

**Verified offline:** compiles; deal-signal thresholds correct; imports OK; app
serves at localhost:8501.

**STILL BLOCKED:** the live California end-to-end smoke test has NOT run — this
machine's `.env` has blank keys, so no real RentCast/Google call has succeeded.
RentCast value/rent field mapping remains UNVERIFIED until then.

---

## Previous state (Location tweaks + Phase 3: Rent & Value) ✅ DONE

**Location tweaks**
- Free **"View on Google Maps"** link on each card + detail (plain Maps search
  URL, no API call) — `app/helpers.py: gmaps_link()`.
- Clearer image labels: "Street View — curb view" and "Satellite — top-down".

**Phase 3 — Rent & value estimates** (on the detail page, lazy + cached)
- `src/metrics.py` (new) — gross yield, 1% rule, rough cap rate (uses
  `operating_expense_pct_of_rent`), and value-vs-AVM %. Pure math, None-safe.
- `rentcast.get_value_estimate` / `get_rent_estimate` gained `cache_only` so the
  per-user cap can serve cached estimates but block new billable calls.
- Detail panel now shows: est. monthly rent (+range), gross yield, 1% rule, cap
  rate, est. value (AVM) + range, list-vs-value %, and a "Why these numbers"
  expander with the sale/rent comps. Every jargon term has a hover tooltip.
- These fetch only when a listing is OPENED (cost rule), and the worker usually
  pre-warms them so opening is a free cache hit.

**Verified:** all compile; smoke test passed — gross yield 7.2%, cap rate 4.32%
(NOI 17,280/400k), value-vs-list −9.09% (below value), None-safety, and the free
Google Maps link.

**Next:** Phase 4 — Deal Score (0–100) with the transparent "why it scored X"
breakdown, building on these metrics.

---

## Previous state (Worker + Shared Cloud DB) ✅ DONE

Added a background worker and made the cache portable to a shared cloud database,
so cost stays flat as customers grow. No feature/look changes.

**What changed:**
- `src/cache/backend.py` (new) — one switch between LOCAL SQLite (default) and
  SHARED PostgreSQL via `DATABASE_URL`. Translates `?`→`%s`, adapts types; same
  schema both ways. Postgres driver `psycopg[binary]` (optional) added to
  requirements.
- `src/cache/db.py` — now runs through the backend; all upserts rewritten to
  portable `INSERT ... ON CONFLICT ... DO UPDATE` (works on SQLite + Postgres);
  added `worker_runs` table + `record_worker_run` / `worker_run_history` /
  `total_billable_calls`.
- `config/cache.yaml` — new `worker:` block (schedule_hours, max_listings_per_city,
  update_value_rent, max_estimates_per_run, prewarm_photos, prewarm_top_n).
- `worker/refresh_worker.py` (new) — automated refresh job: incremental listings
  sync + stale value/rent refresh (TTL-guarded, per-run cap) + optional photo
  pre-warm (off). Logs each run to `worker_runs`. CLI: run-once / `--full` /
  `--loop`. Idempotent. `rentcast.get_value/rent_estimate` gained
  `count_against_user` so worker fetches don't hit a user's cap.
- `app/pages/1_Admin_Usage.py` — shows active backend, **Run worker now** button,
  and worker run history (cities, new/updated, estimates, billable calls, notes).
- `.env.example` — added optional `DATABASE_URL`. README — added plain-English
  worker + cloud-DB setup and hosting/scheduling guidance.

**Verified:** all modules compile; offline smoke test passed for portable upserts
(no duplicates), worker_runs idempotent record, full worker run (18 listings + 36
estimate calls), idempotent re-run (0 new, 0 billed — estimates served from
cache), and run-history logging.

---

## Previous state (Cost Architecture pass) ✅ DONE

Reworked the whole app for LOW cost per customer. Features and the clean-green
look are unchanged — just leaner.

**What changed:**
- `config/cache.yaml` (new) — TTLs (listings 24h, value/rent 7d, images ~never),
  incremental-sync settings, image sizes (640x360), per-user monthly cap (300),
  and per-call cost estimates. Loaded via new helpers in `config/settings.py`.
- `src/cache/db.py` — TTL-aware `cache_get`, cache hit/miss counters
  (`cache_stats`), per-user monthly usage (`user_usage`), and a `meta` table for
  last-sync timestamps.
- `src/cost.py` (new) — per-user cap status + estimated-spend helpers.
- `src/data_sources/streetview.py` — keyed by LOCATION (rounded lat/long / norm.
  address), shared across users + listing ids; smaller configured size; hit/miss
  tracked; `cache_only` flag to enforce the cap.
- `src/data_sources/aerial.py` (new) — satellite image, same shared-cache design,
  gated behind an explicit button.
- `src/data_sources/rentcast.py` — incremental sync using per-area last-sync
  timestamps; cached, address-keyed `get_value_estimate` / `get_rent_estimate`
  (weekly TTL) — PLUMBING for Phase 3, not yet shown in the UI.
- `app/main.py` — never fetches on load; photos lazy (Show photo / Open);
  inline detail panel lazy-loads photo + aerial; sidebar shows last-sync and the
  per-user cap.
- `app/pages/1_Admin_Usage.py` (new) — calls by source, image fetches, cache
  hit-rate, estimated spend, cap usage, TTL windows.

**Verified:** all modules compile; offline smoke test passed for TTL expiry,
hit-rate counters, per-user cap (warn 80% / block 100%), cost estimate,
incremental days-old calc, and shared image key (same spot under 2 listing ids =
1 cached file).

**Expected savings:** ~95–99%+ fewer billable calls at scale vs. fetch-per-view
(see chat note). Photos/estimates go from "per card per user" to "once per
property, ever."

---

## Previous state (Phase 2 — Live listings + photos) ✅ DONE

Pulls real for-sale listings from RentCast for the configured cities and shows
each as a card with its real Street View photo, price, beds/baths, sqft, and
days on market. All reads come from the SQLite cache; only the "Refresh from
RentCast" button makes billable calls.

**Built in Phase 2:**
- `src/data_sources/rentcast.py` — GET `/v1/listings/sale` (header `X-Api-Key`),
  raw→Listing mapping, `sync_listings()` (full or incremental via `days_old`),
  per-listing upsert with price-drop detection, usage counting, and
  `load_cached_listings()` for free browsing.
- `src/data_sources/streetview.py` — real exterior photo; FREE metadata check
  first, downloads the image ONCE to `data/streetview/`, caches result so repeat
  views don't re-bill Google.
- `scripts/sync_listings.py` — command-line sync (`--days`, `--limit`).
- `app/main.py` — listings dashboard: card grid, city/price/beds/type filters,
  refresh controls, photo-load cap (cost control), live API-usage panel.
- `app/helpers.py` — money/number/bed-bath/days formatting.

**Verified:** all modules pass `py_compile`; offline smoke test passed for
mapping, upsert, price-drop detection, api_cache, usage tally, and cached read.

**RentCast facts confirmed from docs:** endpoint
`https://api.rentcast.io/v1/listings/sale`, auth header `X-Api-Key`, up to 500
results/call, camelCase fields (id, formattedAddress, city, zipCode, latitude,
longitude, price, bedrooms, bathrooms, squareFootage, yearBuilt, propertyType,
status, daysOnMarket).

---

## Previous state (Phase 1 — Scaffold) ✅ DONE

The project skeleton is built and runs. It loads config + keys and shows a
welcome dashboard. No live API calls yet.

**Built so far:**
- `README.md` — full beginner setup guide (install Python → run app).
- Project structure: `config/`, `src/` (data_sources, scoring, financing,
  cache), `app/`.
- Editable config: `cities.yaml`, `scoring_weights.yaml`, `financing.yaml`.
- `config/settings.py` — loads `.env` keys + all YAML in one place.
- `src/models.py` — data shapes (Listing, RentEstimate, ValueEstimate,
  RiskFlags, ScoreBreakdown, Deal).
- `src/cache/db.py` — SQLite shared cache: API cache, price history,
  usage tracking, listing upsert with price-drop detection.
- `app/main.py` — runnable Streamlit skeleton + `app/assets/theme.py`
  (clean-green theme).
- `.env.example`, `requirements.txt`, `.gitignore`.

**Verified:** Python 3.12.10 present; all modules pass `py_compile`.

---

## What YOU need to do before Phase 2

1. Install packages: `pip install -r requirements.txt` (README Step 3).
2. Create `.env` and paste your **RentCast** + **Street View** keys (Step 4).
3. Run `streamlit run app/main.py` and confirm the welcome screen loads.

---

## Next up (Phase 2 — Live listings + photos)

- `src/data_sources/rentcast.py` — fetch sale listings by city/zip, with
  caching + incremental sync + usage counting.
- `src/data_sources/streetview.py` — build/cache the real exterior photo URL.
- A real listings page: cards with photo + key facts.
- `scripts/sync_listings.py` — the "go fetch new/changed listings" command.

## Later phases
- Phase 3: Rent & value estimates, objective metrics, value-vs-AVM check.
- Phase 4: Deal Score + transparent "why it scored X" breakdown + comps/range.
- Phase 5: "How much cash you really need" (beginner-first) + tooltips + filters.
- Phase 6: Risk flags (CalFire/FEMA), map view, AI "imagine remodeled" button.
- Phase 7 (later): branding/landing/login, payments, hosting.

---

## Notes / decisions
- Building on **Windows** (PowerShell), though original brief said Mac — code is
  cross-platform.
- Do NOT scrape Redfin/Zillow/Realtor (TOS). RentCast is the listings source.
- Shared cache so repeat views don't re-bill APIs (cost control).
- Fair Housing: no demographic / "neighborhood quality" signals in scoring.

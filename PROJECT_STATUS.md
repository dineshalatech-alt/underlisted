# PROJECT_STATUS — NorCal Deal Finder

_A single honest snapshot of the whole project. Last updated: 2026-06-07._

> **Reality check up front:** the code is written and passes offline tests, but
> **no live API call has ever succeeded yet** — this machine has no API keys (the
> `.env` exists but its key fields are blank). So every path that talks to
> RentCast or Google is **written and unit-tested with fake data, but UNTESTED
> against the real services.** Details in section 8.

---

## 1. What the app does (plain language)

It helps a beginner find for-sale homes across **Northern California** and, for
each one, shows:
- a **real photo** (Google Street View) and a **satellite/aerial** view,
- the **facts** (price, beds/baths, sqft, year, days on market),
- an estimated **monthly rent** and simple yardsticks (gross yield, the 1% rule,
  a rough cap rate),
- a **value check** (list price vs. an estimated value / AVM),
- a free **"View on Google Maps"** link.

The bigger plan (not all built yet) is a **Deal Score (0–100)**, a beginner-first
**"how much cash you really need"** breakdown, and **fire/flood risk flags**.
Everything is labeled an **estimate / screening tool**, not advice.

It runs locally now (Streamlit web app). Accounts, payments, and hosting are a
later phase.

---

## 2. Tech stack & project structure

**Stack:** Python + Streamlit (UI), SQLite locally / PostgreSQL in the cloud
(shared cache), `requests` for APIs, PyYAML for config, pandas/pydeck/Pillow.

```
14. Real Estate/
├─ README.md              Beginner setup guide (install → run)
├─ PROGRESS.md            Running build log, newest phase on top
├─ ROADMAP.md             Vision, strategy, decisions, future ideas
├─ PROJECT_STATUS.md      ← this file
├─ requirements.txt       Python packages
├─ .env.example           Template for keys (safe to share)
├─ .env                   YOUR real keys (private; currently BLANK on this PC)
├─ .gitignore             Keeps .env + cache + venv private
│
├─ config/
│  ├─ cities.yaml         Target cities/zips (Sac, Stockton, Modesto, Vallejo,
│  │                      Antioch, Oakland) — editable
│  ├─ scoring_weights.yaml  Deal-Score weights — CONFIG ONLY, score not built yet
│  ├─ financing.yaml      Rates, down %, closing %, reserves, expense % — partly
│  │                      used (expense % feeds cap rate); rest awaits later phases
│  ├─ cache.yaml          TTLs, image sizes, per-user cap, worker schedule, costs
│  └─ settings.py         Loads .env + all YAML in one place
│
├─ src/
│  ├─ models.py           Data shapes: Listing, RentEstimate, ValueEstimate,
│  │                      RiskFlags, ScoreBreakdown, Deal
│  ├─ metrics.py          Gross yield, 1% rule, cap rate, value-vs-AVM (pure math)
│  ├─ cost.py             Per-user cap status + estimated-spend helpers
│  ├─ cache/
│  │  ├─ backend.py       Switch: local SQLite OR cloud PostgreSQL (DATABASE_URL)
│  │  └─ db.py            Shared cache: listings, api_cache(TTL), usage,
│  │                      hit/miss counters, per-user usage, worker_runs, meta
│  ├─ data_sources/
│  │  ├─ rentcast.py      Listings sync + value/rent estimate fetchers (cached)
│  │  ├─ streetview.py    Real curb photo (shared, address-keyed, cached once)
│  │  └─ aerial.py        Satellite image (Google Static Maps), cached once
│  ├─ scoring/            EMPTY (only __init__.py) — Deal Score not built
│  └─ financing/          EMPTY (only __init__.py) — cash-needed not built
│
├─ app/
│  ├─ main.py             The dashboard: card grid, filters, detail panel
│  ├─ helpers.py          Formatting (money, %, beds/baths) + Google Maps link
│  ├─ assets/theme.py     Clean-green theme (colors + CSS)
│  └─ pages/
│     └─ 1_Admin_Usage.py Admin view: calls, hit-rate, spend, worker history
│
├─ worker/
│  └─ refresh_worker.py   Background job: incremental refresh of cache (no UI)
│
├─ scripts/
│  └─ sync_listings.py    Command-line listings sync (alternative to the button)
│
└─ data/                  Auto-created: cache.db, /streetview, /aerial
```

---

## 3. Features by phase (DONE / PARTIAL / NOT STARTED)

### Phase 1 — Scaffold — **DONE**
- Project structure, config files, runnable Streamlit skeleton, README. ✅

### Phase 2 — Live listings + Street View — **DONE (code) / UNTESTED LIVE**
- Pull for-sale listings from RentCast for configured cities. ✅ *(endpoint &
  fields confirmed from RentCast docs; not yet run against a real key)*
- Card grid: price, beds/baths, sqft, year, type, status, days on market. ✅
- Real Street View photo per card/detail. ✅ *(untested live)*
- SQLite caching so repeat views don't re-bill. ✅ *(tested offline)*
- API-usage panel. ✅

### Cost-architecture pass — **DONE (code) / mostly tested offline**
- Shared cache keyed by property/address, not per user. ✅ *(tested)*
- TTL expiry (listings daily, value/rent weekly, images ~never), config'd. ✅
- Per-user monthly lookup cap (warns at 80%, blocks at 100%). ✅ *(tested)*
- Admin/Usage page: calls by source, cache hit-rate, estimated spend. ✅
- **Lazy images — PARTIAL vs. the literal spec.** Photos load on **click / open**
  (plus a "first N cards" backstop), NOT on true browser "scroll into view."
  Streamlit can't easily detect scroll; the click/open approach achieves the same
  cost goal. Functionally complete, implemented differently than worded.

### Worker + shared cloud DB — **DONE (code) / Postgres path UNTESTED LIVE**
- Background worker: incremental listings + stale value/rent refresh, logs each
  run, idempotent, run-once / `--full` / `--loop`, "Run now" button. ✅ *(tested
  offline with mocked network)*
- SQLite↔PostgreSQL switch via `DATABASE_URL`; portable upserts. ✅ *(tested on
  SQLite only — **never run against a real PostgreSQL server**)*
- Worker run history in Admin view. ✅

### Location tweaks — **DONE**
- Free "View on Google Maps" link (no API call). ✅ *(tested)*
- Clearer labels: "Street View — curb view" / "Satellite — top-down." ✅
- Aerial/satellite image with toggle on detail. ✅ *(code done; untested live;
  needs "Maps Static API" enabled on the Google key)*

### Phase 3 — Rent & value estimates — **DONE (code) / field mapping UNVERIFIED**
- Detail page shows est. monthly rent (+range), gross yield, 1% rule, cap rate,
  est. value (AVM) + range, list-vs-value %, and a comps expander. ✅
- Jargon tooltips on every metric. ✅
- Math verified by offline test. ✅
- ⚠️ The RentCast **value/rent endpoint field names are my best assumption**, not
  confirmed against a live response (see section 8).

### Phase 4 — Deal Score (0–100) — **NOT STARTED**
- `config/scoring_weights.yaml` exists; `src/scoring/` is empty. No score, no
  "why it scored X" breakdown yet.

### "How much cash you really need" — **NOT STARTED**
- `config/financing.yaml` exists; `src/financing/` is empty. No down-payment /
  closing / reserves breakdown, no live-in vs. invest toggle, no PITI yet.

### Risk flags (Cal Fire fire zones + FEMA flood) — **NOT STARTED**
- `RiskFlags` shape exists in models, but there is **no** `risk.py`, no data pull,
  no badges in the UI. This is the planned differentiator and is not begun.

### Map view — **NOT STARTED** (pydeck installed, no map screen yet).

### AI "imagine remodeled" + branding (Gemini/Nano Banana) — **NOT STARTED**
- `GEMINI_API_KEY` is wired into settings, but there is **no** `gemini_images.py`,
  no render button, no generated branding/landing assets.

### Accounts / payments / landing page / hosting — **NOT STARTED** (later phase).

---

## 4. Data sources & API keys

| Source | Used for | Env var | Wired in? | Proven live? |
|---|---|---|---|---|
| **RentCast** | Sale listings; value (AVM) & rent estimates | `RENTCAST_API_KEY` | Yes | ❌ no key on this PC |
| **Google Street View Static** | Real curb photo | `STREETVIEW_API_KEY` | Yes | ❌ |
| **Google Maps Static** | Satellite/aerial image | reuses `STREETVIEW_API_KEY` | Yes | ❌ (needs "Maps Static API" enabled) |
| **Google Maps link** | Clickable address link | none (free URL) | Yes | ✅ (no API) |
| **Google Gemini** | AI renders + branding | `GEMINI_API_KEY` | settings only | ❌ feature not built |
| **Cal Fire / FEMA** | Fire & flood risk | none (free public) | No | ❌ not started |

Keys live only in `.env` (git-ignored). **No keys are printed anywhere.** On this
computer the `.env` currently has **blank** key slots, so live features are dark.

---

## 5. Cost-control setup & current state

- **Shared cache (SQLite now / Postgres later):** one lookup + one image fetch per
  property, served to all users. ✅ working (SQLite, offline-tested).
- **TTL expiry** in `config/cache.yaml`: listings 24h, value/rent 7d, images
  ~never. ✅
- **No fetch on page load:** the app only reads cache; refresh happens via the
  button or the worker. ✅
- **Incremental sync:** per-area "last sync" timestamps drive a smaller daily
  pull; weekly `--full` catches older-home price changes. ✅ (offline-tested)
- **Background worker:** refreshes cache on a schedule; does **not** fetch images
  by default (config flag `prewarm_photos` to opt in). ✅ (offline-tested)
- **Per-user monthly cap** (default 300): warns at 80%, blocks new billable
  fetches at 100%; cached views stay free. ✅ Today it tracks a single `"local"`
  user because there are **no accounts yet**.
- **Smallest-good image size** (640×360, config'd); expensive things (aerial, and
  later AI Pro) are behind explicit buttons. ✅
- **Visibility:** Admin/Usage shows billable calls by source, image fetches,
  cache hit-rate, and estimated $ (rates editable in `cache.yaml`). ✅

**Estimated effect (not measured live):** cost tracks the number of *distinct
properties*, not the number of users — so it stays roughly flat as customers grow.

---

## 6. Not built yet / gaps / placeholders / TODO

- **Deal Score** (Phase 4) — not started; weights config is a placeholder.
- **"Cash you really need"** breakdown — not started; financing config is a
  placeholder (only the expense % is actually used so far, for cap rate).
- **Risk flags (Cal Fire / FEMA)** — not started; model field exists, nothing else.
- **Map view** — not started.
- **AI "imagine remodeled" + branding/landing** — not started.
- **Accounts / payments / trial** — not started (copy/placeholders only).
- **Real authentication** — none; the per-user cap uses a hardcoded `"local"` user.
- **Lazy-load = click/open**, not literal scroll-into-view (see Phase notes).
- **Price-drop flag** is computed and stored, shown as a small card badge; there's
  no dedicated "price drops" view/feed yet.
- **No automated test suite in the repo** — validation was done with temporary
  throwaway scripts (now deleted), not committed `pytest` files.

---

## 7. Exact commands

**One-time setup (Windows / PowerShell):**
```powershell
cd "$HOME\OneDrive\Documents\14. Real Estate"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # then paste your keys into .env
```

**Run the app:**
```powershell
streamlit run app/main.py
# then open http://localhost:8501
```

**Run the background worker:**
```powershell
python -m worker.refresh_worker          # run once (safe to repeat)
python -m worker.refresh_worker --full    # full refresh (weekly)
python -m worker.refresh_worker --loop    # keep running on a schedule
```

**Command-line listings sync (optional):**
```powershell
python scripts/sync_listings.py            # full
python scripts/sync_listings.py --days 7   # incremental
```

**Use a shared cloud database (optional, later):** put
`DATABASE_URL=postgresql://user:pass@host:5432/db` in `.env`, then run the worker
once to create the tables.

---

## 8. Broken / untested / unsure (the honest list)

1. **No live API call has succeeded yet.** This PC has no keys. Listings, photos,
   aerial, and estimates are written and unit-tested with **fake** data only.
   First real run could surface field-name or auth mismatches.
2. **RentCast value/rent field names are ASSUMED.** The **listings** endpoint
   (`/v1/listings/sale`) and its fields were confirmed from RentCast's docs. The
   **AVM** endpoints (`/v1/avm/value`, `/v1/avm/rent/long-term`) and the fields I
   read (`price`, `priceRangeLow/High`, `rent`, `rentRangeLow/High`,
   `comparables`) are my best understanding and **not verified** against a real
   response. If the section shows "No estimate available," this mapping is the
   first place to check.
3. **PostgreSQL path is untested live.** The portable SQL was tested on SQLite
   only; it has **never** run against a real Postgres server. `psycopg` is now
   installed, but expect to shake out small issues on first cloud connect.
4. **Aerial images need "Maps Static API" enabled** on the Google key (a different
   service than Street View). If not enabled, aerials come back blank/error.
5. **Street View billing assumption:** we use the free metadata check, then
   download the image once and reuse the file. Correct in design; unverified live.
6. **Currently running instance:** the app is up on `http://localhost:8501` from a
   freshly installed `.venv` on this machine, against an **empty cache and no
   keys** — so it shows the welcome/empty state by design.
7. **Worker estimate budget** stops after `max_estimates_per_run` *properties that
   needed a refresh*; this is a simple guard, not a precise per-call meter.
8. **Stale data window:** because refresh is scheduled, listings can be a few hours
   old. Intended trade-off; tune TTLs in `cache.yaml` if you want fresher.

---

_This file is a status report only — writing it changed no code._

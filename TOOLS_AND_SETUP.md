# TOOLS & SETUP — so we don't re-learn it

The practical setup in one place. To resume the project, start at
**[PROJECT_MEMORY.md](PROJECT_MEMORY.md)**.
*Last updated: 2026-06-07.*

---

## Tools & services

| Tool / service | Used for | Status / note |
|---|---|---|
| **RentCast API** | Sale listings + value (AVM) & rent estimates | **Proven live.** On the **free 50-call plan** now → **upgrade to Foundation ($74/mo) before loading many CA cities.** Key in `.env` (`RENTCAST_API_KEY`). |
| **Google Cloud** | Street View Static (curb photo) + Maps Static (satellite) | **PARKED — 403.** Project **`amazing-aleph-497810-h3`**, billing linked, APIs enabled. Key in `.env` (`STREETVIEW_API_KEY`, reused for Maps Static). Grey placeholders used meanwhile. |
| **Streamlit** | The web app UI (multipage) | Working. |
| **SQLite / PostgreSQL** | Shared cache | SQLite local now; switch to Postgres later via `DATABASE_URL`. |
| **Tabler Icons** | One icon library, app-wide | Web font via CDN (`app/icons.py`). |
| **Pillow** | Generated logo/favicon offline | Done. |
| **Google Gemini** | Future "imagine remodeled" | Key wired in settings; feature not built. |
| **CalFire / FEMA** | Future fire/flood risk | Free public data; not started. |

> **Secrets rule:** all keys live ONLY in `.env` (git-ignored). Never printed,
> never pasted into chat. For debugging we only ever show key length / last-4.

---

## Exact commands (Windows / PowerShell)

**One-time setup**
```powershell
cd "$HOME\OneDrive\Documents\14. Real Estate"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # then paste your keys into .env
```

**Run the app**
```powershell
streamlit run app/main.py
# open http://localhost:8501
```

**Run the background worker**
```powershell
python -m worker.refresh_worker          # run once (safe to repeat)
python -m worker.refresh_worker --full   # full refresh (weekly)
python -m worker.refresh_worker --loop   # keep running on a schedule
```

**Optional command-line listings sync**
```powershell
python scripts/sync_listings.py            # full
python scripts/sync_listings.py --days 7   # incremental
```

**Use a shared cloud DB (later):** put
`DATABASE_URL=postgresql://user:pass@host:5432/db` in `.env`, then run the worker
once to create the tables.

---

## How we work (rules & techniques we rely on)

- **Cache-first / no-API-calls-while-designing.** When polishing UI or designing,
  use cached or realistic sample data and grey placeholders — never burn RentCast
  or Google quota for looks.
- **Never fetch on page load.** The app only reads cache; refresh happens via the
  button or the worker.
- **Plan mode for backend steps.** Plan the approach before writing backend code;
  one clear phase at a time, and don't start the next phase until confirmed.
- **Fair-Housing-safe scoring.** Scoring/filtering never uses demographic or
  "neighborhood quality" signals.
- **Verify visually with screenshots** (Playwright at a 420px mobile viewport,
  saved to `design_preview/`) instead of guessing how it looks.
- **Research with subagents** when studying competitors (public pages only, no
  scraping).

---

## PARKED — Google photos 403 fix (when we revisit)

1. Set the project and enable services in Cloud Shell:
   ```
   gcloud config set project amazing-aleph-497810-h3
   gcloud services enable apikeys.googleapis.com street-view-image-backend.googleapis.com static-maps-backend.googleapis.com
   ```
2. Clear any key restrictions:
   ```
   for k in $(gcloud services api-keys list --format='value(name)'); do gcloud services api-keys update "$k" --clear-restrictions; done
   ```
3. **Check the billing ACCOUNT status, not just the link** — it can show "linked"
   while the account itself is inactive/closed. Errors seen: Street View "not
   authorized to use this service or API"; Maps Static "You must enable Billing on
   the Google Cloud Project."

---

## Key decisions (locked)

- **Nationwide (whole U.S.)** as of 2026-06-12 (was a California-only pilot).
- **Pricing:** $12.99/mo for the first 12 months, then **$29.99/mo**; 3-day trial,
  cancel anytime. (Full detail in [MASTER_SPEC.md](MASTER_SPEC.md).)
- **Deal alerts + saved searches = flagship premium / retention feature** (the
  thing serious investors pay up for; basis for a future premium tier).
- **Fair-Housing-safe scoring** — no demographic / neighborhood-quality signals.
- **Low cost per customer** is a core constraint (shared cache, precompute,
  never-fetch-on-load).
- Automation is a **scheduled worker, not an AI agent.**

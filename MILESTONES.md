# MILESTONES & OPEN THREADS

A short log of big wins and parked TODOs, so nothing gets lost between sessions.
To resume, start at **[PROJECT_MEMORY.md](PROJECT_MEMORY.md)**. (Day-to-day detail
lives in PROGRESS.md; full snapshot in PROJECT_STATUS.md.)

---

## ✅ Milestones reached (dated)

**All on 2026-06-07** (built in one intensive run):

1. **Phase 1 — Scaffold.** Project structure, config files, runnable Streamlit app, beginner README.
2. **Phase 2 — Live listings + photos.** RentCast listings as cards (price, beds/baths, sqft, year, days-on-market) with Street View / aerial; SQLite cache.
3. **Cost architecture.** Shared cache keyed by property (not per user), TTL expiry, lazy images, per-user monthly cap, Admin/Usage page with cache hit-rate + estimated spend.
4. **Worker + cloud-DB switch.** Scheduled background refresh job (`worker/refresh_worker.py`) — a plain worker, not an AI agent; SQLite⇄PostgreSQL via one `DATABASE_URL`.
5. **Phase 3 — Rent & value estimates.** Gross yield, 1% rule, cap rate, list-price-vs-AVM, with jargon tooltips.
6. **Live data pipeline PROVEN.** Real Sacramento listings + rent/value estimates working end to end at **localhost:8501**. RentCast confirmed live (listings + value + rent, fields match the code). 8 real listings loaded (≈9 billable calls).
7. **Deal Score (0–100) — module built.** Transparent score with editable weights + "why it scored X" breakdown. *(Renders on sample data; next step is to validate/lock it on the real cached listings — see PROJECT_MEMORY.)*
8. **"How much cash you really need" breakdown.** Down payment / closing / cash-to-close / reserves, live-in-vs-invest toggle, credit band — pure client-side math.
9. **Visual polish.** Marketing/landing page, polished mobile feed + detail, one icon library (Tabler), logo/favicon, green theme — all no-API.
10. **Pricing locked + plan files.** $12.99/mo for 12 months → $29.99 standard. Wrote MASTER_SPEC, ROADMAP_TO_LAUNCH (incl. Phase 6 video plan), MARKETING_NOTES.
11. **Competitive research.** Studied 9 rivals (PropStream, DealMachine, DealCheck, Mashvisor, Roofstock, Reventure, Zillow, Redfin, Homes.com) → COMPETITIVE_IDEAS.md, with 6 visual upgrades approved to build later.

---

## ⏳ Open threads / parked TODOs

### TODO — Google photos/satellite (Street View + Maps Static)
TODO — Google photos/satellite still 403. Project, billing link, and enabled APIs
confirmed correct. Remaining fixes: (a) API-key restriction via Cloud Shell:
`for k in $(gcloud services api-keys list --format='value(name)'); do gcloud
services api-keys update "$k" --clear-restrictions; done` ; (b) billing ACCOUNT
status may be inactive though linked — check account status, not the link. App
works fine without photos (cosmetic). Revisit fresh.

**Extra context (from debugging):** key lives in project `769442287214` =
`amazing-aleph-497810-h3` (display name "My First Project"). Before the Cloud
Shell loop, run `gcloud config set project amazing-aleph-497810-h3` and
`gcloud services enable apikeys.googleapis.com street-view-image-backend.googleapis.com static-maps-backend.googleapis.com`. Exact errors seen: Street View →
"not authorized to use this service or API"; Maps Static → "You must enable
Billing on the Google Cloud Project."

### TODO — RentCast plan upgrade before scaling
Currently on the **free 50-call plan**. Upgrade to **Foundation ($74/mo)** before
loading many California cities at once, or the sync will run out of calls.

### Next build step
**Deal Score on cached data** — see [PROJECT_MEMORY.md](PROJECT_MEMORY.md).

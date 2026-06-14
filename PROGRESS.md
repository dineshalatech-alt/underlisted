# PROGRESS — Deal Finder (U.S. nationwide)

A running log of what we've built, the current state, and what's next.

---

## Landing → "Why Underlisted" content section added — 2026-06-14 (Juliet)

- **Owner wanted our reasons-to-choose-us on the landing**, clean/simple/organized, with the
  emotional frame: a home is the **biggest purchase of your life** — use Underlisted first.
  Copy came from Serena in `develop/WEBSITE_WHY_US.md`.
- **`app/main.py`** — added a new "Why Underlisted" section **between "How it works" and the
  banknote pricing card** (selling/Payhip/$18.99 logic untouched). It has, top to bottom:
  a calm **frame band** pull-quote (gold hairline, gold bold accents); an eyebrow + title
  ("Why Underlisted" / "The whole picture, in plain English"); **5 benefit cards** in an equal
  grid (3 + 2 centered) reusing the existing dark-glass `.feat` style with **gold number badges**
  + Tabler icons; a bold **contrast block** (grey setup line → off-white payoff, "actually good"
  in gold); a small **trust strip** with gold dot separators; and a closing one-liner above the
  existing pricing card.
- New CSS lives in the same `<style>` block in `main.py` (`.frameband`, `.section-eyebrow`,
  `.section-title`, `.feat .num`, `.contrast`, `.trust`) — cohesive with dark-luxe, no theme rip-out.
- ✅ Verified: `py_compile` clean, app served 200, screenshots in `design_preview/`
  (`why_us_section.png`, `why_us_contrast.png`, `why_us_trust.png`). 0 billable calls.

---

## Landing → "Dark luxe" (black + DM Sans + gold) — 2026-06-14

- **Owner asked to copy an Apple-style dark theme** (black `#000`, off-white `#F5F5F7`,
  **DM Sans**) for the app landing — keeping the gold buttons, gold-foil `$18.99` banknote,
  and dollar-bill motif (gold-on-black = luxury). Scope: **app landing only**.
- `app/main.py`: DM Sans imported + forced app-wide; `.stApp` now black with the dollar-bill
  SVG pattern recolored **gold** (faint); off-white body text; hero scrim fades to black;
  feature cards → **dark glass** (gold hairline border, white head, grey body); section
  headings white; the banknote keeps its cream surface + dark text so it reads as a real bill.
- `.streamlit/config.toml`: theme switched to `base="dark"`, gold `primaryColor`, black bg,
  off-white text. (Restart required — done.)
- ✅ Verified: compiles, app serves 200, screenshots in `design_preview/` (`dark_top.png`,
  `dark_feat.png`, `note_card.png`). Payment/checkout untouched. 0 billable calls.
- Note: warm cream palette still lives in `app/assets/theme.py` for the OTHER pages (Browse
  Deals etc.) — they're unchanged. A future pass can take dark-luxe app-wide if owner wants.

---

## Differentiation strategy + develop/ & team/ folders + new standing rule — 2026-06-14

- **Competitor research (Scout) + brainstorm (Atlas + Serena):** every serious rival (Mashvisor,
  PropStream, DealCheck, DealMachine, Reventure) serves INVESTORS or is market-level. **Nobody serves
  the plain-English first-time BUYER.** Our wedge: "for people who'll LIVE in the home, not flip it" +
  insurance-risk + "can you afford THIS home?". Chosen moat to build next: **"Can I Afford It?" +
  Surprise-Cost** (personal affordability badge + budget-killer warnings) — mostly logic on data we
  already pay for. Atlas mapped the build (`db.py` prefs table, `0_Browse_Deals.py`, deal-score module).
- **New `develop/` folder:** `DEVELOPMENT.md` (goals, map, how-we-win, optimization priorities) +
  `Underlisted_Strategy.html` + **`Underlisted_Strategy.pdf`** (branded, with an arrow MAP of the
  engine→funnel + gold "optimize here" callouts). PDF rendered via Playwright/Chromium (`.tmp/html_to_pdf.py`).
- **New `team/` folder:** `TEAM.md` — roster (Atlas builds · Serena grows · Scout researches · Juliet
  designs), what each does, and the improvement loop. PROGRESS.md remains the timeline.
- **New STANDING RULE added to global `~/.claude/CLAUDE.md`:** every project always gets a `develop/`
  folder (project map + goals + how-we-win) and a `team/` folder (roster + running log + how we improve).
- RentCast still paused until July 7 (owner choice); upgrade = #1 paid step when ready.

---

## Early-bird pricing + gold/dollar-bill touch (landing only) — 2026-06-14

- **Owner pricing decision (landing page ONLY for now):** show anchor **~~$99.99/mo~~**
  struck through → **$18.99/mo** early-bird ("Founding-member rate, locked in for life").
- **Gold + dollar-bill design** added to `app/main.py`: a banknote-style "Founding Member"
  card — gold double border, guilloché engraving lines, gold corner `$` seals, gold-foil
  shimmering `$18.99`, and a serial-number line. Hero pill matches (struck $99.99 → $18.99).
  New CSS classes: `.gold-foil` (animated foil text), `.note` / `.seal` (banknote).
- ⚠️ **Scope limited:** other pages + marketing still show the OLD ladder
  ($12.99 → $29.99 → $44.99) — `app/pages/2_Check_A_Deal.py`, `3_My_Alerts.py`,
  `MASTER_SPEC.md`, `MARKETING_*`, `PROJECT_MEMORY.md`. NOT changed yet (owner to decide).
- Warm logo also recolored (coral/cream/gold house); green originals backed up as
  `app/assets/logo_green_backup.png` / `favicon_green_backup.png`.
- **All landing buttons → gold** (gold-gradient fill, dark text, hover lift) + a faint
  **engraved dollar-bill pattern** woven into the page background (`.stApp`, subtle SVG
  watermark so text stays readable). Owner: keep subtle, landing page only for now.
- ✅ Verified: compiles, app serves 200, screenshots in `design_preview/`
  (`after_pricing.png`, `note_card.png`). Payment/checkout logic untouched. 0 billable calls.

---

## HUD Fair Market Rents wired (FREE area rent fallback) — 2026-06-14

- Owner created a free HUD USER token (Fair Market Rent dataset) → `HUD_FMR_TOKEN` in `.env`.
- **New source: `src/data_sources/hud_fmr.py`** — fetches each state's full FMR table once
  (free, cached to `data/hud_fmr/<STATE>.json`, refreshed ~yearly by the worker). `area_rent(listing)`
  matches a listing's city → its HUD metro and returns the fair-market rent for the bedroom count.
  Reads only the local cache (NO network on page load). Dormant if the token is missing.
- **Wired as a FREE fallback rent** in `rentcast.get_rent_estimate()` (new `_hud_rent_fallback`):
  when RentCast has no rent — including the capped/cache-only page-load path — the app uses the
  HUD area rent so rent-yield still works at $0. `RentEstimate` gained `source` + `area` fields
  (backward-compatible) so the UI can label it honestly ("HUD Fair Market Rent (area)").
- Worker step 1d3 (`update_hud_fmr` in `cache.yaml`) refreshes FMR for every state in the
  city list. ✅ Verified: CA/TX/GA tables pulled (2026); Sacramento 3-bed = $3,002, 1-bed = $1,832;
  capped page-load path returns the HUD rent with correct source/area. **0 billable calls.**
- Integration plan updated: HUD FMR now ✅ done. Remaining free keys (FRED/Census/crime) optional.

---

## Live mortgage rate wired (FREE, no key) + data-source integration plan — 2026-06-13

- **New source: `src/data_sources/mortgage_rates.py`** — pulls the real current 30-yr
  fixed rate from **Freddie Mac PMMS** (free public CSV, NO key, not billable), caches it
  to `data/mortgage_rate.json` (read with no network on page load — mirrors `market.py`).
  Optional `FRED_API_KEY` upgrade reads the same number from the Fed; falls back to Freddie
  automatically, so it works out of the box.
- **Wired into the money math** (`src/financing/cash_needed.py`): "true monthly cost" now
  uses the LIVE primary rate and keeps the owner's investment **premium** on top. Typed
  `financing.yaml` rates are now the fallback until the first refresh.
- **Worker step added** (`refresh_worker.py` 1d2, `update_mortgage_rate` in `cache.yaml`,
  ~weekly). Settings gained `fred_api_key` + `has_fred`; `.env.example` documents the
  optional free key.
- ✅ **Verified end-to-end:** fallback 6.6% → live **6.52%** (Freddie Mac, as of 6/11/2026);
  $400k P+I $2,478 → $2,458; investment 7.22% (premium preserved). **0 billable calls.**
- **Scout's data-source register** saved earlier: `research/DATA_SOURCE_REGISTER.xlsx`
  (25 US real-estate sources, vetted for cost + legal + fit).
- **New doc: `DATA_SOURCE_INTEGRATION_PLAN.html`** — how to connect ALL 25 sources, what's
  needed from the owner per source, and the build order. **Next free key to grab: HUD FMR
  token** (free rent baseline → cuts RentCast cost). Paid options await owner approval; MLS
  feeds need an MLS membership.

---

## Design upgrade kickoff: Juliet agent + warm landing redesign — 2026-06-13

- **New agent: Juliet** (`.claude/agents/Juliet.md`) — owns DESIGN & BRAND. Job: make the
  app + website radiant, vibrant, attractive, trustworthy. Uses the general Claude design
  skills (frontend-design, website-build, video-to-website, nano-banana-images) + the owner's
  Kling animation as a hero. Roster now: **Atlas** builds · **Serena** grows · **Scout**
  researches · **Juliet** designs.
- **Brand color rule LIFTED (owner decision).** The old "light green `#1D9E75`, never blue"
  rule no longer constrains the *look* of the app/website — full color freedom. Non-color
  guardrails (no billable calls, don't touch payment/selling, secrets, Fair Housing) still hold.
  ⚠️ CLAUDE.md §6 + the `document-theme` skill still say green-only — update pending owner OK.
- **Palette chosen: "Warm & trustworthy"** — cream `#FFFDF8`, near-black text `#1A1A1A`,
  coral `#FF6B5C` (+ deep `#E2513F`), gold `#F2A93B`, cocoa `#2E2A26`. Added to
  `app/assets/theme.py` (legacy GREEN_* names aliased so other pages keep working).
- **Landing redesigned** (`app/main.py`): Kling video as a looping, muted hero background
  with a poster frame + warm scrim for legibility; coral CTAs; hover-lift feature cards;
  coral-accented pricing card. Streamlit theme + static serving set in `.streamlit/config.toml`.
- **Kling video optimized** 12 MB → **548 KB** (`app/static/hero.mp4`, 1280-wide, crf 30,
  faststart, no audio) + `hero_poster.jpg` (106 KB). Served at `/app/static/`.
- ✅ Verified: app boots clean, `/app/static/hero.mp4` serves 200, before/after screenshots in
  `design_preview/` (`before_landing.png` → `after_landing.png`). **0 billable API calls.**
- **Next (Juliet):** owner approval → carry the warm palette into Browse Deals (feed + detail)
  and the static `site/` website; recolor the green house logo to match; then update CLAUDE.md §6.

---

## Marketing plan + nationwide city coverage — 2026-06-13

- **Marketing strategy built** (3 deliverables, green-themed, no blue):
  `MARKETING_PLAN.html/.md` (90-day plan, faceless "Underpriced Home of the Day"
  engine, funnel, $12.99 hook), `MARKETING_COST_ANALYSIS.html` (live 2026 ad rates;
  100k impressions ≈ $300–$1,500 paid or free organic; ladder shows 100k ≈ ~6 subs;
  who-to-reach = buyers/investors/agents-as-channel/creators), and
  `GO_LIVE_CHECKLIST.html` (plain-English worker + Payhip steps).
- **Owner decisions:** spend **$0 organic** until the app converts; **all videos
  produced IN-HOUSE** (no paid outside creators); expand coverage **nationwide**.
- **Worker + payment = code-complete already** (prior commits). Remaining work is
  owner-only dashboard steps: add GitHub Actions secrets + run the workflow; create
  the Payhip $12.99/mo product and paste its link into `config/cache.yaml:checkout_url`.
- **Nationwide city coverage shipped:** `_iter_targets()` in `src/data_sources/
  rentcast.py` now reads an optional per-target `state:` (falls back to the file-level
  default — backward-compatible). `config/cities.yaml` rewritten: kept the 6 CA cities
  (by zip) and added 15 deal-heavy metros across TX/OH/IN/MO/TN/AL/FL/GA/NC/PA/OK
  (whole-city search). ✅ Verified: 33 target lookups across 12 states parse cleanly.
  Fixed stale "NorCal" labels in `worker/refresh_worker.py`.
- **Next:** owner runs the go-live checklist → then build the **in-house video factory**
  (one-click: app screen-record + AI voiceover + captions → 9:16 deal video) + first 5 scripts.
- **New agent: Scout** (`.claude/agents/Scout.md`) — research scout that hunts (1) new DATA
  sources to enrich the app, (2) new COMPETITORS, (3) new PLACES to market; returns a ranked,
  green-themed report with cost + legal/ToS check + top pick. Guardrails baked in: no scraping
  portals, Fair-Housing info-only, never spends/signs up, cites sources. Feeds Atlas (data) and
  Serena (competitors/marketing). Keeps a running register under `research/` (won't overwrite the
  existing `DATA_SOURCES_USA*.xlsx`). Roster now: **Atlas** builds · **Serena** grows · **Scout** researches.

---

## Email alerts switched ON + pricing update — 2026-06-12

- **Deal-alert emails are LIVE.** Added `RESEND_API_KEY` to `.env`; built
  `src/notify/email_sender.py` (Resend HTTP API, green-themed digest, no blue).
  `db.py` now stores an **email per saved search** + a `notified` flag (migrations
  auto-add the columns). The worker (`refresh_worker.py` step 1f) emails one digest
  per saved search for new matches and marks them sent (never double-emails).
  My Alerts page now has an **"Email me at"** field.
  ✅ **Verified:** real test email sent to dineshalatech@gmail.com (Resend id returned).
- **Caveat:** sends from Resend's shared test address → can only reach the owner's
  own Resend email until a **domain is verified** in Resend. Set `ALERT_FROM_EMAIL`
  after that to email real customers.
- **Pricing updated:** path is now **$12.99/mo intro (12 mo) → $29.99 now → rising to
  $44.99 later**. Hook changed to *"Lock in $12.99/mo for a year — the price is rising
  to $44.99 soon."* Updated in app/main.py, MASTER_SPEC, MARKETING_NOTES, PROJECT_MEMORY.

---

## Growth features ("do all") — 2026-06-12

Built the four growth levers from GROWTH_STRATEGY.md (all free, 0 API calls):
1. **SEO + PR static site** — `tools/gen_site.py` writes hostable HTML to `site/`:
   `index.html`, `deals-in-<city>.html` (one per city), `report-underpriced.html`.
   Real SEO/PR assets (Streamlit can't rank; static HTML can). Needs HOSTING to go live.
2. **Free "Is it a good deal?" funnel** — `app/pages/2_Check_A_Deal.py`: type a city/ZIP,
   see the top-scored home + a verdict, free, no signup. Cache-first.
3. **Saved searches + deal alerts** — `app/pages/3_My_Alerts.py` + `db.py`
   (saved_searches / alert_log tables) + worker matching step (`update_alerts`).
   Save a search → worker records matching deals. **Email sending DORMANT** until an
   email account is added (needs EMAIL_* creds). Verified: a saved search matched 2 deals.
4. **Underpriced report** — generated as part of the static site (PR asset).

Still needed to fully activate: **hosting** (for the SEO pages/site) and a **free email
account** (to actually send alerts). Both are accounts you create.

---

## Free data sources wired — FEMA risk + FHFA price trend — 2026-06-12

Two more FREE (no-key, not billable) sources added to the database:
- **FHFA House Price Index (ZIP-level)** — `src/data_sources/market.py` downloads the
  free FHFA ZIP5 file (19,024 ZIPs) into `data/fhfa_zip5.json` (parsed once; worker
  refreshes ~yearly via `update_market`). Detail page now shows **"Home prices in
  <ZIP>: ▲/▼ X% in <year> · FHFA"**.
- **FEMA risk extended** to **earthquake + overall** rating (NRI fields ERQK_RISKR /
  RISK_RATNG) on top of fire+flood. New `RiskFlags.quake_zone` / `.overall_risk`;
  earthquake badge + insurance note where High.
- **HUD Fair Market Rents** — key slot added (`HUD_FMR_TOKEN` in settings/.env.example);
  needs a FREE token (5-min signup) before wiring its lookup. Dormant until added.
- Verified live on cached Sacramento listings (95827: flood AE + prices −0.8% 2025).
  **0 billable calls.**

---

## Fire/flood RISK flags — the moat — DONE (free, live) — 2026-06-12

Wired the differentiator using **free FEMA data (no key, not billable)**:
- `src/data_sources/risk.py` — FEMA **National Flood Hazard Layer** (flood zone) +
  FEMA **National Risk Index** (wildfire rating). Shared cache, 180-day TTL. Both are
  free ArcGIS REST endpoints (verified live by point).
- Wired into the **Deal Score** (`risk` factor now reflects real fire/flood) and the
  **UI**: red "Flood zone" / "fire risk" badges on cards + an amber insurance-cost
  callout on the detail. Worker refreshes risk each run (`worker.update_risk`).
- Verified live on the 8 cached Sacramento listings — one (95827) is FEMA flood zone
  **AE**: shows the badge + note and its score dropped to 17. **0 billable calls.**

**Paid services we currently have keys for:** RentCast (working) + Google Street View
(key set but 403-parked). Foreclosure Data Hub + Gemini not set. Everything else on the
68-source list needs a new account/key (can't be "wired" without sign-up).

---

## Nationwide switch (copy + groundwork) — 2026-06-12

Scope changed from California-only to **whole U.S.** (decision recorded in
`memory/nationwide-scope.md` + MASTER_SPEC). Done so far (no API calls):
- **App copy** → nationwide: landing headline "Find under-priced **U.S.** homes",
  page title "Deal Finder", "Nationwide listings", disclaimers updated; feed header
  now "U.S. deals"; marketing one-liner → "American homes".
- **Feed filter** city options now derive from the **data actually loaded** (any
  state), not a fixed CA list.
- **Demo foreclosures** diversified to **Cleveland OH + Atlanta GA** to show
  nationwide (Foreclosure Data Hub is flat-fee, all 50 states).
- **foreclosure.sync_listings** now takes optional `state` / `zips` (on-demand any
  U.S. area). Links recolored green (no blue, house style). Key docs updated.
- **Nationwide search built (option A):** a "Search any U.S. city or ZIP" box on the
  feed. Cache-first — cached areas show instantly & free; an un-cached area shows an
  explicit green **"Load … (uses 1 RentCast lookup)"** button that only bills when
  clicked (`rentcast.sync_area()`). Verified with **0 API calls** (Load not clicked).
- **Still cost-smart:** fetch **by searched area on demand**, never bulk-sync the
  country. Remaining: CA references in some secondary docs/README to sweep; the
  Streamlit info box renders blue (could swap for a green box for strict house style).

---

## Foreclosure / bank-owned homes (Foreclosure Data Hub) — code DONE, awaiting $1 key

Added a new data source for cheap bank-owned / foreclosure (REO) homes, since
RentCast carries none. Built to the approved plan; **no live data yet** (needs the
$1 trial key). All verified with NO API calls.

- **Backend:** `src/data_sources/foreclosure.py` (mirrors rentcast.py: fetch → map →
  cache via shared `listings` table with `FC:` id prefix; usage kind `foreclosure`).
  `config/settings.py` reads `FORECLOSURE_API_KEY` (+ `has_foreclosure`). New
  `Listing.est_value` field. `config/cache.yaml`: foreclosure TTL + `sync_foreclosure`
  / `max_foreclosure_per_city`. Worker (`worker/refresh_worker.py`) syncs foreclosures
  after listings — **skipped silently until the key is set**. RentCast's loader now
  excludes `FC:` rows.
- **UI** (`app/pages/0_Browse_Deals.py`): "Bank-owned · foreclosure" badge, a
  "Bank-owned / foreclosures only" filter, and a lighter card showing **bid vs
  estimated value** ("X% below value") + a sold-as-is warning + free HUD/HomePath/
  HomeSteps links. No beds/baths/rent (foreclosure data lacks them).
- **Demo:** until the live feed is connected, 2 clearly-marked DEMO foreclosures show
  so the feature is visible (`app/sample_data.py`). Verified: 8 real + 2 demo rows,
  21%/18% below value, **0 billable calls**. Screenshots in `design_preview/fc_*.png`.
- **Phase A (pending you):** sign up for the $1 trial → add `FORECLOSURE_API_KEY` to
  `.env` → run `.tmp/foreclosure_probe.py` to confirm CA fields, then the worker loads
  real foreclosures. Plan: `~/.claude/plans/synchronous-foraging-hamster.md`.

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

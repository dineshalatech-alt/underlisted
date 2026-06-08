# NorCal Deal Finder — Roadmap & Decisions

A plain-English record of where this project is, the decisions we've made, what's
left to do, and the bigger-picture ideas — so nothing gets lost between sessions.

> Day-to-day build status lives in **[PROGRESS.md](PROGRESS.md)**. Setup steps
> live in **[README.md](README.md)**. This file is the "why" and the "what next."

---

## The vision (one line)

A beginner-friendly tool that finds for-sale homes across Northern California,
shows a real photo, what they could rent for, how good a "deal" they are, and —
in plain words — how much cash you'd really need to buy.

---

## What's already built and working ✅

1. **Phase 1 — Scaffold:** project structure, config files, runnable app.
2. **Phase 2 — Live listings + photos:** real RentCast listings as cards with
   Street View photos, price, beds/baths, sqft, days on market. SQLite cache.
3. **Cost architecture (built for many customers):** shared cache keyed by
   property (not per user), TTL expiry, lazy images, per-user monthly cap,
   Admin/Usage page with cache hit-rate + estimated spend.
4. **Background worker + shared cloud database:** an automated job
   (`worker/refresh_worker.py`) refreshes the cache on a schedule; the cache can
   move from local SQLite to hosted PostgreSQL with one `DATABASE_URL` setting.
   Aerial (satellite) image fetcher already added, with a Street/Aerial toggle on
   the detail panel.

---

## Pending small tweaks (before Phase 3)

From the location discussion — partly done, a couple still open:

- [x] Show the address as plain text (we never dropped a precise pin).
- [x] Aerial / satellite image alongside Street View, with a toggle. *(Done in the
      cost pass; uses the Google key — needs "Maps Static API" enabled on it.)*
- [x] **"View on Google Maps" link** on each card/detail — a free, no-API link.
- [x] **Clearer image labels** for customers: "Street View — curb view" vs
      "Satellite — top-down."

---

## Next planned phase

**Phase 3 — Rent & value estimates** (on the detail page, using the cached
fetchers the worker already populates):
- estimated monthly rent, gross yield, the 1% rule, a rough cap rate,
- list price vs. estimated value (AVM) as % above/below.

Then later: Deal Score, the "cash you really need" breakdown, risk flags
(Cal Fire + FEMA), map view, and the optional AI "imagine remodeled" button.

---

## Our key strategic decisions

### 1. Real estate app FIRST, stock app SECOND
Both ideas are the *same machine* (pull data on a schedule → cache cheaply →
score → show → alert). But:
- **Real estate data is hard to get** (that's our moat); **stock data is cheap but
  the market is crowded** with free incumbents (Yahoo, brokers) and big paid tools.
- **Stocks carry heavier regulation** ("buy this stock" edges toward investment
  advice); a real-estate "screening opinion" is safer.
- **Our clearest edge is in real estate** (see the fire-risk wedge below).
- **Plan:** finish and launch real estate, get real paying customers, *then* build
  the stock app as "app #2" reusing the proven engine. Build the shared pieces
  (cache, worker, alerts, billing, UI kit) as **reusable modules** so app #2 can
  plug in later — but don't split focus before the first app has customers.

### 2. The differentiator — the NorCal fire-risk / insurance angle 🔑
A house can look like a great deal on price but sit in a **high wildfire (or
flood) zone**, where insurance is very expensive or normal insurers won't cover
it — pushing the buyer onto California's FAIR Plan. That can turn a ~$500/yr
insurance bill into hundreds per month, **wrecking the cash-flow math** and even
**blocking the mortgage** (lenders require insurance). So a "cheap" house in the
wrong zone is a trap, not a deal.

The big competitors (PropStream, Mashvisor, DealCheck) show price, comps, rent,
cash flow — but **don't warn about this**. We will, right on the deal card
(amber "fire risk / check insurance cost" badges), using **free public data**:
Cal Fire fire-hazard-severity zones + FEMA flood maps. "We warn you about the
catch nobody told you about" is an honest, trust-building wedge.

### 3. The automation is a scheduled WORKER, not an AI agent
We deliberately chose a plain background job (refresh on a schedule, sleep) — not
an LLM making decisions each run. That keeps cost low and behavior predictable,
which is the whole point at customer scale.

---

## Future ideas (parked, not yet built)

- **Alerts + daily digest engine:** "tell me when a deal in my area drops in
  price" / "email me the best new NorCal deals each morning." Same mechanics as
  stock alerts (watch criteria → fire alert/digest), pointed at houses.
- **Reusable shared core** so a future **stock alert app** sits on the same
  foundation (cache, worker, alerts, billing, theme).
- **Hosting + payments** (Phase 7): accounts, $12.99/mo + 3-day trial, landing
  page. This is when it stops being "runs on my laptop" and goes online.

---

## Honest cautions to keep in mind

- **Going live = ongoing cost + responsibility.** A cloud database + a 24/7
  worker + hosting is a small monthly bill, and the moment it's online a **leaked
  API key or `DATABASE_URL` can be run up by strangers** — keep them in `.env`,
  never commit them anywhere public.
- **Scheduled refresh means data can be a few hours stale.** Fine for a screening
  tool; tune the freshness windows in `config/cache.yaml` if you want fresher.
- **Stocks are more regulated than real estate** — relevant only if/when we build
  app #2. Avoid anything that reads as personalized investment advice.
- **Interrupting Claude Code** stops current work but does **not** undo files
  already written — safest to interrupt while it's waiting for you. Putting the
  project in **Git** gives a reliable "undo" for big changes.

---

*Last updated: 2026-06-07.*

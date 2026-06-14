# Underlisted — Data Sources Master Log

> Goal: the **best data system representing the whole USA**, so customers always find enough homes
> — with rich, trustworthy detail. Owner is willing to pay for sources that genuinely add value.
> Maintained by **Scout**. Companion file: `DATA_SOURCE_REGISTER.xlsx` (sortable). Updated 2026-06-14.

---

## 0. How cost works here (important)
Underlisted uses ONE **shared cache**. The background **worker** fetches each property *once* and
everyone reads the cache. So a paid data source's cost scales with **how many unique homes we cover**
(controlled by the per-city caps in `config/cache.yaml`), **NOT** how many customers visit. That's
why adding paid sources stays predictable and affordable.

---

> ⚠️ **2026-06-14 — RentCast limit hit.** Our free RentCast tier (50 requests/mo) is maxed for this
> billing period (Jun 7–Jul 7). RentCast is our **main listings feed**, so upgrading it is now the
> **#1 paid priority** (see §4 + §6). Customers are unaffected (they read the cache); only the
> worker's refresh is paused until we pick a plan.

## 1. ✅ What we HAVE now (live)
| Source | Data | Coverage | Status |
|---|---|---|---|
| **RentCast** | For-sale listings, value (AVM), rent | Nationwide | Live — ⚠️ FREE tier (50/mo) **maxed**; needs a paid plan for nationwide |
| **FEMA National Risk Index** | Fire, flood, quake + hazards | Nationwide | Live (our moat) |
| **FHFA House Price Index** | ZIP price trend | Nationwide | Live |
| **Freddie Mac PMMS** | Live 30-yr mortgage rate → true monthly cost | Nationwide | Live (no key) |
| **HUD Fair Market Rents** | Area rent benchmark → free fallback rent | Nationwide | Live (token added 6/14) |

This is already a solid free base: listings, value, rent, risk, price trends, and a live mortgage rate.

---

## 2. The honest gaps (to truly be "whole-USA, enough data")
1. **Listings depth & freshness** — RentCast is our only listings feed. The most complete, freshest
   listings live in the **MLS** (gated) or paid aggregators (**ATTOM**).
2. **Value accuracy** — RentCast's AVM is fine; **HouseCanary** is best-in-class and would sharpen our
   core promise (the Deal Score).
3. **Property records depth** — tax history, owner, deeds, liens. **ATTOM** is the deepest single API.
4. **Climate-risk moat** — free FEMA is area-level; **First Street** gives forward-looking, property-level
   flood/fire — a stronger version of our differentiator.

---

## 3. 🟡 Free add-ons (optional keys — low priority)
| Source | Adds | Need |
|---|---|---|
| FRED | Mortgage rate from the Fed | Free key (Freddie already live, so optional) |
| Census (permits/ACS) | New-supply signal; demographics (display-only) | Free key |
| FBI Crime | Area crime (display-only, never scored) | Free api.data.gov key |
| Walk Score | Walkability (display-only) | Free key |

---

## 4. 💵 Paid options — real costs & value (you approve, I wire)
| Source | What it adds | Cost / month | Verdict |
|---|---|---|---|
| **Datafiniti** | Richer property records — cheapest way to TEST | **Free trial** (1,000 recs/2 wk) → from **$119** | ✅ TEST FIRST ($0) |
| **HouseCanary** | Pro-grade value (AVM) → sharper Deal Score | from **$79** ($790/yr) | ✅ RECOMMEND (accuracy) |
| **ATTOM** | 158M properties: listings + tax + deed + owner + AVM | from **$95** | ✅ RECOMMEND (depth + breadth) |
| **Mashvisor** | Investor analytics (cap rate, ROI, short-term-rental) | from **~$129** (usage) | CONSIDER (investor audience) |
| **Regrid** | Nationwide parcels + ownership (map polygons) | **$500–$2,000** (30-day trial) | LATER (only if we add maps) |
| **First Street** | Property-level climate flood/fire (the moat) | Enterprise — **contact for quote** | ⭐ PURSUE QUOTE (differentiator) |
| **BatchData** | 155M properties, 700 data points | from **$1,000** | SKIP for now (too pricey) |

*Exact ATTOM / First Street pricing needs a sales quote. I never sign up or spend — you approve, then
I build the connector (same pattern as RentCast) and the worker fills the shared cache.*

---

## 5. 🔒 MLS — the gold standard for listings (future)
The most complete, freshest for-sale listings come from the **MLS** via **Bridge Interactive** (Zillow
Group — the API itself is free), **Trestle** (CoreLogic), or **MLS Grid**. Catch: each requires an **MLS
membership / data-access agreement** (often a broker relationship + ~$20–50/mo feed dues per MLS, plus
paperwork). This is the biggest quality jump for listings, but it's a project — best pursued once we're
earning. Not blocking now.

---

## 6. ⭐ Scout's recommended build for the BEST whole-USA system
A phased path. Each step is independent — stop wherever the value/cost balance feels right.

0. **KEEP THE LIGHTS ON — `+$74/mo`:** Upgrade **RentCast to Foundation** (1,000 req/mo). It's our
   main listings feed and it's currently maxed, so this comes first. I tune the worker to refresh
   ~weekly so all 33 cities fit comfortably under 1,000 calls. *(Growth $199/mo only if you want daily.)*
1. **VALIDATE (free):** Run the **Datafiniti free trial** (1,000 records) to confirm richer property data
   meaningfully beats RentCast for our listings/detail. $0, ~2 weeks. *(I set it up on your OK.)*
2. **DEPTH — `+$95/mo`:** Add **ATTOM**. Single best nationwide property database (listings + tax + deed +
   owner + AVM, 158M homes). This most directly delivers "enough data so customers always find homes."
3. **ACCURACY — `+$79/mo`:** Add **HouseCanary** AVM to sharpen the Deal Score (our core promise).
4. **MOAT — quote:** Get a **First Street** quote for property-level climate risk → strengthens the
   insurance-risk warning that sets us apart.
5. **INVESTORS — `+$129/mo`:** Add **Mashvisor** when we push the beginner-investor audience.
6. **GOLD-STANDARD LISTINGS — later:** Pursue an **MLS** feed for the freshest, most complete listings
   once revenue justifies the membership + paperwork.

### Budget tiers (monthly)
- **Minimum to run nationwide:** RentCast Foundation → **$74/mo** (keeps listings flowing).
- **Lean serious:** RentCast + ATTOM → **~$169/mo** (listings + deep records).
- **Recommended:** RentCast + ATTOM + HouseCanary → **~$248/mo** (+ accuracy).
- **Full moat:** + Mashvisor + First Street (quote) → **~$380–700+/mo**.

> **RentCast vs ATTOM are different companies.** RentCast (the source we already use, and the one that
> emailed about the limit) is our listings/value/rent feed. ATTOM is a *separate, bigger* paid provider
> we'd ADD for deep tax/deed/owner records. Upgrading RentCast ≠ buying ATTOM.

---

## 7. Change log
- **2026-06-14 (later)** — RentCast free tier (50/mo) hit its limit. Logged RentCast pricing
  (Free 50 · Foundation $74/1,000 · Growth $199/5,000); made a RentCast upgrade the #1 paid step.
  **Owner decision: WAIT for the July 7 reset** (no spend now). Worker stays paused until then; added a
  warning to GO_LIVE_CHECKLIST so the worker isn't turned on before the reset. Customers unaffected (cache).
- **2026-06-14** — HUD Fair Market Rents wired (free fallback rent). Folder + this log created. Register
  refreshed with paid pricing (Regrid $500–2k, Mashvisor ~$129, First Street = quote).
- **2026-06-13** — Live mortgage rate (Freddie Mac, no key) wired into true-monthly-cost. Scout register
  built (25 sources). Nationwide city coverage (12 states).
- **Earlier** — RentCast, FEMA risk, FHFA price trend live (free base).

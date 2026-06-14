# Underlisted — Development Brain (`develop/`)

> The strategy home for the project: goals, the map, and how we win. Living doc — keep updated.
> Readable/visual version: **`Underlisted_Strategy.pdf`** (same folder). Last updated 2026-06-14.

---

## Project goals
- **What:** tell a normal person which U.S. home is actually a good deal — and whether they can
  truly afford it — in **plain English**, nationwide.
- **Core promise:** one **Deal Score (0–100)**, the **true monthly cost**, the **real cash needed**,
  and a **fire/flood insurance-risk warning**. For people who want to **live** in the home, not flip it.
- **Audience:** first-time / normal buyers (primary), beginner investors (secondary).
- **Price:** founding **~$18.99/mo**, locked in for early members.
- **North star:** a buyer in any state opens Underlisted and finds **enough homes, with enough
  trustworthy detail**, to act with confidence.

## The map (how it works + where we optimize)
See `Underlisted_Strategy.pdf` for the visual. In words:

```
THE ENGINE  (we pay once per home; everyone reads the cache)
  Data sources ──▶ Worker ──▶ Shared cache ──▶ What the buyer sees
  (RentCast,        (fetch     (cheap,          (Deal Score · Afford? ·
   FEMA, HUD,        once on    instant)          Risk · True monthly cost ·
   FHFA, rate)       schedule)                    Cash needed)
                                                        │ powers
                                                        ▼
THE FUNNEL  (turn visitors into members)
  Free "Check a Deal" ──▶ Waitlist / email ──▶ $18.99 / mo member

OPTIMIZE (gold): + ATTOM / First Street (deeper data + climate moat) ·
  ⭐ "Can I Afford It?" personal score (our moat) · in-house deal videos (cheap reach)
```
The key insight: the expensive part (live data) is already built, so our biggest wins are cheap to add.

## How we win over other businesses
Every serious competitor serves **investors** (cap rate, BRRRR, motivated sellers, jargon) or is
market-level (ZIP forecasts). **None serve the normal first-time buyer in plain English.** We own
that abandoned lane.

| Player | Really for | Their language |
|---|---|---|
| Mashvisor | Investors | "Mashmeter", occupancy |
| PropStream ($79–299) | Wholesalers | motivated sellers, skip tracing |
| DealCheck ($14) | Investors | cap rate, CoC, IRR, DCR |
| DealMachine | Flippers | driving-for-dollars, off-market |
| Reventure | Market watchers | ZIP price forecasts |
| **Underlisted** | **First-time BUYERS (live-in)** | **"Can you afford THIS home? Is it risky?"** |

## Optimization priorities (in order)
1. **Build "Can I Afford It?" + Surprise-Cost** — personal affordability badge + budget-killer
   warnings (insurance range, tax, PMI, HOA) + plain "why this score". Highest-leverage moat;
   mostly logic on data we already pay for. (Atlas leads.)
2. **Deepen the data** — upgrade RentCast (after July 7 reset); add ATTOM (depth) + First Street
   (climate moat) when budget allows. See `research/data_sources/`.
3. **In-house deal videos** — "find out if you can afford that house in 30 seconds" → cheap
   nationwide reach, lower cost per customer. See `MARKETING_PLAN.html`.

## Where we are (pointers)
- Running build log: `../PROGRESS.md`
- Data-source plan + costs: `../research/data_sources/`
- Go-live steps: `../GO_LIVE_CHECKLIST.html`
- Marketing: `../MARKETING_PLAN.html`, `../MARKETING_COST_ANALYSIS.html`

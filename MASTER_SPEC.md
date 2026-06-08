# MASTER_SPEC — California Deal Finder

The single source of truth for **what** this product is, **how it's priced**, and
**which decisions are locked in**. Day-to-day build status lives in
[PROGRESS.md](PROGRESS.md); the "why" and bigger picture live in
[ROADMAP.md](ROADMAP.md); the path to launch lives in
[ROADMAP_TO_LAUNCH.md](ROADMAP_TO_LAUNCH.md).

*Last updated: 2026-06-07.*

---

## One-line product

A dead-simple, beginner-friendly, **visual** tool that finds under-priced
**California** homes, gives each a clear 0–100 deal score, and explains — in plain
English — what it'd really cost to buy. Built to run **cheaply per customer**.

---

## Pricing (LOCKED)

**Founding-member intro offer:**
- **$12.99/month for the first 12 months**, then **$29.99/month**.
- New customers who sign up **after** the intro period start at **$29.99/month**.
- 3-day free trial · cancel anytime.

**Approved pricing copy (use everywhere):**
- Standard line: **"$12.99/mo for your first 12 months, then $29.99/mo — cancel anytime"**
- Hook line: **"Lock in $12.99/mo for a year — goes up to $29.99 soon."**

> Change history: standard price raised from $24.99 → **$29.99** on 2026-06-07.
> Intro ($12.99 for 12 months) unchanged.

**Tiers to consider later (NOT now):**
A two-tier structure once the product is established —
- **Basic / Browse** — browse the feed, deal scores, rent & value, cash-needed.
- **Premium** — **deal alerts + saved searches** (this is the premium *investor*
  feature; alerts are what serious users pay up for). Possibly fire/flood risk
  detail, ZIP heatmap, side-by-side compare.

Decision deferred until we have paying customers; record only.

---

## Locked product decisions

- **California only** for now (more states later).
- **Low data cost per customer** is a core constraint: shared cache keyed by
  property, precompute scores, never fetch on page load, lazy images, per-user cap.
  (See [PROGRESS.md](PROGRESS.md) / cost architecture.)
- **Fair Housing safe:** scoring/filtering **never** uses demographic or
  "neighborhood quality" signals.
- The differentiator wedge is the **fire / flood insurance risk warning** the big
  players don't show (CalFire + FEMA, free public data). See ROADMAP.md.
- Automation is a **scheduled worker**, not an LLM agent.

---

## Approved to build LATER — visual layer ON TOP of the Deal Score

These are **APPROVED in principle but NOT to be built now.** Build them only
**after the 0–100 Deal Score exists and is solid**, layered on top of it. (Full
context for each lives in [COMPETITIVE_IDEAS.md](COMPETITIVE_IDEAS.md), Parts 3–4.)

| # | Feature | Builds on | Status |
|---|---|---|---|
| 1 | **Letter grade / stars** derived from the 0–100 score (A+→D or ★1–5) | Deal Score | ✅ Approved — build later |
| 2 | **Visible "good deal" threshold line** on the score gauge | Deal Score gauge | ✅ Approved — build later |
| 3 | **Estimate shown as a low–high range** everywhere (not one fake-precise number) | value/rent estimate fields | ✅ Approved — build later |
| 4 | **Colored status badges on cards** — Great deal / Price cut / New / fire-risk dot | Deal Score + price history + risk data | ✅ Approved — build later |
| 5 | **Price-history as colored event rows** (Listed / Price cut / Sold, green/red deltas) | price_history | ✅ Approved — build later |
| 6 | **ZIP-level deal heatmap with a metric dropdown** (bigger build — stage it last) | ZIP-level aggregates | ✅ Approved — build later, larger effort |

**Rule:** do not start any of these until the Deal Score is built and confirmed.
They are enhancements *on top of* it, not replacements.

---

## Marketing one-liner (approved)

> **"Zillow shows you homes; DealCheck makes you do the math. We just tell you
> which California homes are actually good deals — and why."**

Full marketing copy, hooks, and the video plan live in
[MARKETING_NOTES.md](MARKETING_NOTES.md) and
[ROADMAP_TO_LAUNCH.md](ROADMAP_TO_LAUNCH.md) (Phase 6).

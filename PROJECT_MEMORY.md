# PROJECT MEMORY — START HERE

**Open this file first to resume. No re-explaining needed.**
*Last updated: 2026-06-07.*

---

## Where we are right now (plain English)

We're building a **nationwide (U.S.), beginner-friendly deal-finder app** that finds
under-priced homes and explains them simply. The whole pipeline works: **RentCast
is proven live**, real Sacramento listings are loaded, and the app looks polished —
landing page, mobile feed, detail page with a "how much cash you need" section,
Tabler icons, logo. Pricing: **$12.99/mo for 12 months → $29.99 now → rising to $44.99 later**.
The one cosmetic thing still broken is **Google photos (403)** — parked on purpose;
the app works fine with grey placeholders.

## Next step (do this next)

**Build/validate the Deal Score (0–100) on the real CACHED listings** — no new API
calls. The scoring module exists and renders on sample data; the next move is to
run it on the 8 real cached Sacramento listings, confirm the numbers look right,
and lock it in as the product's centerpiece. **Only after that** do we layer the
approved visuals on top (letter grade, threshold line, range, badges, price-history
rows — see MASTER_SPEC).

---

## Mind map — the whole project at a glance

```
U.S. DEAL FINDER (nationwide)
│
├── ✅ DONE
│   ├── Phase 1 — Scaffold (structure, config, runnable app)
│   ├── Phase 2 — Live listings as cards  ← RentCast PROVEN LIVE
│   ├── Cost architecture (shared cache, TTL, per-user cap, Admin/Usage)
│   ├── Worker + SQLite⇄Postgres switch (scheduled refresh, not an AI agent)
│   ├── Phase 3 — Rent & value estimates (yield, 1% rule, cap rate, AVM)
│   ├── "How much cash you really need" breakdown
│   ├── Visual polish (landing, feed, detail, Tabler icons, logo/favicon)
│   ├── Pricing locked ($12.99→$29.99) + plan files written
│   └── Competitive research (9 rivals studied)
│
├── ⏳ IN PROGRESS
│   └── DEAL SCORE (0–100)  ← THE NEXT STEP
│       module built + shows on SAMPLE data;
│       must be validated on REAL cached listings and locked in as the centerpiece
│
├── ⛔ PARKED
│   └── Google Street View / satellite photos (403)
│       project + billing link + APIs look correct; suspect key restriction or
│       inactive billing ACCOUNT. Cosmetic — grey placeholders work fine.
│
└── 🔭 TO DO (after Deal Score)
    ├── Visual layer ON TOP of score: letter grade/stars, "good deal" threshold
    │   line, estimate as low–high range, status badges, price-history event rows,
    │   (bigger) ZIP deal heatmap                         [APPROVED — build later]
    ├── Risk flags: CalFire fire + FEMA flood  ← the differentiator wedge
    ├── Map view
    ├── Deal alerts + saved searches            ← flagship PREMIUM / retention feature
    ├── AI "imagine remodeled" (Gemini)
    └── Accounts / payments / hosting (Phase 7)
```

---

## The other key files (what each holds)

| File | What's in it |
|---|---|
| **[MASTER_SPEC.md](MASTER_SPEC.md)** | Single source of truth: locked pricing, "tiers later" note, and the APPROVED-but-build-later visual features (on top of the Deal Score). |
| **[ROADMAP_TO_LAUNCH.md](ROADMAP_TO_LAUNCH.md)** | Phased path to launch (Phases 1–7). **Phase 6 = the marketing-video plan.** |
| **[MILESTONES.md](MILESTONES.md)** | Dated log of big wins + the parked Google-photos fix (with the exact Cloud Shell command). |
| **[COMPETITIVE_IDEAS.md](COMPETITIVE_IDEAS.md)** | Research on 9 rivals + data-saving tricks, visual ideas, ADD/SKIP feature calls, and our "what makes us different" angle. |
| **[PROJECT_STATUS.md](PROJECT_STATUS.md)** | Detailed honest snapshot + full file tree. *(Note: written before the live RentCast test — its "untested/no live call" warnings are now out of date for RentCast.)* |
| **[TOOLS_AND_SETUP.md](TOOLS_AND_SETUP.md)** | Tools/services, exact run commands, working rules, the parked Google fix, and key decisions. |
| **[MARKETING_NOTES.md](MARKETING_NOTES.md)** | The one-liner + ad/video hooks. |
| **[PROGRESS.md](PROGRESS.md)** | Running build log, newest on top. |
| **[ROADMAP.md](ROADMAP.md)** | The strategic "why" (fire-risk wedge, real-estate-before-stocks). |
| **[README.md](README.md)** | Beginner setup guide. |

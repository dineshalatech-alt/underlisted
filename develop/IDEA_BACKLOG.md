# 💡 Idea Backlog & Roadmap — Underlisted

**Owner:** Theo (Head of Product & Roadmap) · **Everyone can read & add** · Updated each working day.

This is the project's single "don't lose an idea" list. It does two jobs:

1. **Parking Lot** — the moment anyone (the owner OR any teammate) has an idea while we're
   busy on something else, drop it here in ONE line. Don't stop the current task. Don't
   polish it. Just park it so it isn't lost.
2. **Roadmap** — Theo reviews the Parking Lot, and the good ideas graduate into the ranked
   roadmap below (with who it's for, the cost, and a priority).

### How we use it (the habit)
- **Capture anytime:** see an idea → add a Parking Lot line → keep working.
- **Theo triages:** moves parked ideas into the Roadmap (ranked) or marks them *Parked/Skip*
  with a one-line reason. Nothing is ever silently deleted.
- **End-of-day review (Atlas):** when we close the day, Atlas scans the Parking Lot against what
  we actually did and asks "did we miss anything?" — then updates this file + the daily team log.

> Status keys: **Idea** (raw) · **Next** (do soon) · **Building** · **Done** · **Parked** (good,
> but later / gated on money or a decision) · **Skip** (decided no — reason given).

---

## 🅿️ Parking Lot (raw ideas — add yours here, one line)

- _(add new ideas here — e.g. "Idea: add a 'school-free' crime info layer (info-only) — raised by Dinesha")_

---

## 🗺️ Roadmap (Theo-ranked)

| # | Idea | For whom | Owner | Cost | Status | Priority | Note |
|---|------|----------|-------|------|--------|----------|------|
| 1 | RentCast upgrade → one controlled worker run to fill the DB with real homes | All buyers | Atlas/Penny | 💵 paid (quota maxed → ~Jul 7) | Next | 🔴 High | The #1 paid go-live step. Don't run before quota resets (overage). |
| 2 | Finish Stripe/Payhip → switch the $18.99 Subscribe button on | Business | Atlas | — | Next | 🔴 High | Paste link into `config/cache.yaml: checkout_url`. |
| 3 | Mirror the "Why Underlisted" section to the static `site/` | Prospects | Juliet | free | Next | 🟠 Med | App + site should match. |
| 4 | Mirror a teaser of the investor calculators to `site/` (SEO) | Beginner investors | Serena/Quill | free | Idea | 🟠 Med | High-intent search traffic. |
| 5 | 8 SEO articles on the calculator terms (cap rate, 1% rule, ARV, 70% rule…) | Beginner investors | Quill/Serena | free | Idea | 🟠 Med | Titles drafted by Quill. |
| 6 | Real **comps** (recently-sold prices) in the app + a comps calculator | Investors & buyers | Theo→Forge | 💵 paid (ATTOM) | Parked | 🟡 Low | Needs paid sold-price data. Revisit when ATTOM is approved. |
| 7 | Wire **ATTOM** (AVM + sold history) into scoring/detail/worker | All buyers | Theo→Forge | 💵 free trial (lapses ~Jul 14) | Idea | 🟠 Med | Decide HOW to blend it before the trial ends. |
| 8 | Per-county property-tax rate (free Census/state data) to tighten the afford range | Buyers | Forge | free | Idea | 🟡 Low | Makes "true monthly cost" sharper. |
| 9 | Teaser of the "Can I Afford It?" badge in the free `2_Check_A_Deal` funnel | First-time buyers | Forge | free | Idea | 🟡 Low | Pulls funnel users toward the moat. |
| 10 | Verify a domain in Resend so alert emails reach real customers | All buyers | Atlas | free | Idea | 🟠 Med | Today only the owner gets test emails. |
| 11 | Free enrichment keys (FRED / Census / Walk Score) | Buyers | Forge | free | Idea | 🟡 Low | Nice-to-have data upgrades. |

---

## ✅ Recently shipped (so we can see momentum)

- **Free Investor Tools** — rental cash-flow + fix-&-flip/ARV calculators (Theo spec → Forge build
  → Vera test). 2026-06-14.
- **7 investor terms** added to the shared glossary → in-app tooltips + public learn page; Investor
  Tools page links to the 1-minute guide (Quill content + Forge wire-up). 2026-06-14.
- **In-app "What does this mean?" tooltips** across the deal screen (Juliet). 2026-06-14.
- **"Can I Afford It?" moat** — afford badge + surprise-cost panel (Forge/Vera). 2026-06-14.

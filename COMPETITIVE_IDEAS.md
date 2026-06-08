# Competitive Ideas — What the Best Deal-Finders Do, and What I Should Steal

**Type:** Research only. Nothing was built or changed. This is a menu for you to
review and decide from.
**Date:** 2026-06-07
**My app's north star:** dead-simple, beginner-friendly, *visual*, California-only,
**low data cost** per customer.

> Note on sources: this comes from each competitor's **public** marketing, help,
> and blog pages plus well-known public product behavior. A few exact UI colors
> couldn't be confirmed without live screenshots — flagged where that's the case.
> Some "estimate" and "score" details are inferred, not insider knowledge.

---

## ✅ Decision log — APPROVED to build LATER (2026-06-07)

The following are **approved in principle but NOT to be built now.** They layer
**ON TOP of the 0–100 Deal Score** and may only be built **after the Deal Score
exists and is confirmed solid.** Also tracked in
[MASTER_SPEC.md](MASTER_SPEC.md).

1. **Letter grade / stars** from the 0–100 score (A+→D or ★1–5).
2. **Visible "good deal" threshold line** on the score gauge.
3. **Estimate shown as a low–high range** everywhere.
4. **Colored status badges on cards** — Great deal / Price cut / New / fire-risk dot.
5. **Price-history as colored event rows** (Listed / Price cut / Sold, green/red deltas).
6. **ZIP-level deal heatmap with a metric dropdown** — *bigger build, stage it last.*

Everything else in Parts 3–4 below remains a candidate, not yet approved.

---

## Part 1 — Competitor snapshots

### PropStream — *the data + map tool*
- **Best features:** 160M+ property database, 165+ filters, 20+ prebuilt lead lists, built-in ROI/flip/rehab calculators, an AI assistant that answers "is this a good investment?"
- **Visuals:** A **color heat map** is the signature — click a metric (value, price growth, rental value, foreclosure rate) and the map "lights up" with a color legend. Map pins show value + photo. **Named ordinal scores** instead of raw numbers: *Foreclosure Factor* (Very Low → Very High) and a *condition grade* (Disrepair → Luxury).
- **Glance-ability:** Named word-tiers (Very Low → Very High) are easier for beginners than a number. Color heat map needs no reading.
- **Cost signals:** Scores are **precomputed**; the heat map paints **aggregated regional data**, not per-property live fetches.

### DealMachine — *driving-for-dollars + AI score*
- **Best features:** GPS "driving for dollars," **AI Vision Builder** that scores properties from satellite + street-view images, 700+ list filters, friendly AI assistant ("Alma").
- **Visuals:** **One AI score per property on a 10–90 scale** — set a threshold (default 75) and matching homes auto-drop into a list. **Traffic-light route colors:** green = driven in last 6 months, yellow = 6–12 mo, red = 1–2 yrs. Comps shown as 3 big single numbers (Est. Value, Avg $/sqft, Avg Price), not dense tables.
- **Glance-ability:** One number per property is the simplest "worth it?" signal there is. Traffic-light colors need zero explanation.
- **Cost signals:** AI scores are **batch-computed for a drawn area once**, then filtered. Route colors come from stored timestamps (free).

### DealCheck — *the calculator + charts*
- **Best features:** Fast deal analyzer (cash flow, cap rate, ROI, BRRRR, flips), up to 20 comps, **side-by-side property comparison**, one-click shareable PDF/online reports.
- **Visuals:** **Time-series projection charts** are the headline — watch cash flow / equity / profit grow year by year. Big metric tiles up top; change an input and everything recalculates live. **No single deal-score gauge or red/green verdict** — leans on clean numbers. *(That's a gap I can beat.)*
- **Glance-ability:** Charts let a beginner *watch* a deal grow instead of parsing IRR. "MAO" (max allowable offer) gives one actionable "don't pay more than X."
- **Cost signals:** All projections are **client-side formula math — zero API calls**. Data imported once, then analyzed offline. Comps capped at 20 (bounded, cacheable).

### Mashvisor — *the heatmap leader (most relevant to me)*
- **Best features:** Neighborhood **heatmap**, long-term-vs-Airbnb calculator, neighborhood analytics, **Mashmeter Score**, Market Finder.
- **Visuals:** Gradient **green → yellow → red** map; **one dropdown switches the whole map** between metrics (score, cap rate, rent, price, occupancy, days-on-market…). Click a colored area → property dots appear. **Mashmeter Score = 0–100% plus a letter grade A+ → D.**
- **Glance-ability:** "Green = good, red = bad" on one map is the whole pitch. Letter grade is instantly understood. One dropdown keeps it from showing 12 numbers at once.
- **Cost signals:** Heatmap + scores are **precomputed at the neighborhood level** and cached; per-property numbers only load when you drill into a dot. (This is *exactly* my cost architecture.)

### Roofstock — *turnkey rentals + star ratings*
- **Best features:** Curated pre-vetted rentals, **Neighborhood Rating (1–5 stars)**, per-listing pro formas, inspection reports.
- **Visuals:** **1–5 star badge** on every listing (5 = lowest risk). Compact stat row on cards (rent, cap rate, gross yield, appreciation). Interactive pro-forma sliders.
- **Glance-ability:** Everyone understands 1–5 stars with no explanation — it compresses ~12 risk variables into one familiar symbol.
- **Cost signals:** Star ratings **precomputed per neighborhood, reused** across all listings there. Listings carry stored estimates; sliders recalc client-side.

### Reventure — *newer, very glance-able forecast app*
- **Best features:** **Home Price Forecast Score (0–100)** for every ZIP/city/county, "Overvalued %" metric, national ZIP-level heatmap. Free tier = current trends, $39/mo = the forecast.
- **Visuals:** Full-US **choropleth heatmap**, zoom nation → ZIP. Forecast Score gauge with a **hard threshold: below 50 = declining, above 50 = growing.** Overvalued % with 📈/📉 direction arrows.
- **Glance-ability:** The **"above 50 / below 50" line is the cleanest verdict I found** — one number, instant buy/avoid read.
- **Cost signals:** Scores **precomputed per ZIP on a batch schedule** — one pass paints the whole map. Free tier serves cached trend data; expensive forecast is paywalled (caps cost per free user).

### Zillow — *the consumer giant*
- **Best features:** **Zestimate** (instant value on every home, on AND off market), Rent Zestimate, saved searches, price/tax history, photo-first listings, map search.
- **Visuals:** **List price = big bold number; Zestimate sits beside it with a low–high RANGE** (the range conveys uncertainty for free). **Zestimate history = a line chart "like a stock chart."** **Price-history = a vertical list of dated events** (Listed / Price cut / Sold) with $ and % deltas. **Map price pins** print the actual price ("$625K") and **cluster into count bubbles** when zoomed out. Photo-corner **badges**: New, Price cut, Open house.
- **Glance-ability:** Card = hero photo → one line `price · beds · baths · sqft` → address. Badges sit on the photo so status reads first. Deep data hidden in accordions.
- **Cost signals (my #1 lesson):** Zestimate is **precomputed in batch**, refreshed a few times a week, served from cache — *never computed per page view.* Pins cluster; photos lazy-load.

### Redfin — *the snappier portal*
- **Best features:** **Redfin Estimate** (updated daily for listed homes), **Hot Homes** flag (predicts fast sellers), **Compete Score (0–100)** for how competitive an area is.
- **Visuals:** **Hot Homes = a bold flame badge** on the map pin and across the first photo. **Compete Score = a 0–100 number with a color/word band** ("Very Competitive"). Estimate shown with a history graph + sale-to-list ratio. Clean, fast map.
- **Glance-ability:** One bright HOT badge says "act fast" before any numbers. 0–100 score with a color band is beginner-perfect.
- **Cost signals:** Estimates are batch-scored and **refreshed by activity — active/hot listings often, the long tail rarely.** Hot Homes / Compete Score are stored model outputs.

### Newer / honorable mentions
- **Homes.com** — deliberately simple, "for people overwhelmed by data." Closest in *philosophy* to my app; study its restraint.
- **Trulia** — neighborhood map *overlays* (schools, crime, commute) done lightly.
- **2026 trend** — Zillow/Redfin/Realtor.com all added **natural-language search** ("3-bed under $700K near good schools"). Direction of travel, not a cheap copy.

---

## Part 2 — Data-saving / efficiency techniques I could adopt

These all match (and reinforce) my existing cost architecture: *shared cache keyed
by property, never fetch on page load, precompute, lazy-load.*

1. **Precompute every score offline, serve from cache — never compute per page view.** Zillow/Redfin/Mashvisor/Reventure all do this. My Deal Score should be computed once per listing in the worker and stored, so the feed renders from cache with **zero** live calls. *(Already my model — keep enforcing it.)*
2. **Refresh by activity, not uniformly (Redfin).** Active / high-score / recently-viewed listings refresh often; the long tail refreshes rarely or never. Cheap, big savings. → a per-listing "tier" in the worker's TTL logic.
3. **Aggregate at the ZIP/neighborhood level, not per property (Mashvisor / Reventure / PropStream).** A heatmap or "this ZIP scores B+" is computed **once per ZIP** and reused across every listing in it — dramatically cheaper than per-home data, and it's a whole new visual for almost no cost.
4. **Estimate-first, live-data-on-demand.** Show the cached AVM estimate up front; only fire a live per-property comps fetch when the user explicitly drills in. Everyone does this; I already do — extend it to *every* expensive field.
5. **Client-side math is free (DealCheck).** Cash-needed, cap rate, yield, projections, "what-if" sliders — all pure formulas on already-cached numbers. Add as many interactive recalcs as I want at **zero data cost.**
6. **Bound every fetch (DealCheck caps comps at 20).** Hard caps on comps/photos/listings-per-city keep cost predictable. *(I already cap listings per city and per-user lookups.)*
7. **Map pin clustering + lazy photos (Zillow/Redfin).** If I add a map, cluster pins into count bubbles when zoomed out and lazy-load photos on swipe — less rendered, less shipped.
8. **Gate the most expensive data behind the paywall (Reventure).** Free/preview users see cached trends; the costliest live data is a paid feature. Protects quota *and* creates the upsell.

---

## Part 3 — Better ways to represent data visually (specific)

Ranked by *clarity-per-dollar* for a beginner. I already have a score gauge,
price-vs-value bar, and a "why it scored X" breakdown — these build on that.

| Visual | What it is | Why it helps a beginner | Cost |
|---|---|---|---|
| **0–100 deal-score gauge with a hard threshold line** | My gauge + a visible "70 = good deal" marker (Reventure's "above/below 50", Redfin Compete Score) | One glance = buy/skip verdict | Free (have it) |
| **Letter grade or 1–5 stars badge** | Translate the 0–100 score into **A+→D** or **★★★★☆** on each card (Mashvisor / Roofstock) | Words/stars read faster than numbers | Free |
| **Price-vs-value bar** | Horizontal bar: list price marker vs estimated-value marker, green if below value (have a version) | Instantly shows "priced under what it's worth" | Free |
| **Estimate shown as a low–high range** | "Worth ~$610K (range $580–640K)" instead of a single fake-precise number (Zillow) | Teaches uncertainty, builds trust | Free (have the range data) |
| **Price-history as dated event rows** | Vertical list: *Listed $X → Price cut –$10K → …* with green/red deltas (Zillow) | Easiest "is the seller motivated?" read; no chart needed | Cheap (need price_history — I track price drops already) |
| **Sparkline value trend** | Tiny line of value over time, "like a stock chart" (Zillow/Redfin) | Up/down at a glance | Cheap if I store history |
| **Color heatmap by ZIP** | CA map shaded green→red by avg deal score / yield, one **metric dropdown** (Mashvisor) | "Where are the deals?" in one look; a flagship visual | Medium — needs ZIP aggregates (computed once) |
| **Traffic-light / colored status badges on the photo** | "Great deal," "Price cut," "New," fire-risk dot — on the card image (Redfin Hot, Zillow) | Status reads before any text | Free |
| **Compact stat row, everything else hidden** | Card = photo + `price · beds · baths · sqft` + one badge; deep data in accordions (Zillow/Roofstock) | Keeps the feed calm and scannable | Free (have most) |
| **Side-by-side compare (2 homes)** | Two cards, key numbers aligned, deltas highlighted (DealCheck/Roofstock) | Removes the mental math of ranking | Cheap (client-side) |
| **What-if sliders** | Drag down-payment / rate / rent, watch cash-needed & cash flow recalc live (DealCheck/Roofstock) | Makes it interactive and personal | Free (client math) |

---

## Part 4 — New feature ideas: ADD or SKIP

**ADD (cheap, on-strategy, beginner-clear):**
- **ADD — Letter grade / stars from my existing score.** One line of code over data I have; huge glance-ability. *Reasoning: free, universally understood.*
- **ADD — Hard "good deal" threshold line on the gauge.** *Reasoning: turns a number into a verdict; free.*
- **ADD — Price-history as colored event rows.** *Reasoning: best "motivated seller" signal; I already detect price drops.*
- **ADD — Estimate shown as a low–high range everywhere.** *Reasoning: honesty + trust; I already have the range fields.*
- **ADD — Colored status badges on cards** (Great deal / Price cut / New / fire-risk dot). *Reasoning: free, reads before text.*
- **ADD — Side-by-side compare two homes.** *Reasoning: pure client-side; high "feels premium" value.*
- **ADD — What-if sliders on the cash-needed / cash-flow section.** *Reasoning: free client math; makes it personal.*
- **ADD (phase 2) — ZIP-level deal heatmap with one metric dropdown.** *Reasoning: flagship Mashvisor-style visual, computed once per ZIP — fits my low-cost model. Bigger build, so stage it.*
- **ADD (light) — One "neighborhood vibe" element from FREE/public data** (e.g. CalFire fire risk, FEMA flood — already on my roadmap). *Reasoning: differentiator, public data, no RentCast cost. Keep it to one or two dots, not Trulia's 30 overlays.*

**SKIP (pro-only, expensive data, or beginner-confusing):**
- **SKIP — Driving-for-dollars / GPS routes (DealMachine).** *Reasoning: pro investor workflow; off-strategy for beginners.*
- **SKIP — Skip tracing, direct mail, dialer, CRM (PropStream/DealMachine).** *Reasoning: pro lead-gen, not deal discovery.*
- **SKIP — 165+ filters / 700+ list filters.** *Reasoning: overwhelms beginners; I want a calm feed, not a query builder. A handful of filters max.*
- **SKIP — Foreclosure/pre-foreclosure/tax-lien lists.** *Reasoning: distressed-data sources, extra cost, advanced concepts.*
- **SKIP — Airbnb/short-term-rental projections (Mashvisor).** *Reasoning: STR is complex + regulation-heavy; long-term rent only keeps it simple. Revisit later.*
- **SKIP (for now) — IRR / ROE / BRRRR / 35-year projections (DealCheck).** *Reasoning: jargon. Keep cash-needed + simple yield + cap rate only.*
- **SKIP (for now) — AI image scoring from satellite (DealMachine).** *Reasoning: needs paid vision calls + image fetches I'm avoiding. The "imagine remodeled" idea is already parked separately.*
- **SKIP — Natural-language / ChatGPT search.** *Reasoning: trendy but adds LLM cost + complexity; my feed + a few filters is simpler. Watch the trend.*
- **SKIP — 12-month price *forecasts* (Reventure).** *Reasoning: forecasting is its own hard, liability-prone product. I describe the *current* deal, not predict the market.*

---

## Part 5 — What makes us different

Every competitor is built for **investors who already know the jargon**, or is a
**giant data portal** that buries you in numbers, filters, and tools. Two clear gaps:

1. **DealCheck has great math but *no single verdict* — no score gauge, no
   red/green "is this good?"** I lead with exactly that.
2. **Zillow/Redfin show a price and an estimate but never tell you if it's a
   *deal*** — they're search engines, not deal finders. I do the judging for you.

**Where I win — simplicity and clarity:**
- **One verdict, not a spreadsheet.** A 0–100 score → a color → a letter grade →
  one line of plain English. Mashvisor/Reventure prove beginners want *a verdict*;
  I give it per-listing, not just per-ZIP.
- **Plain English over jargon.** "How much cash you'd really need," "priced 11%
  under what it's worth" — no IRR, no BRRRR, no cap-rate-first.
- **Calm, mobile-first feed.** Best deal first, photo + 4 facts + one badge.
  Homes.com's restraint, aimed at *deals* instead of just *listings*.
- **Honest by design.** Estimate ranges (not fake-precise numbers), a visible
  "why it scored X," sample/real labels, and **Fair Housing-safe scoring** that
  never uses demographic or "neighborhood quality" signals — a line PropStream's
  crime-weighted scores and Roofstock's risk stars don't hold.
- **Cheap to run = cheap for the customer.** Precomputed, cached, California-only.
  The whole product is built around the low-cost architecture the big players use
  internally but never pass on to a $13/mo beginner.

**One-liner:** *Zillow shows you homes; DealCheck makes you do the math. We just
tell you, in plain English, which California homes are actually good deals — and
why.*

---

## Suggested next steps (you decide — nothing built yet)

- **Quickest wins (all free, all on-strategy):** letter-grade/stars badge,
  threshold line on the gauge, estimate-as-range, colored status badges,
  price-history event rows.
- **Then:** side-by-side compare + what-if sliders (client-side, no data cost).
- **Bigger, stage it:** ZIP-level deal heatmap with a metric dropdown.
- **Already on roadmap, keep:** CalFire/FEMA risk dots (free public data).

Tell me which of these to turn into a build phase and I'll plan it — still no API
calls, cache-first, one phase at a time.

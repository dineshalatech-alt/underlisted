# CLAUDE.md — Underlisted (project guide & memory)

> This file loads automatically each session. It's the front door for the project:
> what it is, what's done, what's next, how it's built, and which accounts/tools we use.
> Plain language — the owner (Dinesha) is non-technical and on Windows/PowerShell.
> Keep this updated as we go.

---

## 1. What this is

**Underlisted** — a beginner-simple website/app that finds **under-priced U.S. homes**.
Type a city, every home gets a plain-English **Deal Score (0–100)**; green = good deal.
Unique angles (our moat): **plain-English simplicity**, a **fire/flood insurance-risk
warning**, the **true monthly cost**, and the **real cash you'd need**. Nationwide (USA).

- **Brand name:** Underlisted  ·  **Domain:** underlistedhomes.com
- **Audience:** first-time / normal home buyers (primary), beginner investors (secondary)
- **One-liner:** "Zillow shows you homes; other tools make you do the math. We just tell
  you which U.S. homes are actually good deals — and why."

### Pricing (locked)
$12.99/mo intro (first 12 months) → **$29.99/mo now** → planned rise to **$44.99/mo** later.
Hook: *"Lock in $12.99/mo for a year — the price is rising to $44.99 soon."*

---

## 2. Current status (2026-06-14)

| Piece | Status |
|---|---|
| 🌐 Public SEO site + **waitlist email capture** (Netlify Forms) | ✅ Live |
| 🏷️ Own domain **underlistedhomes.com** (A `@`→75.2.60.5, CNAME `www`→netlify) | ✅ Connected (HTTPS finishing) |
| 📧 **Email alerts** (Resend) | ✅ Live (test-sender only until a domain is verified in Resend) |
| 📛 Brand renamed Deal Finder → **Underlisted** | ✅ Done (app, site, marketing) |
| 📣 **Marketing kit** (`MARKETING_KIT.html`) + **promo video** (`PROMO_FULL.mp4`) | ✅ Ready |
| ☁️ Code **cloud-ready** (`st.secrets`) + pushed to **GitHub** (now **public**) | ✅ `github.com/dineshalatech-alt/underlisted` |
| 🖥️ **App online** (Streamlit Cloud) | ✅ LIVE: `underlisted-gidalbx5x5vlaeuvqncwpp.streamlit.app` (keys in st.secrets) |
| 🗄️ Hosted **Postgres** (Supabase) + `DATABASE_URL` | ✅ **LIVE** — connected via **Session pooler** (`postgres.nemvzwcxlhyjsjaappkt@aws-1-us-east-1.pooler.supabase.com:5432`). `DATABASE_URL` in Streamlit Secrets; Admin/Usage shows backend = **PostgreSQL**. Fixed a Postgres transaction-abort bug (migrations now run each in their own transaction — `src/cache/db.py:connect()`). DB connected but **empty** until the worker runs. |
| 🔁 Auto-refresh **worker** (GitHub Actions cron) | ✅ **Code complete** (`.github/workflows/refresh.yml` + `worker/refresh_worker.py`, daily/manual). ⏳ Not switched on yet — needs GitHub Actions Secrets, and **RentCast quota is maxed → worker PAUSED until July 7 reset** (don't run before then = overage). Fills shared Postgres when on. |
| 💳 **Payment button** | ✅ **Built** — config-driven Payhip "Subscribe" button, dormant until a link is pasted into `config/cache.yaml: checkout_url`. Founding price **$18.99/mo** (landing). Never change selling logic without asking. |
| 🗂️ **Data sources** (mostly free) | ✅ Live: RentCast (listings/value/rent), FEMA risk, FHFA trend, **live mortgage rate** (Freddie Mac, no key), **HUD Fair Market Rents** (free fallback rent). Nationwide = **12 states**. Paid options (ATTOM/HouseCanary/First Street) await owner OK — see `research/data_sources/`. |
| 🧭 **Strategy / moat** | ✅ Set: *for buyers who'll LIVE in the home, not flip it* + insurance-risk + **"Can I Afford It?"** = the moat to build next. See `develop/`. |
| 🎨 **Design** | Landing is **dark-luxe** (black + DM Sans + gold) with a **"Why Underlisted"** section; warm palette still on other pages. Owned by **Juliet**. |

---

## 3. The plan / next steps (in order)

1. **Build the "Can I Afford It?" moat** ← **RESUME HERE.** Owner approved. Personal affordability
   badge (enter income/cash/debts → green/amber/red + "you'd have $X left/month") + a **Surprise-Cost**
   panel (insurance range, property tax, PMI, HOA) + a plain "why this score". Highest-leverage
   differentiator and needs **NO RentCast** (logic on data we already have). Files Atlas flagged:
   `src/cache/db.py` (small user-prefs table), `app/pages/0_Browse_Deals.py` (badges), the deal-score
   module. Show estimates as labelled ranges (trust); keep personal inputs out of logs.
2. **RentCast upgrade** — quota maxed; **paused until July 7 reset** (or upgrade sooner: Foundation
   $74/1,000 req, Growth $199/5,000). Then I run ONE controlled worker test to fill the DB with real
   nationwide homes. The #1 paid step. **Don't run the worker before this is sorted (overage).**
3. **Go-live gate** — after RentCast: add GitHub Actions Secrets + run the worker; create the Payhip
   $18.99 product + paste link into `config/cache.yaml: checkout_url`. See `GO_LIVE_CHECKLIST.html`.
4. **Mirror the "Why Underlisted" section to the static `site/`** so app + website match (Juliet).
5. **Optional/later:** free keys (FRED/Census/crime/Walk Score), paid data (ATTOM/HouseCanary/First
   Street — owner OK), **verify a domain in Resend** (so alert emails reach real customers).

> Living docs: `develop/` (goals, map, how-we-win, strategy PDF) · `team/` (roster + improvement loop) ·
> `research/data_sources/` (data plan + costs) · `PROGRESS.md` (session timeline, newest on top).

---

## 4. How it's built (architecture)

- **Stack:** Python 3.12 + **Streamlit** multipage app. **SQLite** locally /
  **PostgreSQL** in the cloud (auto-selected by `DATABASE_URL`).
- **Cost architecture (important):** ONE **shared cache** keyed by property (never per
  user). The app **never fetches on page load** — it reads cache only. A **background
  worker** populates the cache on a schedule. Per-user monthly lookup cap. This keeps
  per-customer API cost low. (See memory: cost-architecture.)
- **Data-source pattern:** each source mirrors `rentcast.py` — fetch raw → map to a
  `Listing` → cache via `db.upsert_listing`. Add a new source by copying that shape.
- **Deal Score (0–100):** weighted factors (value discount, rent yield, days-on-market,
  risk), rescaled over whatever factors are available.
- **Secrets resolver:** `config/settings.py:_secret()` reads an **env var first**
  (`.env` locally / host env), then falls back to **Streamlit `st.secrets`** (lazy import,
  so the worker / CLI tools never load Streamlit). Same code works locally and on cloud.
- **SEO:** `tools/gen_site.py` writes plain static HTML to `site/` (Streamlit can't rank;
  static pages can). The waitlist `<form>` uses **Netlify Forms** (no backend).

### Key files
- `config/settings.py` — settings + `_secret()` resolver; reads YAML in `config/`.
- `src/cache/backend.py` (SQLite/Postgres switch) · `src/cache/db.py` (schema, cache,
  listings, saved_searches/alert_log, usage).
- `src/data_sources/` — `rentcast.py` (listings/value/rent, billable), `foreclosure.py`
  (bank-owned, dormant until key), `risk.py` (FREE FEMA fire/flood/quake), `market.py`
  (FREE FHFA ZIP price trend), `streetview.py` (photos, 403 parked).
- `src/notify/email_sender.py` — Resend sender + alert digest.
- `worker/refresh_worker.py` — background refresh: listings → foreclosure → risk → market →
  match saved-search alerts → **email digests** → stale value/rent. Cost-guarded.
- `app/main.py` (landing) · `app/pages/0_Browse_Deals.py` (feed+detail) ·
  `1_Admin_Usage.py` · `2_Check_A_Deal.py` (free funnel) · `3_My_Alerts.py` (saved searches).
- `tools/gen_site.py` → `site/` (index, deals-in-<city>, report-underpriced, thanks).
- `.tmp/make_video.py` — records the running app into a 9:16 MP4 (Playwright + ffmpeg).

---

## 5. Accounts, services & tools used

| Service | What for | Notes |
|---|---|---|
| **GitHub** | Code host | repo `dineshalatech-alt/underlisted` (**private**). `gh` CLI is logged in as `dineshalatech-alt`. |
| **Netlify** | Hosts the static `site/` | project name `findrealestatedeals`; live at findrealestatedeals.netlify.app; **Forms → "waitlist"** holds signups. Re-deploy = drag `site/` folder onto Deploys. |
| **Namecheap** | Domain registrar | underlistedhomes.com (order 205162350). DNS: A `@`→`75.2.60.5`, CNAME `www`→`findrealestatedeals.netlify.app`. |
| **Resend** | Sends alert emails | `RESEND_API_KEY` in `.env`. Test sender `onboarding@resend.dev` only reaches the owner until a domain is verified. |
| **RentCast** | Listings, value, rent | `RENTCAST_API_KEY` (real). Billable → only the worker calls it. |
| **Google Street View** | House photos | `STREETVIEW_API_KEY`. **403 parked** (billing/restriction). |
| **Streamlit Community Cloud** | Will host the app | deploy `app/main.py`. Needs repo access + secrets. |
| **Supabase** (planned) | Free Postgres | will provide `DATABASE_URL`. |
| **Foreclosure Data Hub** | Bank-owned homes (optional) | NOT subscribed; trial expired; $49/mo. `FORECLOSURE_API_KEY` blank. |
| **Kling 3.0 (Artlist) + Nano Banana** | Marketing video/images | made the green-USA "homes/pins" map intro (image → image-to-video). |
| **ffmpeg (imageio-ffmpeg) + Playwright** | Video pipeline | `.tmp/make_video.py` records the app demo; ffmpeg stitches map intro + demo → `PROMO_FULL.mp4` (9:16, no audio). |

---

## 6. Conventions & gotchas (follow these)

- **Secrets:** only in `.env` (gitignored) or Streamlit `st.secrets`. NEVER print key values
  in chat or commit them. `.env.example` is the blank template.
- **Repo hygiene:** `.gitignore` excludes `.env`, `*.db`, `.streamlit/secrets.toml`,
  `*.mp4/*.mov/*.webm`, and `*.pdf` (personal paperwork). Local `data/cache.db` is untracked.
- **Brand/theme:** **light green `#1D9E75` + black text, NEVER blue** anywhere (fills, fonts,
  charts, links). Greens: `#1D9E75` / deep `#0F6E56` / fill `#E1F5EE`. Amber `#E08A00`,
  Red `#C0392B` for warnings only. Logo: `app/assets/logo.png`.
- **Fair Housing:** scoring/filtering must NEVER use demographic or "neighborhood-quality"
  signals. Crime/demographic data is info-only, never scored.
- **Data sources:** licensed APIs only — never scrape Zillow/Redfin/Realtor/competitors.
- **Windows/PowerShell:** run Python via `.venv/Scripts/python.exe`. Hooks/scripts must be
  cross-platform.
- **Don't break saved data formats** or touch selling/payment/landing logic without asking.
- **Readable deliverables:** any list/table/report → give a readable file (xlsx/HTML/PDF),
  not just `.md` (a `.md` source can accompany it).

---

## 7. Related docs & memory

- **Plans/specs:** `MASTER_SPEC.md`, `ROADMAP_TO_LAUNCH.md`, `GROWTH_STRATEGY.md`,
  `COMPETITIVE_IDEAS.md`, `PROJECT_MEMORY.md`, `PROGRESS.md` (running log).
- **Marketing:** `MARKETING_KIT.html` (ads/posts/email), `MARKETING_NOTES.md`,
  `MARKETING_CLIP.md`, `PROMO_FULL.mp4`, `MARKETING_CLIP.mp4`.
- **Setup:** `SETUP_GUIDE.md` / `.html` (host + email + foreclosure key).
- **Auto-memory** (`~/.claude/.../memory/`): cost-architecture, nationwide-scope,
  direct-competitors, go-live-pending, app-name.

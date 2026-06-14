# Session handoff — Juliet (design) · 2026-06-14

Plain-English summary of this chat so you can **clear it and continue later**.
I'm **Juliet**, the design/brand agent for Underlisted. (Teammates: **Atlas** builds,
**Serena** grows, **Scout** researches.)

---

## What we did this session (in order)

1. **Created Juliet** — a permanent design agent saved at `.claude/agents/Juliet.md`.
   In any future chat you can say *"Juliet, …"* and she has the design context.

2. **Lifted the old color rule.** The old "light green only, never blue" brand rule is
   **off** for the look of the app/website. Full color freedom now.

3. **First look — "Warm & trustworthy":** cream + coral + gold. Used your **Kling video**
   as a looping hero background (shrunk from **12 MB → 548 KB** so it loads fast).
   Recolored the house **logo** to warm coral/gold (the green originals are backed up).

4. **Early-bird pricing (landing page only):** show **~~$99.99/mo~~ → $18.99/mo**
   as a *Founding-member rate*, styled as a **gold banknote** (gold-foil shimmering price,
   ornate border, corner `$` seals, "serial number"). The hero pill matches.

5. **All buttons → gold**, and a faint **dollar-bill pattern** woven into the page background.

6. **Final look — "Dark luxe"** (what the landing looks like now): copied the Apple-style
   dark theme you shared — **black background, off-white text, DM Sans font** — while keeping
   the gold buttons, the gold `$18.99` banknote, and the dollar-bill pattern (gold-on-black =
   luxury). Hero fades into black; feature cards are dark glass with a gold edge.

7. **"Why Underlisted" content section** was added to the landing (frame quote → 5 benefit
   cards → bold contrast block → trust strip), matching the dark-luxe style.

---

## What the landing looks like now (top → bottom)

- **Hero:** your Kling video looping behind a dark scrim · house logo · headline
  *"Find under-priced U.S. homes in seconds"* · early-bird pill (~~$99.99~~ **$18.99/mo**).
- **Two gold buttons:** *Start 3-day free trial* · *Browse deals (free preview)*.
- **Why people use it** — 3 dark-glass feature cards.
- **How it works** — 3 steps.
- **Why Underlisted** — frame quote + 5 benefit cards + contrast block + trust strip.
- **Gold "Founding-member" banknote:** ~~$99.99/mo~~ → **$18.99/mo**, shimmering gold.
- Black page throughout, with a faint gold dollar-bill watermark in the background.

---

## See it / run it again

The app runs locally. If the preview is closed, restart it from the project folder:

```powershell
.venv\Scripts\python.exe -m streamlit run app/main.py
```

Then open **http://localhost:8501**. (The gold price shimmers; icons render correctly
in a real browser even if a screenshot shows a small box.)

---

## Important notes & guardrails kept

- **Payment / checkout logic untouched.** I only changed how prices *look*, not billing.
  Real billing still comes from the Payhip link in `config/cache.yaml: checkout_url`.
- **0 billable API calls** this whole session (pure visual work).
- The **$18.99 / $99.99** wording is **landing-page only**. Other pages and the marketing
  files still show the older **$12.99 → $29.99 → $44.99** ladder (see "Next" below).

---

## Files changed this session

| File | What changed |
|---|---|
| `.claude/agents/Juliet.md` | **New** — the design agent |
| `app/main.py` | The whole landing redesign (dark luxe, hero video, gold buttons, banknote, Why-Us section) |
| `app/assets/theme.py` | Added the warm palette (still used by other pages) |
| `.streamlit/config.toml` | Dark theme + static-file serving for the hero video |
| `app/static/hero.mp4` + `hero_poster.jpg` | **New** — the slimmed Kling hero loop |
| `app/assets/logo.png` / `favicon.png` | Recolored (green originals saved as `*_green_backup.png`) |
| `PROGRESS.md` | Logged each step |
| Screenshots in `design_preview/` | `dark_top.png`, `dark_feat.png`, `note_card.png`, etc. |

---

## Next steps (when you're ready — just ask Juliet)

- **"Take dark luxe app-wide"** — make Browse Deals / Check a Deal / My Alerts match the
  dark landing (they still use the warm cream look).
- **"Do the public website (site/)"** — apply the same look to the static SEO site.
- **"Take $18.99 everywhere"** — sweep the old $12.99/$29.99 pricing out of the other
  pages + marketing so everything agrees.
- Optional: update **CLAUDE.md §6** to record the lifted color rule (still says green-only).

---

*Tip: when you start the next chat, this file + `PROGRESS.md` are the fastest way to
catch up. Say "Juliet, read the latest session handoff" and I'll continue from here.*

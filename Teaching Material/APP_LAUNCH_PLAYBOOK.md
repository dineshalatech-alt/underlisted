# 🧩 App Launch Playbook — the repeatable recipe

> The exact method we used for **Underlisted**, written so it works for **every future app/website**.
> Plain language for a non-technical founder. Pair it with `LEARNING_MAP_ARROWS.pdf` (the picture).
> An automation helper exists too: the **app-launch-guide** agent (see end).

---

## The helper team (the standard free stack)
| Helper | Job | Free tier | Connects by |
|---|---|---|---|
| **GitHub** | Stores the code | Free | 👤 login |
| **Streamlit Cloud** *(or Vercel/Render)* | Runs the app online | Free | 👤 login (reads GitHub) |
| **Supabase** | Database (remembers data) | Free | 🔑 `DATABASE_URL` |
| **Netlify** | Public site + signups | Free | 📍 DNS + drag-drop |
| **Namecheap** *(or Cloudflare)* | Domain name | ~$10/yr | 📍 DNS records |
| **Resend** | Sends emails | Free 3k/mo | 🔑 `RESEND_API_KEY` |
| **(data/API providers)** | Whatever data the app needs | varies | 🔑 API key |

## The 3 ways things connect (memorize)
- 🔑 **API key** — a secret password the helper gives you (RentCast, Resend, Supabase).
- 👤 **Login** — you authorize one service to read another (GitHub → app host).
- 📍 **DNS** — address records that point your domain at your host (Namecheap → Netlify).
- 🔒 Keys ALWAYS live in a **secret box**: `.env` (local), host **Secrets** (live), CI **Secrets** (worker).

---

## The launch sequence (do in this order)

### 0. Decide the idea (ask first)
- **Q:** What does the app DO in one sentence? Who is it for?
- **Q:** What's the brand name? → check the **.com on Namecheap** + check no company owns the name (web search). Pick a distinctive name if the obvious ones are taken.

### 1. Build the app locally
- Scaffold the code; keep secrets in a **`.env`** (gitignored from day one).
- Use a **secret resolver** so the same code reads `.env` locally OR host Secrets in the cloud.

### 2. Public page + waitlist FIRST (fastest "live")
- Generate a simple static site; add a **waitlist email form** (Netlify Forms — no backend).
- Host it by dragging the folder to **Netlify**. You're collecting emails the same day.

### 3. Buy the domain + connect it
- Buy the **.com** on Namecheap. Connect to Netlify with **DNS** (A `@`→host IP, CNAME `www`).
- Wait for HTTPS (the padlock) to finish.
- **Q:** Public or private GitHub repo? (Public = free app hosting is easy + no secrets exposed since `.env` is ignored. Private = strategy stays hidden but needs host permission.)

### 4. Put the code on GitHub
- **Safety sweep BEFORE pushing:** confirm `.env`, keys, big videos, and personal PDFs are gitignored. Never commit secrets.
- Push with `gh repo create`.

### 5. Deploy the app (host)
- Connect the host (Streamlit Cloud) to the GitHub repo. Main file + branch.
- Paste keys into the host's **Secrets** box (TOML). 
- **Gotcha:** repo "not found" usually = wrong account or private-repo permission. Fix the account or make it public.

### 6. Database (Supabase)
- Create a free project; **SAVE the database password**.
- Copy the **Session pooler** connection string (IPv4 — works on host AND CI). Replace `[YOUR-PASSWORD]`.
- Add it to host Secrets as `DATABASE_URL`. App auto-creates its tables on first connect.
- **Verify:** Supabase → Table Editor shows the new tables.

### 7. Background worker (keep data fresh, keep cost low)
- A scheduled job (**GitHub Actions cron**) does the paid API calls + fills the shared database.
- The **app only READS** the database — never fetch on page load (this is what keeps cost per user low).
- Add the same keys as **GitHub Actions Secrets**.

### 8. Payment (last)
- **Q (ask before wiring):** which provider — Payhip / Stripe / Lemon Squeezy?
- Most simple apps: a hosted "Subscribe" checkout link + a light access approach.

### 9. Growth
- SEO static pages, short promo videos, launch email, communities. Post consistently.

---

## 🔒 Safety rules (never break these)
- Keys live ONLY in `.env` / Secrets. **Never** paste a key in chat, email, or a screenshot.
- Use **licensed APIs only** — never scrape Zillow/Redfin/portals/competitors.
- (For housing) scoring must **never** use demographic / "neighborhood-quality" signals — Fair Housing.
- Don't break a saved data format; don't change selling/payment without asking.

## ✅ One-line checklist
Name+domain → local app+`.env` → waitlist site (Netlify) → connect domain (DNS) → push to GitHub
→ deploy app + Secrets → Supabase + `DATABASE_URL` → worker (CI cron) → payment → growth.

## 🤖 The "good questions" to always ask
1. One-sentence purpose + who it's for? 2. Brand name — is the .com free & name unused? 3. Public or
private repo? 4. Which data/API providers (free first)? 5. Did you SAVE the DB password? 6. Which payment
provider? 7. What's the price? 8. Who sends the email (test sender vs your domain)?

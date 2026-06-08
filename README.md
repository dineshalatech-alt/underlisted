# NorCal Deal Finder 🏡

Find for-sale homes across **Northern California**, see a real photo of each one,
what it could rent for, how good a "deal" it is, and — in plain English — **how
much cash you'd really need to buy it.**

> ⚠️ **Everything in this app is an ESTIMATE.** It is a screening tool, not
> investment advice, not a loan offer, and not an appraisal. Always verify with a
> licensed lender, contractor, and local real-estate agent before acting.

This README is written for someone who has **never coded before.** Follow it
top to bottom. Copy/paste the commands exactly.

---

## What this app does (in plain words)

For each home for sale, it shows you:

1. **A real photo** of the house (from Google Street View).
2. **The facts** — price, beds, baths, size, year built, days on the market.
3. **Rent estimate** — what it might rent for each month, plus simple yardsticks
   (gross yield, the "1% rule", a rough cap rate).
4. **Value check** — is it listed *above* or *below* its estimated value?
5. **Risk flags** — fire zone? flood zone? (California insurance matters.)
6. **A Deal Score (0–100)** — with a "why it scored this" breakdown so you can
   trust it.
7. **"How much cash you really need"** — one big number, then a friendly breakdown
   of down payment, closing costs, and reserves.

---

## The 6 steps to get it running

You only do steps 1–4 **once**. After that, you just run step 6 whenever you want.

| Step | What you do | Time |
|------|-------------|------|
| 1 | Install Python | 5 min |
| 2 | Download/open this project | 2 min |
| 3 | Install the app's helpers | 2 min |
| 4 | Get your API keys & paste them in | 15 min |
| 5 | Edit which cities to search (optional) | 2 min |
| 6 | Run the app | 10 sec |

We are building this **iteratively**. Right now Steps 1–3 and 6 work and the app
launches with a welcome screen. The live data, scoring, and finance pages get
turned on as we build each module together.

---

## Step 1 — Install Python (the language this app is written in)

**Windows (your computer):**

1. Go to <https://www.python.org/downloads/>
2. Click the big yellow **"Download Python 3.12"** button.
3. Run the installer. **VERY IMPORTANT:** on the first screen, check the box
   **"Add python.exe to PATH"** at the bottom *before* clicking Install.
4. Click **Install Now**, wait, then **Close**.

**Check it worked.** Open **PowerShell** (press Start, type `PowerShell`, hit
Enter) and type:

```powershell
python --version
```

You should see something like `Python 3.12.x`. If you see an error, restart your
computer and try again (the PATH change needs a restart sometimes).

---

## Step 2 — Open the project folder

This project lives in:

```
c:\Users\dines\OneDrive\Documents\14. Real Estate
```

In PowerShell, go there by typing:

```powershell
cd "$HOME\OneDrive\Documents\14. Real Estate"
```

(The quotes matter because the folder name has a space and a dot in it.)

---

## Step 3 — Install the app's helpers (its "ingredients")

Apps rely on small pre-built tools called *packages*. We keep them in their own
private box (a "virtual environment") so they never mess with the rest of your
computer.

Run these **one line at a time**:

```powershell
# 1. Create the private box (folder named ".venv")
python -m venv .venv

# 2. Turn it on
.\.venv\Scripts\Activate.ps1

# 3. Install everything the app needs
pip install -r requirements.txt
```

> If line 2 gives a red "running scripts is disabled" error, run this once, then
> retry line 2:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

When it's done, your PowerShell prompt will start with `(.venv)`. That means the
box is "on." You turn it on again each new session with line 2 above.

---

## Step 4 — Get your API keys (the app's passwords to outside services)

An **API key** is just a long password that lets the app ask another company's
service for data. We store yours in a private file called `.env` that **never
leaves your computer** and is **never shared**.

Make your private file by copying the example:

```powershell
Copy-Item .env.example .env
```

Now open `.env` in Notepad:

```powershell
notepad .env
```

You'll get these keys and paste each one after the `=` sign. **No spaces, no
quotes.**

### 4a. RentCast (listings, value & rent estimates) — *required*
- Go to <https://developers.rentcast.io>, sign up, and (per your plan) get your
  API key. You said you'll be on a **paid plan**.
- Paste it as: `RENTCAST_API_KEY=your_key_here`

### 4b. Google Street View (the real house photos) — *required*
- Go to <https://console.cloud.google.com>, create a free project.
- Search "Street View Static API" and click **Enable**.
- Go to **APIs & Services → Credentials → Create credentials → API key**.
- Paste it as: `STREETVIEW_API_KEY=your_key_here`

### 4c. Google Gemini (optional "imagine remodeled" pictures & branding) — *optional*
- Go to <https://aistudio.google.com/apikey>, click **Create API key**.
- Paste it as: `GEMINI_API_KEY=your_key_here`
- You can skip this one for now; the app still runs without it.

Save and close Notepad.

> 🔒 **Your keys stay private.** The `.env` file is listed in `.gitignore`, so it
> is never uploaded or shared. Never paste your keys into a chat or a webpage.

---

## Step 5 — Choose your cities (optional)

Open `config/cities.yaml` to add or remove target cities/zips. It starts with
Sacramento, Stockton, Modesto, Vallejo, Antioch, and Oakland. Just follow the
pattern already in the file.

You can also tweak:
- `config/financing.yaml` — interest rates, down-payment %, closing-cost %.
- `config/scoring_weights.yaml` — how the Deal Score is calculated.

---

## Step 6 — Run the app

```powershell
streamlit run app/main.py
```

Your web browser opens automatically to the app. To stop it, click back in
PowerShell and press **Ctrl + C**.

---

## Keeping costs low (important for many customers)

This app is built so that **lots of customers cost very little**:

- **Shared cache.** All listings, photos, and estimates are cached **once per
  property** (not per user). If 500 people view the same Sacramento home, that's
  **one** data lookup and **one** photo download total — everyone else is served
  from the cache for free.
- **No fetching on page load.** Opening the app never calls a paid API. Fresh data
  comes from a **scheduled daily sync** (below) or the manual Refresh button.
- **Lazy photos.** A card shows no photo until you click **Show photo** or open the
  listing. Aerial/value/rent load **only when you open a property.**
- **Per-user monthly cap.** A configurable limit (`config/cache.yaml`) stops any
  single heavy user from running up the bill.
- **Admin / Usage page.** Watch billable calls, image fetches, your cache hit-rate,
  and estimated spend — open it from the left page menu.

### The background worker (the automated refresh job)

The **worker** is a small program that refreshes the cache on its own — no user
and no page-load triggers it. On each run it pulls new/changed listings, updates
any value/rent estimates that have gone stale, and saves it all to the shared
cache. (It does **not** download photos unless you turn that on in
`config/cache.yaml`.)

**Run it once, right now (safe to repeat):**
```powershell
python -m worker.refresh_worker
```
**Catch price changes on older homes (do this ~weekly):**
```powershell
python -m worker.refresh_worker --full
```
**Keep it running on a schedule (it refreshes every `schedule_hours`):**
```powershell
python -m worker.refresh_worker --loop
```
You can also click **▶️ Run worker now** on the **Admin / Usage** page.

Each run is logged (cities done, new/updated counts, billable calls used) — see
that history on the Admin / Usage page.

### Schedule the worker on Windows (so it runs daily by itself)

1. Press Start, type **Task Scheduler**, open it.
2. **Create Basic Task** → name it "Deal Finder Worker" → **Daily**.
3. Action: **Start a program**.
   - Program/script:
     `C:\Users\dines\OneDrive\Documents\14. Real Estate\.venv\Scripts\python.exe`
   - Add arguments: `-m worker.refresh_worker`
   - Start in: `C:\Users\dines\OneDrive\Documents\14. Real Estate`
4. Finish.

### When the app is hosted (later)

Once the app lives on a server, you schedule the worker one of these ways:
- A **cron job** (Linux servers) running `python -m worker.refresh_worker` daily, or
- A small always-on **worker process** running `python -m worker.refresh_worker --loop`
  (most hosts — Railway, Render, Fly.io — let you add a "worker" alongside the web app), or
- Your host's built-in **scheduled jobs** (e.g. Render Cron Jobs, Railway Cron).

---

## The shared cloud database (for when you have customers)

Right now the cache is a **local file** (`data/cache.db`, SQLite) — perfect for
testing on your computer. When you launch to real customers, the worker and every
user need to share **one** database in the cloud so the cache is truly shared.

**You do not need to change any code** — just set one value.

1. Create a free PostgreSQL database. Easiest options (pick one):
   - **Supabase** → <https://supabase.com> (you're already using it elsewhere)
   - **Neon** → <https://neon.tech>
   - **Railway** → <https://railway.app>
2. Each gives you a **connection string** that looks like:
   `postgresql://user:password@host:5432/dbname`
3. Put it in your `.env` file:
   ```
   DATABASE_URL=postgresql://user:password@host:5432/dbname
   ```
4. Install the database driver once (already in requirements):
   ```powershell
   pip install -r requirements.txt
   ```
5. Run the worker once to create the tables in the cloud:
   ```powershell
   python -m worker.refresh_worker
   ```

That's it. The app and worker now share the same cloud cache. To go back to local
testing, just blank out `DATABASE_URL` again. The Admin / Usage page shows which
database is active at the top.

---

## Project layout (so you know where things live)

```
14. Real Estate/
├─ README.md                 ← this file
├─ PROGRESS.md               ← running log of what we've built
├─ requirements.txt          ← list of helper packages
├─ .env.example              ← template for your keys (safe to share)
├─ .env                      ← YOUR real keys (private, never shared)
├─ .gitignore                ← tells git what to keep private
│
├─ config/                   ← things YOU can edit, no coding
│  ├─ cities.yaml            ← which cities/zips to search
│  ├─ financing.yaml         ← interest rates, down %, closing %, reserves
│  ├─ scoring_weights.yaml   ← how the Deal Score is weighted
│  └─ settings.py            ← loads the above + your keys
│
├─ src/                      ← the "brain" (kept separate from the screens)
│  ├─ models.py              ← the shape of a listing's data
│  ├─ cache/                 ← SQLite cache so we don't re-bill the APIs
│  ├─ data_sources/          ← RentCast, Street View, Gemini, risk maps
│  ├─ scoring/               ← the Deal Score logic
│  └─ financing/             ← the "cash you really need" math
│
├─ app/                      ← the screens you see
│  ├─ main.py                ← the app's front door
│  └─ assets/                ← logo, colors, generated-once images
│
└─ data/                     ← the cache database lives here (auto-created)
```

**Why split it up?** This is meant to become a real product. Keeping the data,
scoring, and finance logic separate from the screens means we can later add
accounts, payments, and hosting without rewriting everything.

---

## Disclaimers (please read)

- **Estimates only.** Values, rents, and cash figures are estimates — not
  investment advice and not a loan offer. Verify with licensed professionals.
- **Deal Score is a screening tool**, not a guarantee.
- **Fair Housing:** the scoring and filters deliberately avoid any demographic or
  "neighborhood quality" signals that could proxy for protected classes.

---

## Where we are right now

See **[PROGRESS.md](PROGRESS.md)** for the current state and the next step.

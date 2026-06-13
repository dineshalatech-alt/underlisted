# Setup Guide — get online + turn on email (free, ~10 min)

> **Come back here later.** Two free signups switch on the last pieces. A nicely
> formatted version is in **SETUP_GUIDE.html** (double-click to open/print).

---

## Where we left off (resume point)

The growth features are **built and working locally** (see PROGRESS.md): the SEO
static site (`site/`), the free "Check a deal" page, and saved searches + deal
alerts. **Two free accounts** are all that's left to make them live:

| To switch on | You do | Then |
|---|---|---|
| **SEO site live** (people can find it on Google) | Host the `site/` folder (Part 1) | Send me the link |
| **Alerts actually email** | Add a free Resend key (Part 2) | Tell me **"email done"** |
| *(separate)* **Real foreclosures** | Add `FORECLOSURE_API_KEY` ($1) | Tell me it's in `.env` |

---

## Part 1 · Put your deal pages online (free) — ~5 min

Makes the `site` folder a real website. Easiest way: **Netlify Drop** (drag-and-drop).

1. Open your site folder:
   `C:\Users\dines\OneDrive\Documents\14. Real Estate\site`
   *(File Explorer → paste that path in the address bar → Enter.)*
2. Go to **https://app.netlify.com/drop**
3. **Drag the whole `site` folder** onto the page and drop it. Wait ~30 seconds.
4. You get a **live link** like `something.netlify.app` — that's your website.
5. Click **Sign up** (free) to keep it, rename it, and later add your own domain.

**Update the site later:** run `python tools/gen_site.py`, then drag the `site`
folder onto Netlify again. (We can automate this.)

**Your own name** (e.g. `yourbrand.com`): buy one (~$10/yr at Namecheap or
Cloudflare) and connect it in Netlify → "Domain settings." Optional, anytime.

---

## Part 2 · Turn on email alerts (free) — ~5 min

Lets the app email "a deal just dropped!". We'll use **Resend** (free, 3,000/mo).

1. Go to **https://resend.com** → **Sign up** (free). Verify your email.
2. Dashboard → **API Keys** → **Create API Key** → **Copy** it (starts `re_`).
3. Open your **`.env`** file and add this line, then save:
   ```
   RESEND_API_KEY=re_your_key_here
   ```
4. Tell me **"email done"** — I'll wire the alert emails and send you a test first.

**Note:** for testing, Resend sends from a built-in address. To email real customers
from *your* brand later, "verify your domain" in Resend (a 5-min step once you have a
domain).

---

## Part 3 · After you're done

- Send me your **live site link** (optional) — I'll help polish it.
- Say **"email done"** once the Resend key is in `.env` — I'll switch on alerts.

🔒 **Keep keys private:** paste them only into the `.env` file — never into chat.

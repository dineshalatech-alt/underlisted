# 🎬 Teaching Video Clips — Plan & Scripts

> A short-form course: "How websites connect to build an app." Each clip teaches **one idea**
> in 30–60 seconds, using **Underlisted** as the real example. Record later; this is the storyboard.
> Matches the slides in `TEACHING_SLIDES.html` / `.pdf` (one slide per clip).

---

## Format (keep it consistent)
- **Length:** 30–60 sec per clip · **Shape:** 9:16 vertical (Reels/TikTok/Shorts) or 16:9 for YouTube
- **Style:** show the matching slide on screen + your voice. Optionally screen-record the real
  website (GitHub, Streamlit, Supabase) while you talk.
- **Brand:** light green (#1D9E75), black text, never blue. Same look as the slides.
- **Hook first:** start every clip with a question or a "you don't need to be a coder" promise.

---

## Clip 1 — "Building an app is like opening a shop" 🏪
- **Hook:** "You don't need to be a coder to understand how apps are built. Here's the secret."
- **Say:** Building an app = opening a shop. One person can't do it all, so you hire helpers.
  Each website is one helper with one job. Your app is the manager.
- **Show:** Slide 2 (the shop idea).
- **End line:** "Next: meet the helpers."

## Clip 2 — "Meet the helpers" 🧰
- **Hook:** "Every app uses a little team. Here's mine."
- **Say:** Walk the table — GitHub (recipe book), Streamlit (kitchen), Supabase (filing cabinet),
  Netlify (billboard), Namecheap (address), Resend (post office), RentCast (supplier).
- **Show:** Slide 3 (the table). Optionally flash each real website.
- **End line:** "But how do they actually talk to each other? One word: keys."

## Clip 3 — "What is an API key?" 🔑  ← most important clip
- **Hook:** "This one word confuses everyone. Let me make it simple."
- **Say:** A key is a secret password a helper gives you, so your app can prove "I'm allowed."
  Like a VIP badge. No key = "I don't know you, go away."
- **Show:** Slide 4. Maybe show copying a key from a dashboard (blur the real value!).
- **End line:** "But where do you keep these keys? Carefully."

## Clip 4 — "Keep your keys in a locked box" 🔒
- **Hook:** "Posting your key in public is like shouting your house code in the street."
- **Say:** Keys live in a locked box — the `.env` file on your computer, or Streamlit Secrets
  in the cloud. Never paste them in chats, emails, or screenshots.
- **Show:** Slide 5. Show the Streamlit Secrets box (with values blurred).
- **End line:** "Now the magic — connecting any two websites is always the same 3 steps."

## Clip 5 — "Connect any 2 websites in 3 steps" 🔗
- **Hook:** "Once you learn this pattern, you can connect anything."
- **Say:** 1) Helper gives you a key. 2) You put it in your secret box. 3) Your app shows it
  every time. That's it — RentCast, Resend, the database, all the same.
- **Show:** Slide 6.
- **End line:** "One key is a little different — the database key."

## Clip 6 — "The database key (address + password)" 🗄️
- **Hook:** "This key looks scary but it's just a note with directions."
- **Say:** Most keys are a password. DATABASE_URL also says *where* the filing cabinet is —
  who, the secret, where, the door, which cabinet. The app reads it, goes there, files the data.
- **Show:** Slide 7 (the labelled `postgresql://...` line).
- **End line:** "Let's see it all work together with one customer."

## Clip 7 — "The journey of one customer" 🚶
- **Hook:** "Here's what happens, start to finish, when someone uses your app."
- **Say:** Google → underlistedhomes.com (Namecheap → Netlify) → join waitlist (Netlify saves it)
  → open app (Streamlit) → deals from Supabase (filled by RentCast) → Resend emails them.
  Every arrow is unlocked by a key.
- **Show:** Slide 8.
- **End line:** "And that's how every modern app is wired."

## Clip 8 — "Recap (save this)" ✅
- **Hook:** "If you remember nothing else, remember this."
- **Say:** Each website = a helper with one job. A key = a secret badge. Keep keys in a locked box.
  Give your app the right keys, and it runs the whole shop.
- **Show:** Slide 9 (recap).
- **End line:** "Follow for the next one — we build a real app step by step."

---

## Recording tips
- Use the slide as the background; talk over it (phone or screen recorder).
- Keep ONE idea per clip — don't cram.
- Re-record the hook until the first 2 seconds grab attention.
- Caption everything (most people watch on mute).
- Post consistently; double down on whichever clip gets the most views.

## Possible future expansions (new clips/courses)
- "What is a domain & DNS?" · "What is hosting?" · "Free tools to launch an app for $0"
- "What is a database?" · "How AI image/video tools work" · "How I made a promo video with AI"

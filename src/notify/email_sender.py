"""
Email sender — delivers deal alerts through Resend.

Why Resend: dead-simple HTTP API, generous free tier (3,000 emails/month), and no
SMTP setup. We only need the key in `.env` as RESEND_API_KEY.

Nothing here runs unless a key is present (settings.has_resend). If the key is
missing every call returns {"ok": False, "skipped": True} so the worker and app
keep running quietly — exactly how the feature stayed dormant before.

Run a quick test (sends one email to yourself):
    python -m src.notify.email_sender --test you@example.com
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests  # noqa: E402

from config.settings import settings  # noqa: E402

RESEND_URL = "https://api.resend.com/emails"
TIMEOUT = 20

# Brand colours (light green, black text, never blue) — match the app + site.
GREEN = "#1D9E75"
DEEP = "#0F6E56"
FILL = "#E1F5EE"
INK = "#1F2933"
MUTED = "#667085"


def send_email(to: str, subject: str, html: str, *, text: str | None = None) -> dict:
    """Send one email. Returns {ok, ...}. Never raises — caller stays alive."""
    if not settings.has_resend:
        return {"ok": False, "skipped": True, "reason": "no RESEND_API_KEY in .env"}
    if not to:
        return {"ok": False, "skipped": True, "reason": "no recipient"}

    payload = {
        "from": settings.alert_from_email,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if text:
        payload["text"] = text
    try:
        resp = requests.post(
            RESEND_URL,
            headers={"Authorization": f"Bearer {settings.resend_api_key}",
                     "Content-Type": "application/json"},
            json=payload, timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        return {"ok": False, "error": f"network error: {exc}"}

    if resp.status_code in (200, 201):
        data = {}
        try:
            data = resp.json()
        except ValueError:
            pass
        return {"ok": True, "id": data.get("id")}
    # Resend returns a helpful JSON error body — surface it (no key leakage).
    detail = resp.text[:300]
    return {"ok": False, "status": resp.status_code, "error": detail}


def _deal_rows_html(matches: list[dict]) -> str:
    rows = []
    for m in matches:
        addr = m.get("address") or "New deal"
        score = m.get("score")
        score_txt = f"{score}" if score is not None else "—"
        rows.append(
            f'<tr><td style="padding:10px 14px;border-bottom:1px solid #E4E7EC;'
            f'color:{INK};">{addr}</td>'
            f'<td style="padding:10px 14px;border-bottom:1px solid #E4E7EC;'
            f'text-align:right;"><span style="background:{FILL};color:{DEEP};'
            f'font-weight:700;border-radius:999px;padding:3px 10px;">'
            f'Score {score_txt}</span></td></tr>'
        )
    return "".join(rows)


def build_alert_html(search_name: str, matches: list[dict],
                     app_url: str | None = None) -> str:
    """The HTML body for an alert digest (light-green theme, no blue)."""
    cta = ""
    if app_url:
        cta = (f'<a href="{app_url}" style="display:inline-block;background:{GREEN};'
               f'color:#fff;font-weight:700;text-decoration:none;padding:11px 20px;'
               f'border-radius:10px;margin-top:6px;">See the deals →</a>')
    count = len(matches)
    plural = "deal" if count == 1 else "deals"
    return f"""\
<div style="font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;
     max-width:560px;margin:0 auto;color:{INK};line-height:1.5;">
  <div style="background:linear-gradient(135deg,{DEEP},{GREEN});color:#fff;
       border-radius:16px;padding:22px 22px;">
    <div style="font-size:1.35rem;font-weight:800;">🏡 {count} new {plural} for you</div>
    <div style="color:#EAFBF4;margin-top:4px;">From your alert: <b>{search_name}</b></div>
  </div>
  <table style="width:100%;border-collapse:collapse;margin:16px 0;">
    {_deal_rows_html(matches)}
  </table>
  {cta}
  <p style="color:{MUTED};font-size:.85rem;margin-top:22px;">
    You're getting this because you saved a deal alert. Prices and details can
    change — always verify before making an offer.
  </p>
</div>"""


def send_alert_digest(to: str, search_name: str, matches: list[dict],
                      app_url: str | None = None) -> dict:
    """Build + send one digest email for a single saved search."""
    if not matches:
        return {"ok": False, "skipped": True, "reason": "no matches"}
    count = len(matches)
    subject = (f"🏡 {count} new deal{'s' if count != 1 else ''} — {search_name}")
    html = build_alert_html(search_name, matches, app_url=app_url)
    return send_email(to, subject, html)


def _cli() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Email sender test.")
    parser.add_argument("--test", metavar="EMAIL",
                        help="Send a sample alert email to this address.")
    args = parser.parse_args()

    if not settings.has_resend:
        print("No RESEND_API_KEY found in .env — add it first, then retry.")
        return 1
    if not args.test:
        print("Usage: python -m src.notify.email_sender --test you@example.com")
        return 0

    sample = [
        {"address": "123 Maple St, Sacramento, CA 95820", "score": 82},
        {"address": "456 Oak Ave, Austin, TX 78704", "score": 74},
    ]
    res = send_alert_digest(args.test, "Test alert", sample)
    if res.get("ok"):
        print(f"Sent! Resend id: {res.get('id')}. Check {args.test} (and spam).")
        return 0
    print(f"Failed: {res}")
    return 1


if __name__ == "__main__":
    raise SystemExit(_cli())

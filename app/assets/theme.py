"""
The clean-green visual theme, in one place.

Colors come straight from the brand brief so every screen stays consistent.
The app itself stays clean and readable (white surfaces, green accents) — the
bold full-bleed background art is reserved for the landing/login screens only.
"""

# --- Brand palette: "Warm & trustworthy" -----------------------------------
# Cream base, warm coral + gold accents, near-black text. Defined in ONE place
# so every screen stays consistent. (Full color freedom — the old green-only
# rule is lifted; see .claude/agents/Juliet.md.)
CORAL = "#FF6B5C"           # primary accent / CTAs
CORAL_DEEP = "#E2513F"      # pressed / darker coral
GOLD = "#F2A93B"            # secondary accent / highlights
CREAM = "#FFFDF8"           # page background
WARM_FILL = "#FBEFE8"       # soft warm card / section fill
COCOA = "#2E2A26"           # deep warm dark (hero scrim, footers)
INK = "#1A1A1A"             # main text (near-black)
MUTED = "#7A7066"           # secondary text (warm grey)
SURFACE = "#FFFFFF"
BORDER = "#ECE3DA"          # warm hairline border

# Positive / caution colors — kept meaningful for the deal score & warnings.
GREEN_GOOD = "#1Fae7a"      # a good deal still reads green (universally trusted)
AMBER = "#E08A00"           # middling / mild warning
RED = "#C0392B"             # weak deal / risk warning

# --- Legacy green aliases (other pages still import these) -------------------
# Kept so Browse Deals / Admin keep working until they're migrated to the warm
# palette. New work should use the warm names above.
PRIMARY_GREEN = GREEN_GOOD
LIGHT_FILL = WARM_FILL
DEEP_GREEN = COCOA


def score_color(score: float) -> str:
    """Green = good deal, amber = middling, red = weak. Used by gauges/pins."""
    if score is None:
        return MUTED
    if score >= 70:
        return PRIMARY_GREEN
    if score >= 45:
        return AMBER
    return RED


# CSS injected into the Streamlit app for the clean-green look.
APP_CSS = f"""
<style>
  /* Slim green dashboard header strip */
  .app-header {{
      background: {DEEP_GREEN};
      color: white;
      padding: 0.6rem 1.1rem;
      border-radius: 10px;
      margin-bottom: 1rem;
      font-weight: 600;
      letter-spacing: 0.2px;
  }}
  .badge {{
      display: inline-block;
      padding: 2px 10px;
      border-radius: 999px;
      font-size: 0.8rem;
      font-weight: 600;
  }}
  .badge-good {{ background: {LIGHT_FILL}; color: {DEEP_GREEN}; }}
  .badge-warn {{ background: #FBE9C7; color: {AMBER}; }}
  .badge-bad  {{ background: #F9D6D1; color: {RED}; }}
  .badge-bank {{ background: #EAECF0; color: #344054; }}
  .muted {{ color: {MUTED}; font-size: 0.9rem; }}
  .stApp h1, .stApp h2, .stApp h3 {{ color: {INK}; }}
  div[data-testid="stMetricValue"] {{ color: {DEEP_GREEN}; }}
  /* Trim the big default top whitespace for a tighter, app-like feel */
  .block-container {{ padding-top: 2rem; }}
  footer {{ visibility: hidden; }}
</style>
"""

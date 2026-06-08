"""
The clean-green visual theme, in one place.

Colors come straight from the brand brief so every screen stays consistent.
The app itself stays clean and readable (white surfaces, green accents) — the
bold full-bleed background art is reserved for the landing/login screens only.
"""

# --- Brand colors ----------------------------------------------------------
PRIMARY_GREEN = "#1D9E75"   # main accent
LIGHT_FILL = "#E1F5EE"      # soft green backgrounds
DEEP_GREEN = "#0F6E56"      # headers, scrim
INK = "#1F2933"             # main text
MUTED = "#667085"           # secondary text
SURFACE = "#FFFFFF"
BORDER = "#E4E7EC"

# Caution colors — reserved ONLY for warnings/bad signals.
AMBER = "#E08A00"
RED = "#C0392B"


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
  .muted {{ color: {MUTED}; font-size: 0.9rem; }}
  .stApp h1, .stApp h2, .stApp h3 {{ color: {INK}; }}
  div[data-testid="stMetricValue"] {{ color: {DEEP_GREEN}; }}
  /* Trim the big default top whitespace for a tighter, app-like feel */
  .block-container {{ padding-top: 2rem; }}
  footer {{ visibility: hidden; }}
</style>
"""

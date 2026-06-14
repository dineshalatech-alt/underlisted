"""
The plain-English glossary — ONE source of truth for app + website.

Every home-buying word we show is defined here in kid-simple language. Both the
public website (`tools/gen_site.py` builds `site/learn.html`) and the app
(in-app "What does this mean?" tooltips on the deal screen) read from this list,
so the two teach IDENTICALLY and the wording can never drift apart.

Wording rules: everyday words, a sentence or two per term, a real-dollar example,
no jargon, no pressure. Fair Housing: we explain the *product*, never characterize
people or areas.

To edit a definition, edit it HERE only — then rebuild the site
(`.venv/Scripts/python.exe tools/gen_site.py`) so `learn.html` picks it up.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Term:
    """One glossary entry, shared by the site cards and the app tooltips."""
    key: str                       # stable id / URL anchor, e.g. "deal-score"
    icon: str                      # emoji shown on the website card
    label: str                     # short menu/label name, e.g. "Deal Score"
    title: str                     # full heading, e.g. "Deal Score (0–100)"
    paragraphs: list               # plain-English explanation (1–2 short paras)
    example: Optional[str] = None  # a real-dollar example (HTML allowed for site)
    warn: bool = False             # caution-colored (insurance risk etc.)


# The whole glossary. Order = the order shown on the website's learn page.
TERMS: list = [
    Term(
        "deal-score", "🎯", "Deal Score", "Deal Score (0–100)",
        ["This is one simple number that tells you, at a glance, how good a home "
         "looks as a deal. Higher is better.",
         "We color it so you don't have to think: <b>green = looks like a good "
         "deal</b>, <b>amber = okay, look closer</b>, <b>red = probably not a "
         "great deal</b>."],
        warn=False,
    ),
    Term(
        "underpriced", "🏷️", "Underpriced", "Underpriced / undervalued",
        ["It means the home is being sold for <b>less than what it's probably "
         "worth</b>. That's the kind of home we hunt for.",
         "Think of it like finding a $100 jacket on sale for $70 — same jacket, "
         "smaller price."],
        "<b>Example:</b> a home is listed at $270,000, but homes just like it are "
        "worth about $300,000. It's underpriced by roughly $30,000.",
    ),
    Term(
        "estimated-value", "📏", "Estimated value", "Estimated value",
        ["This is <b>our best guess of what the home is really worth</b>, based on "
         "what similar nearby homes are worth.",
         "It's an estimate, not a promise — but it gives you a fair yardstick to "
         "compare the asking price against."],
        "<b>Example:</b> if our estimated value is $300,000 and the seller is asking "
        "$270,000, the price looks like a bargain.",
    ),
    Term(
        "insurance-risk", "🔥", "Insurance risk",
        "Insurance-risk warning (fire / flood)",
        ["Some areas catch fire or flood more often. Insurance companies know this, "
         "so they <b>charge a lot more</b> to insure a home there — sometimes "
         "hundreds extra every month.",
         "We flag it early so a 'cheap' home doesn't surprise you with a giant "
         "insurance bill later."],
        "<b>Example:</b> two homes cost the same, but one sits in a flood zone. That "
        "one can cost much more to insure every single month.",
        warn=True,
    ),
    Term(
        "true-monthly-cost", "💸", "True monthly cost", "True monthly cost",
        ["Most websites only show the loan payment. But owning a home costs more "
         "than that. We add it <b>all</b> up so you see the real number.",
         "True monthly cost = mortgage <b>+</b> property tax <b>+</b> insurance "
         "<b>+</b> PMI (if any) <b>+</b> HOA (if any) <b>+</b> a little for upkeep."],
        "<b>Example:</b> the loan is $1,500/mo, but with tax, insurance and the rest "
        "it's really about $2,050/mo. That's the number you actually pay.",
    ),
    Term(
        "pmi", "🛡️", "PMI", "PMI (private mortgage insurance)",
        ["PMI is an <b>extra monthly fee you pay when your down payment is under "
         "20%</b>. It protects the lender, not you.",
         "The good news: once you've paid down enough of the loan, PMI usually "
         "goes away."],
        "<b>Example:</b> you put down 10% instead of 20%, so you pay maybe $100–$200 "
        "a month extra in PMI until you build up more ownership.",
    ),
    Term(
        "hoa", "🏘️", "HOA", "HOA (homeowners association) fee",
        ["Some homes — especially condos and homes in planned neighborhoods — "
         "charge a <b>monthly fee for shared upkeep</b>: things like lawns, pools, "
         "hallways, or trash.",
         "Not every home has one. When a home does, we include it in the true "
         "monthly cost."],
        "<b>Example:</b> a condo might charge $250/mo in HOA fees to keep the "
        "building and grounds nice.",
    ),
    Term(
        "property-tax", "🧾", "Property tax", "Property tax",
        ["This is a <b>yearly tax you pay on a home</b> to your local government. "
         "It usually helps pay for schools, roads and services.",
         "We spread it across the year so it shows up in your monthly cost, where "
         "you'll actually feel it."],
        "<b>Example:</b> a $3,600 yearly property tax is about $300 added to each "
        "month.",
    ),
    Term(
        "cash-to-close", "💵", "Cash to close", "Cash to close / down payment",
        ["This is the <b>real cash you need up front</b> to buy the home — before "
         "you move in.",
         "It's mainly your down payment (your share of the price) plus closing "
         "costs (one-time fees for paperwork, the loan and so on)."],
        "<b>Example:</b> on a $300,000 home, a 10% down payment is $30,000, plus a "
        "few thousand in closing costs — so you'd need roughly $35,000 in hand.",
    ),
    Term(
        "afford", "✅", "Can I afford it?", "Can I afford it? (green / amber / red)",
        ["You tell us your income, your savings and your monthly debts. We check "
         "whether a home <b>fits YOUR money</b> — and answer in plain colors.",
         "<b>Green = comfortably yes</b>, <b>amber = tight, be careful</b>, "
         "<b>red = a stretch right now</b>. We also show how much you'd have left "
         "over each month."],
        "<b>Example:</b> 'Green — you'd have about $600 left every month after the "
        "home is paid for.' Your numbers stay private.",
    ),
    Term(
        "days-on-market", "📅", "Days on market", "Days on market",
        ["This is simply <b>how long the home has been for sale</b>.",
         "A home that's sat for a long time can mean the seller is more willing to "
         "<b>negotiate</b> — which can be your chance to ask for a better price."],
        "<b>Example:</b> a home listed 4 days ago may sell fast; one listed 120 days "
        "ago might have room to bargain.",
    ),
    Term(
        "mortgage-rate", "📈", "Mortgage rate", "Mortgage rate",
        ["A mortgage is the loan you use to buy a home. The <b>mortgage rate is the "
         "interest you pay to borrow</b> that money, shown as a percentage.",
         "Even a small change in the rate can move your monthly payment by a lot — "
         "so it's worth watching."],
        "<b>Example:</b> on a $300,000 loan, going from 6% to 7% can add roughly "
        "$200 to your monthly payment.",
    ),
]

# Quick lookup by key.
BY_KEY = {t.key: t for t in TERMS}

# Where people can read the whole thing (relative link inside the static site).
LEARN_URL = "learn.html"
LEARN_URL_PUBLIC = "https://underlistedhomes.com/learn.html"


def get(key: str) -> Term:
    """Fetch one term by key (raises KeyError if the key is unknown)."""
    return BY_KEY[key]


def _strip_html(text: str) -> str:
    """Turn the site's <b>…</b> markup into Streamlit-friendly **…** markdown.

    The glossary stores light HTML (for the website cards). The app renders the
    same words as markdown, so we swap the tags rather than keep two copies.
    """
    if not text:
        return ""
    return (text.replace("<b>", "**").replace("</b>", "**")
                .replace("<i>", "_").replace("</i>", "_"))


def app_tip(key: str, *, include_example: bool = True,
            include_link: bool = True) -> str:
    """A short, app-ready explanation for a 'What does this mean?' tooltip.

    Returns Streamlit markdown: the same kid-simple sentences as the website,
    optionally the real-dollar example, and a gentle link to the full
    'Learn the basics' page. Kept short on purpose — tooltips, not essays.
    """
    t = BY_KEY[key]
    parts = [_strip_html(p) for p in t.paragraphs]
    body = "\n\n".join(parts)
    if include_example and t.example:
        body += "\n\n" + _strip_html(t.example)
    if include_link:
        body += (f"\n\n[Learn the basics →]({LEARN_URL_PUBLIC})")
    return body

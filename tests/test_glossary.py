"""
Tests for the shared plain-English glossary (src/glossary.py).

The glossary is the ONE source of truth for home-buying word definitions, used by
BOTH the public website ("Learn the basics" / learn.html) and the app's in-app
"What does this mean?" tooltips. These tests guard that the two can never drift:
same keys, same wording, HTML correctly converted to markdown for the app.

PURE-logic, NO network, NO API calls.

Run from the project root:
    .venv/Scripts/python.exe -m pytest tests/test_glossary.py -q
or without pytest:
    .venv/Scripts/python.exe tests/test_glossary.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import glossary  # noqa: E402

# The terms the deal screen places a "What does this mean?" helper next to.
# If any of these disappears from the glossary, the in-app tooltips break.
TERMS_USED_IN_APP = [
    "deal-score", "insurance-risk", "afford", "pmi", "hoa",
    "cash-to-close", "true-monthly-cost", "estimated-value",
]


def test_all_app_keys_exist():
    """Every term the deal screen tooltips reference must be defined."""
    for key in TERMS_USED_IN_APP:
        assert key in glossary.BY_KEY, f"missing glossary term: {key}"
        glossary.get(key)  # must not raise


def test_no_duplicate_keys():
    keys = [t.key for t in glossary.TERMS]
    assert len(keys) == len(set(keys)), "duplicate glossary keys"


def test_every_term_has_words():
    """A term with no explanation would teach nobody."""
    for t in glossary.TERMS:
        assert t.label and t.title, f"{t.key} missing label/title"
        assert t.paragraphs and all(p.strip() for p in t.paragraphs), \
            f"{t.key} has empty explanation"


def test_app_tip_converts_html_to_markdown():
    """The site stores <b>…</b>; the app must show **…** (no raw HTML tags)."""
    tip = glossary.app_tip("pmi")
    assert "<b>" not in tip and "</b>" not in tip
    assert "**" in tip  # the bold survived as markdown


def test_app_tip_matches_site_wording():
    """The in-app tip must use the SAME sentences as the learn page (just with
    markdown bold instead of HTML bold). This is the anti-drift guarantee."""
    t = glossary.get("hoa")
    tip = glossary.app_tip("hoa", include_example=False, include_link=False)
    for para in t.paragraphs:
        expected = para.replace("<b>", "**").replace("</b>", "**")
        assert expected in tip, f"app tip dropped wording for {t.key}"


def test_app_tip_example_toggle():
    with_eg = glossary.app_tip("cash-to-close", include_example=True,
                               include_link=False)
    without_eg = glossary.app_tip("cash-to-close", include_example=False,
                                  include_link=False)
    assert "Example" in with_eg
    assert "Example" not in without_eg


def test_app_tip_link_toggle():
    with_link = glossary.app_tip("deal-score", include_link=True)
    without_link = glossary.app_tip("deal-score", include_link=False)
    assert glossary.LEARN_URL_PUBLIC in with_link
    assert glossary.LEARN_URL_PUBLIC not in without_link


def test_insurance_term_is_a_warning():
    """The fire/flood insurance term is the cautionary one (drives warn styling)."""
    assert glossary.get("insurance-risk").warn is True
    assert glossary.get("deal-score").warn is False


def test_site_generator_uses_shared_glossary():
    """gen_site.py must build the learn page from the SAME glossary list, so the
    website and app never define the words twice."""
    from tools import gen_site
    body = gen_site.learn_page_body()
    # Each glossary term's anchor + title should appear in the rendered page.
    for t in glossary.TERMS:
        assert f"id='{t.key}'" in body, f"learn page missing card {t.key}"
        assert t.title in body, f"learn page missing title for {t.key}"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed} passed")

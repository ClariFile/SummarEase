"""The two themes: every pair of colours the interface puts together is readable (WCAG contrast ratios). Text at
least 4.5:1; control borders and the focus outline at least 3:1. Dividers are decorative and not held to 3:1.
And the look (record C11, DOS_AND_DONTS.md): violet only on the primary button, focus, the current tab's bar,
selection and links, as teal in ClassiFile."""
import re

import pytest

from summarease.tokens import THEMES, VIOLET

TEXT = 4.5
GRAPHIC = 3.0


def luminance(colour):
    colour = colour.lstrip("#")
    channel = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(int(colour[i:i + 2], 16) / 255) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def pairs(t):
    out = []
    for surface in ("window", "base", "raised", "notice", "selection", "hover", "pressed"):
        out += [(f"text on {surface}", t["text"], t[surface], TEXT)]
    for surface in ("window", "base", "notice", "hover"):
        out += [(f"secondary text on {surface}", t["secondary"], t[surface], TEXT),
                (f"amber text on {surface}", t["amber"], t[surface], TEXT),
                (f"red text on {surface}", t["red"], t[surface], TEXT)]
        if surface != "notice":     # the notice is only behind OCR text, which holds no link
            out += [(f"links on {surface}", t["link"], t[surface], TEXT)]
    out += [("primary button text", t["on_primary"], t["primary"], TEXT),
            ("primary button text, hovered", t["on_primary"], t["primary_hover"], TEXT)]
    for surface in ("window", "base"):
        out += [(f"control border on {surface}", t["control"], t[surface], GRAPHIC),
                (f"focus outline on {surface}", t["accent"], t[surface], GRAPHIC)]
    return out


@pytest.mark.parametrize("name", sorted(THEMES))
def test_every_text_and_background_pair_is_readable(name):
    failing = [f"{what}: {contrast(fg, bg):.2f} < {least}" for what, fg, bg, least in pairs(THEMES[name])
               if contrast(fg, bg) < least]
    assert not failing, f"{name}: " + "; ".join(failing)


def chroma(colour):
    rgb = [int(colour.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    return max(rgb) - min(rgb)


def test_the_themes_are_complete_violet_is_the_accent_and_large_surfaces_are_grey():
    from summarease.app import style_sheet

    assert set(THEMES["light"]) == set(THEMES["dark"])
    for name, t in THEMES.items():
        assert t["primary"] == VIOLET == "#6C47FF"
        for role in ("window", "base", "raised", "notice", "hover", "pressed", "divider", "control"):
            assert chroma(t[role]) <= 12, f"{name}: {role} is not a neutral grey"
        sheet = style_sheet(t)
        assert "palette(" not in sheet and "rgba(" not in sheet, name   # nothing from the system palette
        for block in sheet.split("}"):
            selector, _, body = block.partition("{")
            if t["accent"] in body or t["primary"] in body:
                assert re.search(r"focus|#primary|tab:selected", selector), selector.strip()   # the selection bar
            if ":hover" in selector and "#primary" not in selector:
                assert t["accent"] not in body and t["selection"] not in body, selector.strip()


# The suite's shared values, copied from ClassiFile's classifile/app/tokens.py at 1.0.0-rc.7 (commit 454e720; it
# has no tag yet: retake this table at ClassiFile's v1 tag). The two apps share greys, amber, red, font, text sizes,
# spacing and radii; each keeps its own accent (DOS_AND_DONTS.md; docs/FROM_CLASSIFILE.md, section 2).
SUITE_COLOURS = {
    "light": {"window": "#F6F7F9", "base": "#FFFFFF", "raised": "#FFFFFF", "text": "#111827", "secondary": "#4B5563",
              "disabled": "#6B7280", "divider": "#D9DEE5", "control": "#82868C", "hover": "#EAEEF2",
              "pressed": "#E2E6EB", "notice": "#E8EDF2", "disabled_fill": "#E5E7EB", "amber": "#AA4F09",
              "red": "#B91C1C", "on_primary": "#FFFFFF"},
    "dark": {"window": "#1C1E21", "base": "#212428", "raised": "#272A2F", "text": "#E6E8EB", "secondary": "#A0A6AD",
             "disabled": "#7A8087", "divider": "#33373D", "control": "#777A7F", "hover": "#2A2E33",
             "pressed": "#33373D", "notice": "#272A2F", "disabled_fill": "#2E3238", "amber": "#D29922",
             "red": "#EA756F", "on_primary": "#FFFFFF"},
}
SUITE_SIZES = {"FONT": "Segoe UI", "TEXT_CAPTION": 12, "TEXT_SECONDARY": 13, "TEXT_BODY": 14, "TEXT_HEADING": 16,
               "TEXT_TITLE": 22, "WEIGHT_STRONG": 600, "SPACED": 1, "PAD": 24, "GROUP": 16, "RELATED": 8, "TIGHT": 4,
               "HAIR": 1, "RADIUS_CONTROL": 6, "RADIUS_PANEL": 8, "CONTROL_TEXT": 20}


def test_the_shared_suite_values_equal_classifiles():
    from summarease import tokens

    for name, shared in SUITE_COLOURS.items():
        assert {k: THEMES[name][k] for k in shared} == shared, name
    assert {k: getattr(tokens, k) for k in SUITE_SIZES} == SUITE_SIZES
    assert all(not {"green"} & set(t) for t in THEMES.values())          # the suite's colours, nothing more

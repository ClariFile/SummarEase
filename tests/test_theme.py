"""The two themes: every pair of colours the interface puts together is readable (WCAG contrast ratios). Text at
least 4.5:1; control borders and the focus outline at least 3:1. Dividers are decorative and not held to 3:1.
And the look (record C11, DOS_AND_DONTS.md): violet only on the primary button, focus, selection and links."""
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
                (f"red text on {surface}", t["red"], t[surface], TEXT),
                (f"links on {surface}", t["link"], t[surface], TEXT)]
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
                assert "focus" in selector or "#primary" in selector, selector.strip()
            if ":hover" in selector and "#primary" not in selector:
                assert t["accent"] not in body and t["selection"] not in body, selector.strip()

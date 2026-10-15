"""Design tokens: every colour and size of the interface is named here, once. The structure follows ClassiFile's
tokens (one dictionary per theme, the same role names), with violet (#6C47FF) where ClassiFile has teal
(record C11). tests/test_theme.py checks the contrast of every pair the interface puts together.
Violet appears only on the primary button, the focus outline, the selection and links; everything else is grey."""

THEMES = {
    "light": {
        "window": "#F6F7F9",        # the page behind everything
        "base": "#FFFFFF",          # the text view
        "raised": "#FFFFFF",
        "text": "#111827",
        "secondary": "#4B5563",     # captions, page and slide labels, the status line
        "disabled": "#6B7280",
        "divider": "#D9DEE5",       # decorative lines
        "control": "#82868C",       # the outline of buttons
        "accent": "#6C47FF",        # violet: the focus outline
        "link": "#6C47FF",
        "primary": "#6C47FF",       # the primary button, the one filled violet
        "primary_hover": "#5A36E0",
        "on_primary": "#FFFFFF",
        "selection": "#E9E4FF",     # selected text: a faint violet tint
        "hover": "#EAEEF2",         # a grey change, never violet
        "pressed": "#E2E6EB",
        "notice": "#EEF1F4",        # behind OCR text
        "disabled_fill": "#E5E7EB",
        "amber": "#AA4F09",         # what couldn't be read
        "red": "#B91C1C",           # errors
        "green": "#14793A",
    },
    "dark": {                       # neutral charcoal: no tint in the backgrounds
        "window": "#1C1E21",
        "base": "#212428",
        "raised": "#272A2F",
        "text": "#E6E8EB",
        "secondary": "#A0A6AD",
        "disabled": "#7A8087",
        "divider": "#33373D",
        "control": "#777A7F",
        "accent": "#9D85FF",        # #6C47FF is only 3.2:1 on the dark page; a lighter tint for lines and links
        "link": "#9D85FF",
        "primary": "#6C47FF",
        "primary_hover": "#5A36E0",
        "on_primary": "#FFFFFF",
        "selection": "#38324F",
        "hover": "#2A2E33",
        "pressed": "#33373D",
        "notice": "#2A2D32",
        "disabled_fill": "#2E3238",
        "amber": "#D29922",
        "red": "#EA756F",
        "green": "#57AB5A",
    },
}
VIOLET = "#6C47FF"

# -- text (logical pixels) ------------------------------------------------------------------------------------
FONT = "Segoe UI"
TEXT_CAPTION = 12
TEXT_SECONDARY = 13
TEXT_BODY = 14
TEXT_READING = 15       # the readable text itself
TEXT_HEADING = 18
TEXT_TITLE = 22
WEIGHT_STRONG = 600

# -- spacing and sizes ----------------------------------------------------------------------------------------
PAD = 24
GROUP = 16
RELATED = 8
TIGHT = 4
HAIR = 1
RADIUS_CONTROL = 6
RADIUS_PANEL = 8
CONTROL_TEXT = 20
SPACED = 1              # letter spacing of the pane captions
READING_CHARS = 80      # a text line stops growing at about this many characters; the pane itself fills the window
SUMMARY_SHARE = 0.55    # the Summary pane's share of the workspace at first
NARROW = 960            # below this window width, Source and Summary become tabs
WINDOW = (1280, 760)
MIN_WINDOW = (560, 480)

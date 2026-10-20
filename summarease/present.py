"""How a summary is shown, copied and exported. One list of paragraphs feeds all three, so Copy, the PDF and the
Word file say the same thing as the screen: each line word for word, then where it comes from, OCR and speaker notes
marked, and what couldn't be read."""
from html import escape

from . import tokens as tk
from .readable import DETAILS, LIST_MARK
from .summarize import LEVEL_NAMES

NOTE = "Every line is taken word for word from the document; the reference after it says where."
LINK_CHARS = 32     # a section name used as a reference is shortened beyond this
EMPTY = {
    "no_text": "No text was read from this document, so there is nothing to summarize.",
    "unusable": "The readable text has no sentence, bullet or line a summary can use. It is all in the Source.",
    "none_fit": "No whole line fits this level's length, and lines are never cut short. A higher level may show more.",
}
WHOLE = "This document is short, so this level shows every line it can use."
TABLES = "Tables are not summarized; they are in the Source."
SOURCE_TITLE = "Readable text"
SOURCE_NOTE = "The document's words as SummarEase read them, laid out for reading. Nothing is reworded."


def where(summary, line):
    """The reference shown after a line: its page or slide, or its section."""
    if summary.unit == "page":
        return f"p. {line.unit}"
    if summary.unit == "slide":
        return f"slide {line.unit}"
    label = summary.labels[line.section]
    return label if len(label) <= LINK_CHARS else label[:LINK_CHARS - 1].rstrip() + "…"


def mark(summary, line):
    """SummarEase's own mark for a line that is not the document's main text, or ""."""
    if line.kind == "ocr":
        return "OCR"
    if line.kind == "note":
        return "Speaker notes"
    if line.unit in summary.hidden:
        return "Hidden slide"
    return ""


def notes(summary):
    """SummarEase's notes about this summary, in order: why it is empty, what it leaves out, a short document."""
    out = [EMPTY[summary.empty]] if summary.empty else []
    if summary.omitted:
        n = len(summary.omitted)
        out.append(f"{n} section{'s' * (n > 1)} didn't fit this level's length: "
                   + "; ".join(omitted_name(summary, i, u) for i, u in summary.omitted) + ".")
    if summary.whole:
        out.append(WHOLE)
    if summary.tables:
        out.append(TABLES)
    return out


def omitted_name(summary, section, unit):
    label = summary.labels[section]
    return label if summary.unit not in ("page", "slide") else f"{label} ({'p.' if summary.unit == 'page' else 'slide'} {unit})"


def paragraphs(summary):
    """[(style, text)] in reading order. Styles: title, note, gap, section, item. The document's words are in the
    section and item texts; everything else is SummarEase's."""
    out = [("title", f"{LEVEL_NAMES[summary.level]} summary"), ("note", NOTE)]
    if summary.gaps:
        out.append(("gap", gap_line(summary)))
        out += [("gap", detail) for _, detail in summary.gaps]
    out += [("note", n) for n in notes(summary)]
    for section, lines in summary.sections:
        head = section.heading if section.heading in lines else None
        if summary.level in ("detailed", "comprehensive"):
            out.append(("section", f"{head.text} ({where(summary, head)})" if head
                        else f"{summary.labels[lines[0].section]}"))
        for l in lines:
            if l is head:
                continue
            m = mark(summary, l)
            out.append(("item", f"{bullet(l)}{'[' + m + '] ' if m else ''}{l.text} ({where(summary, l)})"))
    return out


def bullet(line):
    """SummarEase's bullet, unless the line already starts with the document's own list mark."""
    return "" if LIST_MARK.match(line.text) else "• "


def gap_line(summary):
    n = len(summary.gaps)
    unit = summary.unit if summary.unit in ("page", "slide") else "place"
    return f"Some pictures couldn't be read: {n} {unit}{'s' * (n > 1)}."


def as_text(summary_or_paras):
    """For Copy: plain text, one paragraph per line, of a summary or of [(style, text)]."""
    paras = summary_or_paras if isinstance(summary_or_paras, list) else paragraphs(summary_or_paras)
    return "\n".join(t for _, t in paras) + "\n"


def source_paragraphs(blocks):
    """The readable text (record C5, C14) as [(style, text)] for Copy and Export: every word of the view, in its
    order, with SummarEase's own labels and marks. A table row's cells are joined by " | " (layout only)."""
    out = [("title", SOURCE_TITLE), ("note", SOURCE_NOTE)]
    for b in blocks:
        if b.kind == "gaps":
            out += [("gap", b.text)] + [("gap", d) for _, d in b.rows]
        elif b.kind in ("label", "note", "gap"):
            out.append((b.kind, b.text))
        elif b.kind in ("title", "heading"):
            out.append(("section", b.text))
        elif b.kind == "list":
            out += [("item", f"{'' if LIST_MARK.match(i) else '• '}{i}") for i in b.rows]
        elif b.kind == "table":
            out += [("body", " | ".join(r)) for r in b.rows]
        else:   # paragraph, lines, ocr, notes: a line break in the reader's text starts a new paragraph
            out += [("body", line) for line in b.text.split("\n") if line.strip()]
    return out


def to_html(summary, t, details=False):
    """The summary pane: each line with a link to where it comes from ("#l<line id>": that line in the Source pane)."""
    link = lambda l: (f' <a href="#l{l.id}" style="color:{t["link"]}; font-size:{tk.TEXT_CAPTION}px; '
                      f'text-decoration:none;">{escape(where(summary, l)).replace(" ", "&nbsp;")}</a>')   # never split "p. 3"
    tag = lambda l: (f'<span style="color:{t["secondary"]}; font-size:{tk.TEXT_CAPTION}px;">{escape(mark(summary, l))}'
                     f'</span> ' if mark(summary, l) else "")
    out = [f'<body style="font-family:\'{tk.FONT}\'; font-size:{tk.TEXT_READING}px; color:{t["text"]};">']
    if summary.gaps:
        toggle = "Hide details" if details else "Show details"
        out.append(f'<p style="margin-top:0; margin-bottom:{tk.RELATED}px; color:{t["amber"]}; '
                   f'font-size:{tk.TEXT_SECONDARY}px;">{escape(gap_line(summary))} '
                   f'<a href="{DETAILS}" style="color:{t["link"]};">{toggle}</a></p>')
        if details:
            out.append(f'<ul style="margin-top:0; margin-bottom:{tk.GROUP}px; color:{t["secondary"]}; '
                       f'font-size:{tk.TEXT_SECONDARY}px;">' + "".join(
                           f'<li><a href="#u{u}" style="color:{t["link"]};">{escape(d)}</a></li>' for u, d in summary.gaps)
                       + "</ul>")
    note = f'<p style="margin-top:0; margin-bottom:{tk.RELATED}px; color:{t["secondary"]}; font-size:{tk.TEXT_SECONDARY}px;">'
    for n in notes(summary):
        if summary.omitted and n.startswith(f"{len(summary.omitted)} section"):
            n = escape(n.split(": ", 1)[0]) + ": " + "; ".join(
                f'<a href="#u{u}" style="color:{t["link"]};">{escape(omitted_name(summary, i, u))}</a>'
                for i, u in summary.omitted) + "."
        else:
            n = escape(n)
        out.append(note + n + "</p>")
    sectioned = summary.level in ("detailed", "comprehensive")
    for section, lines in summary.sections:
        head = section.heading if section.heading in lines else None
        if sectioned:
            first = head or lines[0]
            text = escape(head.text) if head else (f'<span style="color:{t["secondary"]};">'
                                                    f'{escape(summary.labels[first.section])}</span>')
            out.append(f'<p style="margin-top:{tk.GROUP}px; margin-bottom:{tk.TIGHT}px; '
                       f'font-weight:{tk.WEIGHT_STRONG};">{tag(first) if head else ""}{text}{link(first)}</p>')
        items = [l for l in lines if l is not head]
        if items:
            out += [f'<p style="margin-top:0; margin-bottom:{tk.TIGHT + 2}px; margin-left:{tk.PAD + tk.GROUP}px; '
                    f'text-indent:-{tk.GROUP}px;">{escape(bullet(l)).replace(" ", "&nbsp;")}{tag(l)}'
                    + (f"<i>{escape(l.text)}</i>" if l.kind == "ocr" else escape(l.text)) + f"{link(l)}</p>"
                    for l in items]
    return "".join(out) + "</body>"

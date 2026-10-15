"""How a summary is shown, copied and exported. One list of paragraphs feeds all three, so Copy, the PDF and the
Word file say the same thing as the screen: each line word for word, then where it comes from, OCR and speaker notes
marked, and what couldn't be read."""
from html import escape

from . import tokens as tk
from .readable import DETAILS, LIST_MARK
from .summarize import LEVEL_NAMES

NOTE = "Every line is taken word for word from the document; the reference after it says where."
LINK_CHARS = 32     # a section name used as a reference is shortened beyond this


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


def paragraphs(summary):
    """[(style, text)] in reading order. Styles: title, note, gap, section, item. The document's words are in the
    section and item texts; everything else is SummarEase's."""
    out = [("title", f"{LEVEL_NAMES[summary.level]} summary"), ("note", NOTE)]
    if summary.gaps:
        out.append(("gap", gap_line(summary)))
        out += [("gap", detail) for _, detail in summary.gaps]
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


def as_text(summary):
    """For Copy: plain text, one paragraph per line."""
    return "\n".join(t for _, t in paragraphs(summary)) + "\n"


def to_html(summary, t, details=False):
    """The summary pane: each line with a link to where it comes from ("#u<unit>" in the Source pane)."""
    link = lambda l: (f' <a href="#u{l.unit}" style="color:{t["link"]}; font-size:{tk.TEXT_CAPTION}px; '
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

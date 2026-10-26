"""The readable text view (record C5): the reader's words, laid out as headings, paragraphs, lists and tables.

Layout only. Every word the reader gave (a unit's text, then its OCR text, then its speaker notes) is shown once, in
order, and nothing is added to the document's blocks. SummarEase's own words (page and slide labels, captions, what
couldn't be read) are separate blocks of the OWN_KINDS, so they never mix with the document's.
"""
import re
from collections import Counter
from dataclasses import dataclass, field
from html import escape

from . import tokens as tk
from .reader.common import UNREAD_OUTCOMES

DOC_KINDS = ("title", "heading", "paragraph", "lines", "list", "table", "ocr", "notes")
OWN_KINDS = ("label", "note", "gap", "gaps")

# PDF headings: a short run of lines (HEADING_MAX_WORDS or fewer) at the start of a block, clearly larger than the
# page's body text, or bold where the body text is not. A paragraph is never promoted to a heading.
HEADING_RATIO = 1.2
TITLE_RATIO = 1.6        # this much larger: a level-1 heading
HEADING_MAX_WORDS = 12
BODY_MIN_CHARS = 200     # a page with less sized text than this takes the document's body size
LIST_MARK = re.compile(r"^\s*(?:[•◦▪▫‣∙·○●■□➢➤►▶✓✔–—*-]\s|\(?\d{1,3}[.)]\s|\(?[a-z][.)]\s)")

OCR_CAPTION = "Text read by OCR from a picture. It may contain errors."
UNIT_NAMES = {"page": "Page", "slide": "Slide"}
GAP_NOTE = "A picture here couldn't be read."
# Why, by the unit's OCR status (reader/ocr.py), for the details behind the top line. "done" is not a gap.
GAP_REASONS = {
    "no_text": "OCR found no text in it",
    "no_readable_image": "it could not be opened",
    "failed": "OCR failed on it",
    "unavailable": "OCR is not installed",
    "deferred": "OCR ran out of time",
    "disabled": "OCR is switched off",
    "partial": "OCR read only some of the pictures",
}
# Why one picture of a unit was left unread (record 7, UnitRecord.ocr_pictures), when others were read.
PICTURE_REASONS = {"render_failed": "it could not be opened", "engine_failed": "OCR failed on it",
                   "not_attempted": "OCR ran out of time"}


def gap_detail(u):
    """What the gap details say about a unit not fully read, or None. A unit that read one picture and not another
    (record 7) says how many were left unread and why; the text read from the others stays in the view."""
    if not u.suspected_unread:
        return None
    pictures = getattr(u, "ocr_pictures", None) or []
    unread = [p["outcome"] for p in pictures if p.get("outcome") in UNREAD_OUTCOMES]
    if unread and len(unread) < len(pictures):
        why = ", ".join(sorted({PICTURE_REASONS[o] for o in unread}))
        return f"{len(unread)} of its {len(pictures)} pictures couldn't be read ({why})"
    if unread or u.ocr_status in GAP_REASONS:
        reason = GAP_REASONS.get(u.ocr_status) or PICTURE_REASONS[unread[0]]
        return f"a picture couldn't be read ({reason})"
    return None
DETAILS = "#gap-details"


@dataclass
class Block:
    kind: str                                  # DOC_KINDS hold the document's words; OWN_KINDS hold SummarEase's
    text: str = ""
    level: int = 2                             # headings
    rows: list = field(default_factory=list)   # tables: [[cell, ...]]; lists: [item]; gaps: [(unit, detail)]
    unit: int | None = None                    # the page, slide, block or pasted paragraph it comes from

    def words(self):
        if self.kind == "gaps":
            return words(self.text)
        return words("\n".join(["\n".join(r) if isinstance(r, list) else r for r in self.rows] + [self.text]))


def words(text):
    return text.split()


def doc_words(blocks):
    return [w for b in blocks if b.kind in DOC_KINDS for w in b.words()]


def gapped_units(blocks):
    """The units with a gap note, in order."""
    return [b.unit for b in blocks if b.kind == "gap"]


# -- from the reader's record ---------------------------------------------------------------------------------
def from_record(record, bold=None):
    """Blocks for a DocumentRecord, in reading order, with gaps noted where they are and summed up at the top.
    bold: for PDFs, {page: [[line is bold, ...] per layout block]} (worker.pdf_bold), or None."""
    out, details = [], []
    body = _body_size(record.units) if record.format == "pdf" else None
    for u in record.units:
        name = UNIT_NAMES.get(record.unit)
        mine = []
        if name:
            mine.append(Block("label", f"{name} {u.index}" + (" (hidden in the presentation)" if u.kind == "hidden slide" else "")))
        mine += _native(record, u, body, (bold or {}).get(u.index))
        if u.ocr_text:
            mine += [Block("note", OCR_CAPTION), Block("ocr", u.ocr_text)]
        detail = gap_detail(u)
        if detail:
            mine.append(Block("gap", GAP_NOTE))     # one short note per unit at most
            where = f"{name} {u.index}" if name else f"Place {len(details) + 1}"
            details.append((u.index, f"{where}: {detail}."))
        if u.notes:
            mine += [Block("note", "Speaker notes"), Block("notes", u.notes)]
        for b in mine:
            b.unit = u.index
        out += mine
    if details:
        n = len(details)
        where = f"{n} {record.unit}{'s' * (n > 1)}" if record.unit in UNIT_NAMES else f"{n} place{'s' * (n > 1)}"
        out.insert(0, Block("gaps", f"Some pictures couldn't be read: {where}.", rows=details))
    return out


def _native(record, u, body, bold):
    if record.format == "pdf":
        return _guarded(u, _pdf_blocks(u, body, bold))
    if record.format == "pptx":
        return _guarded(u, _slide_blocks(u))
    return _flow_block(u)


def _guarded(u, blocks):
    """The layout is the reader's too, but if its words ever differ from the unit's text, show the text itself."""
    return blocks if doc_words(blocks) == words(u.text) else _plain(u.text)


def _plain(text):
    return [Block("lines", p) for p in re.split(r"\n\s*\n", text) if p.strip()]


def _size_counts(units):
    sizes = Counter()
    for u in units:
        for b in (u.layout or {}).get("blocks", []):
            for line in b["lines"]:
                if line["size"]:
                    sizes[line["size"]] += len(line["text"].strip())
    return sizes


def _body_size(units):
    """The commonest line size, weighted by characters: the size of the body text."""
    sizes = _size_counts(units)
    return sizes.most_common(1)[0][0] if sizes else None


def _pdf_blocks(u, doc_body, bold):
    sizes = _size_counts([u])
    body = sizes.most_common(1)[0][0] if sum(sizes.values()) >= BODY_MIN_CHARS else doc_body
    layout = (u.layout or {}).get("blocks", [])
    flags = bold if bold and len(bold) == len(layout) else [[False] * len(b["lines"]) for b in layout]
    body_bold = _bold_share(layout, flags) >= 0.5
    out = []
    for b, bf in zip(layout, flags):
        lines = [(l["text"].strip(), l["size"] or 0, f) for l, f in zip(b["lines"], bf + [False] * len(b["lines"]))
                 if l["text"].strip()]
        run = 0     # leading lines that look like a heading
        while run < len(lines) and body and _headingish(lines[run], body, body_bold):
            run += 1
        head = " ".join(t for t, _, _ in lines[:run])
        if run and len(head.split()) <= HEADING_MAX_WORDS and not _sentence(head):
            biggest = max(s for _, s, _ in lines[:run])
            level = 1 if biggest >= body * TITLE_RATIO else 2 if biggest >= body * HEADING_RATIO else 3
            out.append(Block("heading", head, level=level))
            lines = lines[run:]
        out += _flow([t for t, _, _ in lines])
    return out


def _headingish(line, body, body_bold):
    text, size, is_bold = line
    if not re.search(r"[A-Za-z]", text):
        return False
    return size >= body * HEADING_RATIO or (is_bold and not body_bold and size >= body * 0.95)


def _sentence(text):
    """A short line ending like a sentence is body text, not a heading."""
    return text.endswith((".", "!", "?", ":", ";", ",")) and len(text.split()) >= 4


def _bold_share(layout, flags):
    total = boldc = 0
    for b, bf in zip(layout, flags):
        for l, f in zip(b["lines"], bf):
            n = len(l["text"].strip())
            total += n
            boldc += n if f else 0
    return boldc / total if total else 0


def _flow(texts):
    """Lines flow into one paragraph; a line that starts with a list mark starts a new one."""
    out, para = [], []
    for t in texts:
        if para and LIST_MARK.match(t):
            out.append(Block("paragraph", " ".join(para)))
            para = []
        para.append(t)
    if para:
        out.append(Block("paragraph", " ".join(para)))
    return out


def _same(a, b):
    return " ".join(a.split()) == " ".join((b or "").split())


def _slide_blocks(u):
    out = []
    for b in (u.layout or {}).get("blocks", []):
        text = "\n".join(l["text"] for l in b["lines"])
        if text.strip():
            out.append(Block("heading", text.strip(), level=2) if _same(text, u.title) else Block("lines", text.strip()))
    return out


def _flow_block(u):
    """DOCX and ODT: the reader already says what each block is."""
    if not u.text.strip():
        return []
    if u.kind == "title":
        return [Block("title", u.text.strip(), level=1)]
    if u.kind == "heading":
        return [Block("heading", u.text.strip(), level=min(max(u.level or 1, 1), 4))]
    if u.kind == "table":
        return [Block("table", rows=[r.split("\t") for r in u.text.split("\n") if r.strip()])]
    if u.kind == "list":
        return [Block("list", rows=[l for l in u.text.split("\n") if l.strip()])]
    if u.kind in ("footnotes", "endnotes"):
        return [Block("note", u.kind.capitalize()), Block("lines", u.text.strip())]
    return [Block("lines", u.text.strip())]


# -- pasted text ----------------------------------------------------------------------------------------------
def from_text(text):
    """Pasted text: paragraphs split at blank lines, line breaks kept. Held in memory only (record C9)."""
    blocks = _plain(text)
    for i, b in enumerate(blocks, 1):
        b.unit = i
    return blocks


# -- HTML for the view ----------------------------------------------------------------------------------------
def to_html(blocks, t, details=False):
    """The blocks as HTML for a QTextDocument, in the colours of theme t (a tokens.THEMES entry). Each unit starts
    with an anchor "u<unit>" that the summary's links scroll to. details: show the gap details."""
    para = f"margin-top:0; margin-bottom:{tk.RELATED + tk.TIGHT}px;"
    out = [f'<body style="font-family:\'{tk.FONT}\'; font-size:{tk.TEXT_READING}px; color:{t["text"]};">']
    unit = None
    for b in blocks:
        if b.unit is not None and b.unit != unit:
            unit = b.unit
            out.append(f'<a name="u{unit}"></a>')
        e = escape(b.text).replace("\n", "<br>")
        if b.kind == "label":
            out.append(f'<p style="margin-top:{tk.PAD}px; margin-bottom:{tk.RELATED}px; color:{t["secondary"]}; '
                       f'font-size:{tk.TEXT_CAPTION}px; font-weight:{tk.WEIGHT_STRONG};">{e}</p>')
        elif b.kind == "note":
            out.append(f'<p style="margin-top:{tk.RELATED}px; margin-bottom:{tk.TIGHT}px; color:{t["secondary"]}; '
                       f'font-size:{tk.TEXT_SECONDARY}px;">{e}</p>')
        elif b.kind == "gap":
            out.append(f'<p style="{para} color:{t["amber"]}; font-size:{tk.TEXT_SECONDARY}px;">{e}</p>')
        elif b.kind == "gaps":
            out.append(gaps_html(b, t, details))
        elif b.kind in ("title", "heading"):
            size = tk.DOC_TITLE if b.level == 1 else tk.DOC_HEADING if b.level == 2 else tk.TEXT_READING + 1
            out.append(f'<p style="margin-top:{tk.GROUP}px; margin-bottom:{tk.RELATED}px; font-size:{size}px; '
                       f'font-weight:{tk.WEIGHT_STRONG};">{e}</p>')
        elif b.kind == "ocr":
            out.append(f'<table width="100%" cellpadding="{tk.RELATED}" style="margin-bottom:{tk.RELATED}px; '
                       f'background-color:{t["notice"]};"><tr><td><i>{e}</i></td></tr></table>')
        elif b.kind == "notes":
            out.append(f'<p style="{para} color:{t["secondary"]};">{e}</p>')
        elif b.kind == "table":
            rows = "".join("<tr>" + "".join(f"<td>{escape(c)}</td>" for c in r) + "</tr>" for r in b.rows)
            out.append(f'<table border="1" cellspacing="0" cellpadding="{tk.TIGHT + 2}" '
                       f'style="margin-bottom:{tk.RELATED}px; border-color:{t["divider"]};">{rows}</table>')
        elif b.kind == "list":
            out.append(f'<ul style="{para}">' + "".join(f"<li>{escape(i)}</li>" for i in b.rows) + "</ul>")
        else:   # paragraph, lines
            out.append(f'<p style="{para}">{e}</p>')
    return "".join(out) + "</body>"


def gaps_html(b, t, details):
    """The single line about what couldn't be read, with its details behind a disclosure link."""
    toggle = "Hide details" if details else "Show details"
    html = (f'<p style="margin-top:0; margin-bottom:{tk.RELATED}px; color:{t["amber"]}; font-size:{tk.TEXT_SECONDARY}px;">'
            f'{escape(b.text)} <a href="{DETAILS}" style="color:{t["link"]};">{toggle}</a></p>')
    if details:
        html += (f'<ul style="margin-top:0; margin-bottom:{tk.GROUP}px; color:{t["secondary"]}; '
                 f'font-size:{tk.TEXT_SECONDARY}px;">'
                 + "".join(f'<li><a href="#u{u}" style="color:{t["link"]};">{escape(d)}</a></li>' for u, d in b.rows)
                 + "</ul>")
    return html

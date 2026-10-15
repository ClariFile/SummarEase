"""The readable text view (record C5): the reader's words, laid out as headings, paragraphs, lists and tables.

Layout only. Every word the reader gave (a unit's text, then its OCR text, then its speaker notes) is shown once, in
order, and nothing is added to the document's blocks. SummarEase's own words (page and slide labels, captions, what
couldn't be read) are separate blocks of kind "label", "note" or "gap", so they never mix with the document's.
"""
import re
from collections import Counter
from dataclasses import dataclass, field
from html import escape

from . import tokens as tk

DOC_KINDS = ("title", "heading", "paragraph", "lines", "list", "table", "ocr", "notes")
OWN_KINDS = ("label", "note", "gap")

HEADING_RATIO = 1.15     # PDF: a short block whose lines are all this much larger than the body text is a heading
TITLE_RATIO = 1.6        # ... and this much larger, a level-1 heading
HEADING_MAX_LINES = 3
HEADING_MAX_CHARS = 200
LIST_MARK = re.compile(r"^\s*(?:[•◦▪▫‣∙·○●■□➢➤►▶✓✔–—*-]\s|\(?\d{1,3}[.)]\s|\(?[a-z][.)]\s)")

OCR_CAPTION = "Text read by OCR from a picture. It may contain errors."
UNIT_NAMES = {"page": "Page", "slide": "Slide"}
# What a unit's OCR status says about its pictures (reader/ocr.py). "done" is not a gap.
OCR_GAPS = {
    "no_text": "A picture here has no readable text: OCR found none.",
    "no_readable_image": "A picture here could not be opened, so its text (if any) is not shown.",
    "failed": "OCR failed on a picture here, so its text (if any) is not shown.",
    "unavailable": "OCR is not installed, so the text of a picture here is not shown.",
    "deferred": "OCR ran out of time before a picture here, so its text (if any) is not shown.",
    "disabled": "OCR is switched off, so the text of a picture here is not shown.",
}
OCR_DROPPED = "Some of what OCR found in a picture here looked like noise and was left out."


@dataclass
class Block:
    kind: str                                  # DOC_KINDS hold the document's words; OWN_KINDS hold SummarEase's
    text: str = ""
    level: int = 2                             # headings
    rows: list = field(default_factory=list)   # tables: [[cell, ...], ...]; lists: [item, ...]

    def words(self):
        return words("\n".join(["\n".join(r) if isinstance(r, list) else r for r in self.rows] + [self.text]))


def words(text):
    return text.split()


def doc_words(blocks):
    return [w for b in blocks if b.kind in DOC_KINDS for w in b.words()]


# -- from the reader's record ---------------------------------------------------------------------------------
def from_record(record):
    """Blocks for a DocumentRecord, in reading order, with gaps disclosed where they are and counted at the top."""
    out, gapped = [], []
    body = _body_size(record) if record.format == "pdf" else None
    for u in record.units:
        name = UNIT_NAMES.get(record.unit)
        if name:
            out.append(Block("label", f"{name} {u.index}" + (" (hidden in the presentation)" if u.kind == "hidden slide" else "")))
        out += _native(record, u, body)
        if u.ocr_text:
            out += [Block("note", OCR_CAPTION), Block("ocr", u.ocr_text)]
        gaps = ([OCR_GAPS[u.ocr_status]] if u.suspected_unread and u.ocr_status in OCR_GAPS else []) \
            + ([OCR_DROPPED] if u.ocr_status == "done" and u.ocr_discarded_chars else [])
        # ponytail: the OCR status is per unit, so a unit with one read and one unreadable picture is not flagged.
        out += [Block("gap", g) for g in gaps]
        if gaps:
            gapped.append(u.index)
        if u.notes:
            out += [Block("note", "Speaker notes"), Block("notes", u.notes)]
    if gapped:
        plural = "s" * (len(gapped) > 1)
        where = f"{UNIT_NAMES[record.unit].lower()}{plural} {_list(gapped)}" if record.unit in UNIT_NAMES \
            else f"{len(gapped)} place{plural}"
        out.insert(0, Block("gap", f"Not everything could be read: {where}. Each is marked below."))
    return out


def _list(numbers, most=10):
    s = [str(n) for n in numbers]
    if len(s) > most:
        return ", ".join(s[:most]) + f" and {len(s) - most} more"
    return s[0] if len(s) == 1 else ", ".join(s[:-1]) + " and " + s[-1]


def _native(record, u, body):
    if record.format == "pdf":
        return _guarded(u, _pdf_blocks(u, body))
    if record.format == "pptx":
        return _guarded(u, _slide_blocks(u))
    return _flow_block(u)


def _guarded(u, blocks):
    """The layout is the reader's too, but if its words ever differ from the unit's text, show the text itself."""
    return blocks if doc_words(blocks) == words(u.text) else _plain(u.text)


def _plain(text):
    return [Block("lines", p) for p in re.split(r"\n\s*\n", text) if p.strip()]


def _body_size(record):
    """The commonest line size in the document, weighted by characters: the size of its body text."""
    sizes = Counter()
    for u in record.units:
        for b in (u.layout or {}).get("blocks", []):
            for line in b["lines"]:
                if line["size"]:
                    sizes[line["size"]] += len(line["text"].strip())
    return sizes.most_common(1)[0][0] if sizes else None


def _pdf_blocks(u, body):
    out = []
    for b in (u.layout or {}).get("blocks", []):
        lines = [l for l in b["lines"] if l["text"].strip()]
        texts = [l["text"].strip() for l in lines]
        if not texts:
            continue
        smallest = min(l["size"] or 0 for l in lines)
        if (body and smallest >= body * HEADING_RATIO and len(texts) <= HEADING_MAX_LINES
                and sum(map(len, texts)) <= HEADING_MAX_CHARS):
            out.append(Block("heading", " ".join(texts), level=1 if smallest >= body * TITLE_RATIO else 2))
            continue
        para = []   # lines flow into one paragraph; a line that starts with a list mark starts a new one
        for t in texts:
            if para and LIST_MARK.match(t):
                out.append(Block("paragraph", " ".join(para)))
                para = []
            para.append(t)
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
    return _plain(text)


# -- HTML for the view ----------------------------------------------------------------------------------------
def to_html(blocks, t):
    """The blocks as HTML for a QTextDocument, in the colours of theme t (a tokens.THEMES entry)."""
    para = f"margin-top:0; margin-bottom:{tk.RELATED + tk.TIGHT}px;"
    out = [f'<body style="font-family:\'{tk.FONT}\'; font-size:{tk.TEXT_READING}px; color:{t["text"]};">']
    for b in blocks:
        e = escape(b.text).replace("\n", "<br>")
        if b.kind == "label":
            out.append(f'<p style="margin-top:{tk.PAD}px; margin-bottom:{tk.RELATED}px; color:{t["secondary"]}; '
                       f'font-size:{tk.TEXT_CAPTION}px; font-weight:{tk.WEIGHT_STRONG};">{e}</p>')
        elif b.kind == "note":
            out.append(f'<p style="margin-top:{tk.RELATED}px; margin-bottom:{tk.TIGHT}px; color:{t["secondary"]}; '
                       f'font-size:{tk.TEXT_SECONDARY}px;">{e}</p>')
        elif b.kind == "gap":
            out.append(f'<p style="{para} color:{t["amber"]}; font-size:{tk.TEXT_SECONDARY}px;">{e}</p>')
        elif b.kind in ("title", "heading"):
            size = tk.TEXT_TITLE if b.level == 1 else tk.TEXT_HEADING if b.level == 2 else tk.TEXT_READING + 1
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

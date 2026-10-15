"""Export (record C6, C14): a summary as a new PDF with real, searchable text (PyMuPDF) or a new Word file (the
standard library). Never written over anything: each export goes to a temporary file in the chosen folder, is read
back and checked, then saved under a name that is free (a taken name gets " (2)", " (3)", ...)."""
import hashlib
import io
import os
import re
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from . import tokens as tk


class ExportError(Exception):
    """A fixed, text-free reason the export was not saved."""


# -- Word -----------------------------------------------------------------------------------------------------
_W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")    # not allowed in XML; never part of a word
_STYLES = {"title": "Title", "section": "Heading2", "note": "Note", "gap": "Gap", "item": "ListParagraph"}


def _style(sid, name, size, bold=False, italic=False, colour=None, before=0, after=120):
    rpr = f'<w:sz w:val="{size * 2}"/>' + ("<w:b/>" if bold else "") + ("<w:i/>" if italic else "") \
        + (f'<w:color w:val="{colour.lstrip("#")}"/>' if colour else "")
    return (f'<w:style w:type="paragraph" w:styleId="{sid}"><w:name w:val="{name}"/><w:qFormat/>'
            f'<w:pPr><w:spacing w:before="{before}" w:after="{after}"/></w:pPr><w:rPr>{rpr}</w:rPr></w:style>')


def docx_bytes(paras):
    """paras: [(style, text)] from present.paragraphs."""
    t = tk.THEMES["light"]
    body = "".join(
        f'<w:p><w:pPr><w:pStyle w:val="{_STYLES[s]}"/></w:pPr><w:r><w:t xml:space="preserve">'
        f'{xml_escape(_CONTROL.sub("", text))}</w:t></w:r></w:p>' for s, text in paras)
    styles = (f'<w:styles {_W}><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="{tk.FONT}" w:hAnsi="{tk.FONT}" '
              f'w:cs="{tk.FONT}"/><w:sz w:val="22"/></w:rPr></w:rPrDefault></w:docDefaults>'
              '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
              + _style("Title", "Title", 20, bold=True, after=120)
              + _style("Heading2", "heading 2", 13, bold=True, before=240, after=80)
              + _style("Note", "Note", 9, colour=t["secondary"], after=160)
              + _style("Gap", "Gap", 9, colour=t["amber"], after=60)
              + _style("ListParagraph", "List Paragraph", 11, after=80) + "</w:styles>")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.'
                   'wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/'
                   'vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>')
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
                   'officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr("word/_rels/document.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
                   'styles" Target="styles.xml"/></Relationships>')
        z.writestr("word/styles.xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + styles)
        z.writestr("word/document.xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   f'<w:document {_W}><w:body>{body}<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
                   '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134"/></w:sectPr></w:body></w:document>')
    return buf.getvalue()


# -- PDF ------------------------------------------------------------------------------------------------------
# style: (size in points, bold, colour role, space before, space after). Text is placed with PyMuPDF's TextWriter,
# which does not form ligatures: an HTML layout turned "find" into "ﬁnd", and the PDF could not be searched for it.
PDF_STYLES = {"title": (20, True, "text", 0, 6), "section": (13, True, "text", 12, 4), "note": (9, False, "secondary", 0, 10),
              "gap": (9, False, "amber", 0, 3), "item": (11, False, "text", 0, 5)}
PDF_MARGIN = 56
PDF_LEADING = 1.35


def pdf_bytes(paras):
    import pymupdf

    t = tk.THEMES["light"]
    regular, bold, fallback = pymupdf.Font("helv"), pymupdf.Font("hebo"), pymupdf.Font(ordering=0)
    doc = pymupdf.open()
    paper = pymupdf.paper_rect("a4")
    left, right, bottom = PDF_MARGIN, paper.width - PDF_MARGIN, paper.height - PDF_MARGIN
    y = bottom + 1                   # so the first line starts a page

    def runs(text, font):
        """Pieces of text with the font that has their glyphs: the style's font, else the fallback."""
        out = []
        for c in text:
            f = font if font.has_glyph(ord(c)) or c == " " else fallback
            if out and out[-1][1] is f:
                out[-1][0] += c
            else:
                out.append([c, f])
        return out

    def width(text, font, size):
        return sum(f.text_length(s, size) for s, f in runs(text, font))

    for style, text in paras:
        size, strong, role, before, after = PDF_STYLES[style]
        font = bold if strong else regular
        colour = tuple(int(t[role].lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
        text = " ".join(_CONTROL.sub("", text).split())
        indent = width("• ", font, size) if style == "item" else 0
        lines, line = [], ""          # greedy wrap at spaces; a word is never split
        for word in text.split(" "):
            trial = f"{line} {word}" if line else word
            if line and width(trial, font, size) > right - left - (indent if lines else 0):
                lines.append(line)
                line = word
            else:
                line = trial
        lines.append(line)
        y += before
        tw = pymupdf.TextWriter(paper)      # each paragraph is written in order, so the text reads in order
        for i, line in enumerate(lines):
            if y + size * PDF_LEADING > bottom:
                if doc.page_count:
                    tw.write_text(doc[-1], color=colour)
                    tw = pymupdf.TextWriter(paper)
                doc.new_page(width=paper.width, height=paper.height)
                y = PDF_MARGIN
            x = left + (indent if i else 0)
            for piece, f in runs(line, font):
                tw.append((x, y + size), piece, font=f, fontsize=size)
                x += f.text_length(piece, size)
            y += size * PDF_LEADING
        tw.write_text(doc[-1], color=colour)
        y += after
    data = doc.tobytes(garbage=3, deflate=True)
    doc.close()
    return data


# -- saving ---------------------------------------------------------------------------------------------------
def expected_words(paras):
    return " ".join(_CONTROL.sub("", t) for _, t in paras).split()


def check(path, paras):
    """The file opens with the reader, and its text is the export's text, word for word."""
    from .reader import read_document

    res = read_document(path)
    if res.status != "ok":
        raise ExportError("the new file could not be read back")
    got = " ".join(u.text for u in res.record.units).split()
    if got != expected_words(paras):
        raise ExportError("the new file's text did not match the summary")


def free_name(path):
    path = Path(path)
    n = 2
    candidate = path
    while candidate.exists():
        candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
        n += 1
    return candidate


def save(paras, path):
    """Write paras to a new file at path (".pdf" or ".docx"), or the next free name. Returns (final path, sha256).
    Nothing that exists is ever overwritten."""
    path = Path(path)
    kind = path.suffix.lower()
    if kind not in (".pdf", ".docx"):
        raise ExportError("SummarEase exports PDF and Word (.docx) files")
    data = pdf_bytes(paras) if kind == ".pdf" else docx_bytes(paras)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".summarease-", suffix=kind)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        check(tmp, paras)
        for _ in range(100):
            final = free_name(path)
            try:
                os.link(tmp, final)         # fails if the name was taken meanwhile: never overwrites
                break
            except FileExistsError:
                continue
            except OSError:                 # no hard links here (some network or FAT drives): exclusive create
                try:
                    with open(final, "xb") as f:
                        f.write(data)
                    break
                except FileExistsError:
                    continue
        else:
            raise ExportError("no free file name was found")
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
    return final, hashlib.sha256(data).hexdigest()

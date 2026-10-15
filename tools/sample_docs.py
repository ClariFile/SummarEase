"""Invented documents for tests and screenshots: a text PDF (portrait, headings, bold subheadings, paragraphs and a
large-print paragraph that must not become a heading) and a slide PDF (landscape, titles and bullets). Content is
generated from a fixed word list with a fixed seed, so it is the same every time and copies nothing real."""
import random

import pymupdf

WORDS = """system network packet layer model data storage index query cache record field value method result
process thread memory signal channel protocol address route table policy rule access control audit review design
module service client server request response session token schema version update change error report measure
sample test case unit level budget summary section point detail""".split()


def sentence(rng, n=None):
    n = n or rng.randint(9, 22)
    words = [rng.choice(WORDS) for _ in range(n)]
    return " ".join(words).capitalize() + "."


def paragraph(rng, sentences=4):
    return " ".join(sentence(rng) for _ in range(sentences))


def _write(page, x, y, text, size, bold=False, right=540):
    """Text wrapped from (x, y) to the right margin; returns the height used. Raises if it was not written."""
    rect = pymupdf.Rect(x, y, right, y + size * 1.5 * (len(text) * size * 0.5 // (right - x) + 2))
    rc = page.insert_textbox(rect, text, fontsize=size, fontname="hebo" if bold else "helv")
    if rc < 0:
        raise ValueError("text did not fit")
    return rect.height - rc


def make_text_pdf(path, pages=3, seed=1):
    """Portrait pages: a title, then per page a heading, a bold subheading, paragraphs, a large-print paragraph."""
    rng = random.Random(seed)
    doc = pymupdf.open()
    for p in range(pages):
        page = doc.new_page()   # portrait
        y = 60
        if p == 0:
            y += _write(page, 60, y, "Invented Handbook of Systems", 24) + 12
        y += _write(page, 60, y, f"Part {p + 1} Overview of the model", 16) + 8
        y += _write(page, 60, y, "Design notes", 11, bold=True) + 6
        for _ in range(3):
            y += _write(page, 60, y, paragraph(rng), 11) + 10
        y += _write(page, 60, y,
                    "A large print paragraph of invented words that runs well past twelve words and must stay a "
                    "paragraph, never a heading.", 15) + 10
        _write(page, 60, y,
               "A bold sentence in the body text that is much longer than any heading would ever be.", 11, bold=True)
    doc.save(path)
    return path


def make_slide_pdf(path, slides=6, seed=2):
    """Landscape slides: a title slide, an agenda, content slides with bullets, and a summary slide."""
    rng = random.Random(seed)
    doc = pymupdf.open()
    titles = ["Invented Course on Networks", "Agenda"] + [f"Topic {i} of the course" for i in range(1, slides - 2)] \
        + ["Summary"]
    for i, title in enumerate(titles):
        page = doc.new_page(width=842, height=595)   # landscape
        _write(page, 50, 40, title, 30, right=790)
        if i == 0:
            _write(page, 50, 120, "Lecture 1", 18, right=790)
            continue
        bullets = [t for t in titles[2:-1]] if title == "Agenda" else \
            [f"- {sentence(rng, rng.randint(4, 9))}" for _ in range(4)]
        y = 130
        for b in bullets:
            y += _write(page, 60, y, b, 18, right=790) + 10
    doc.save(path)
    return path

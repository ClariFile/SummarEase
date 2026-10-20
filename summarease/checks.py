"""The automatic checks (EVALUATION.md), shared by the tests and `python -m tools.evaluate`. Each returns a list of
problems; a problem names a level, a line number and a unit, never document text."""
import re

from . import present
from . import tokens as tk
from .readable import GAP_REASONS, OWN_KINDS
from .summarize import BRIEF_LINES, BUDGETS, KEY_LINES, LEVELS, SECTION_LINES

ENDS = re.compile(r"[.!?][\"')\]”’]*$")     # how a sentence ends (summarize.sentences)


def unit_texts(record=None, blocks=None):
    """{unit: {kind: text}} that a summary line may come from: the reader's own text for a document (not the
    view's), or the pasted paragraphs. Line breaks are kept: they mark where a line starts and ends. "layout" is the
    reader's own layout lines, one per line: two runs printed side by side on one row are one line of the text but
    two lines of the layout."""
    if record is not None:
        return {u.index: {"text": u.text or "", "ocr": u.ocr_text or "", "note": u.notes or "",
                          "layout": "\n".join(l["text"] for b in (u.layout or {}).get("blocks", []) for l in b["lines"])}
                for u in record.units}
    return {b.unit: {"text": b.text, "ocr": "", "note": "", "layout": ""} for b in blocks if b.unit is not None}


def whole_unit(text, source):
    """text is a complete sentence, bullet or line of source, word for word: it starts where a line or a sentence
    starts and ends where a line or a sentence ends, never inside one ("publish this." is not in "Do not publish
    this.")."""
    words = text.split()
    if not words:
        return False
    for m in re.finditer(r"(?<!\S)" + r"\s+".join(map(re.escape, words)) + r"(?!\S)", source):
        before = source[:m.start()].rstrip(" \t")
        after = source[m.end():].lstrip(" \t")
        starts = not before or before.endswith("\n") or ENDS.search(before)
        ends = not after or after.startswith("\n") or ENDS.search(words[-1])
        if starts and ends:
            return True
    return False


def traceable(summary, texts):
    """Every line equals a sentence, bullet or line of the document, word for word, and its link points to the
    page, slide or section where that text is (OCR lines in the OCR text, speaker notes in the notes)."""
    problems = []
    for i, l in enumerate(summary.lines, 1):
        where = {"ocr": "ocr", "note": "note"}.get(l.kind, "text")
        found = l.unit in texts and (whole_unit(l.text, texts[l.unit][where])
                                     or where == "text" and whole_unit(l.text, texts[l.unit]["layout"]))
        if not found:
            problems.append(f"{summary.level} line {i}: not a whole line where it links (unit {l.unit})")
    return problems


def readable_words(blocks):
    """W, counted here from the readable text, not taken from the summary."""
    return sum(len(b.words()) for b in blocks if b.kind not in OWN_KINDS)


def permitted(level, total):
    """The most words a level may hold (record C12; Comprehensive at least Detailed's budget, record 0.5)."""
    most = lambda lv: max(BUDGETS[lv][0], int(BUDGETS[lv][1] * total))
    return max(most("comprehensive"), most("detailed")) if level == "comprehensive" else most(level)


def within_budget(summary, blocks):
    """The level keeps its budget in words, calculated from the readable text, and its line limits (record C12)."""
    problems = []
    limit = permitted(summary.level, readable_words(blocks))
    if summary.words > limit:
        problems.append(f"{summary.level}: {summary.words} words over the budget of {limit}")
    n = len(summary.lines)
    if summary.level == "brief" and n > BRIEF_LINES:
        problems.append(f"brief: {n} lines")
    if summary.level == "key" and n > KEY_LINES:
        problems.append(f"key: {n} lines")
    if summary.level == "detailed":
        for s, ls in summary.sections:
            body = [l for l in ls if l is not s.heading]
            if len(body) > SECTION_LINES:
                problems.append(f"detailed: {len(body)} lines in one section (unit {ls[0].unit})")
    return problems


def explained(summary):
    """An empty summary says why; a summary with lines does not claim to be empty."""
    if not summary.lines and not summary.empty:
        return [f"{summary.level}: empty without a reason"]
    if summary.lines and summary.empty:
        return [f"{summary.level}: has lines but says it is empty"]
    return []


def nested(summaries):
    """{level: Summary}: every line of a level is in the next level up."""
    problems = []
    for low, high in zip(LEVELS, LEVELS[1:]):
        if low in summaries and high in summaries:
            missing = {l.id for l in summaries[low].lines} - {l.id for l in summaries[high].lines}
            if missing:
                problems.append(f"{len(missing)} {low} line(s) missing from {high}")
    return problems


def gaps_disclosed(summary, blocks, record=None):
    """Every unit not fully read is named in the summary's gap details: the units the readable text marks, and the
    units the reader itself reports (so a disclosure lost in the view does not pass by agreement). A partial OCR
    failure inside a unit the reader calls done cannot be seen here (READER.md, H8)."""
    marked = {b.unit for b in blocks if b.kind == "gap"}
    if record is not None:
        marked |= {u.index for u in record.units if u.suspected_unread and u.ocr_status in GAP_REASONS}
    told = {u for u, _ in summary.gaps}
    return [f"{summary.level}: {len(marked - told)} gap(s) not disclosed"] if marked - told else []


def visible(summary):
    """What the user sees and takes away: the pane (lines, references, links, marks, notes, gaps) and the
    Copy/Export text."""
    return present.to_html(summary, tk.THEMES["light"], details=True), present.paragraphs(summary)


def same(a, b):
    """Two summaries show the user the same thing: the same lines, references, links, marks and notes."""
    return visible(a) == visible(b)

"""The automatic checks (EVALUATION.md), shared by the tests and `python -m tools.evaluate`. Each returns a list of
problems; a problem names a level, a line number and a unit, never document text."""
from .summarize import BRIEF_LINES, KEY_LINES, LEVELS, SECTION_LINES, norm


def unit_texts(record=None, blocks=None):
    """{unit: {kind: text}} that a summary line may come from: the reader's own text for a document (not the
    view's), or the pasted paragraphs."""
    if record is not None:
        return {u.index: {"text": norm(u.text), "ocr": norm(u.ocr_text or ""), "note": norm(u.notes or "")}
                for u in record.units}
    return {b.unit: {"text": norm(b.text), "ocr": "", "note": ""} for b in blocks if b.unit is not None}


def traceable(summary, texts):
    """Every line equals a sentence, bullet or line of the document, word for word, and its link points to the
    page, slide or section where that text is (OCR lines in the OCR text, speaker notes in the notes)."""
    problems = []
    for i, l in enumerate(summary.lines, 1):
        where = {"ocr": "ocr", "note": "note"}.get(l.kind, "text")
        if l.unit not in texts or l.text not in texts[l.unit][where]:
            problems.append(f"{summary.level} line {i}: not found where it links (unit {l.unit})")
    return problems


def within_budget(summary):
    """The level keeps its budget in words and its line limits (record C12)."""
    problems = []
    if summary.words > summary.budget:
        problems.append(f"{summary.level}: {summary.words} words over the budget of {summary.budget}")
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


def nested(summaries):
    """{level: Summary}: every line of a level is in the next level up."""
    problems = []
    for low, high in zip(LEVELS, LEVELS[1:]):
        if low in summaries and high in summaries:
            missing = {l.id for l in summaries[low].lines} - {l.id for l in summaries[high].lines}
            if missing:
                problems.append(f"{len(missing)} {low} line(s) missing from {high}")
    return problems


def gaps_disclosed(summary, blocks):
    """Every unit the readable text marks as not fully read is named in the summary's gap details."""
    marked = {b.unit for b in blocks if b.kind == "gap"}
    told = {u for u, _ in summary.gaps}
    return [f"{summary.level}: {len(marked - told)} gap(s) not disclosed"] if marked - told else []


def same(a, b):
    """Two summaries show the same lines, in the same sections and order."""
    return [(s.label, [(l.text, l.unit, l.kind) for l in ls]) for s, ls in a.sections] == \
        [(s.label, [(l.text, l.unit, l.kind) for l in ls]) for s, ls in b.sections] and a.gaps == b.gaps

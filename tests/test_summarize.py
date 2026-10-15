"""M2: extractive summaries at the four levels (record C12, C13), by every method. The automatic checks of
EVALUATION.md on invented documents: traceable lines, budgets kept, levels nested, gaps disclosed, the same output
for the same input, and renaming a file changes nothing. Plus what each method promises."""
import shutil

import pytest

from office_fixtures import make_docx, make_odt, make_pptx
from summarease import checks
from summarease.readable import Block, from_record, from_text
from summarease.reader import read_document
from summarease.summarize import (
    BUDGETS, LEVELS, Source, budget, build, method_for, sentences, source_from_record, source_from_text,
)
from summarease.worker import pdf_bold
from tools.sample_docs import make_slide_pdf, make_text_pdf


def load(path):
    res = read_document(path)
    blocks = from_record(res.record, pdf_bold(path, res.sha256) if path.suffix == ".pdf" else None)
    return res.record, blocks, source_from_record(res.record, blocks)


DOCS = [(make_text_pdf, "t.pdf"), (make_slide_pdf, "s.pdf"), (make_pptx, "a.pptx"), (make_docx, "a.docx"),
        (make_odt, "a.odt")]


@pytest.mark.parametrize("make, name", DOCS)
@pytest.mark.parametrize("method", ["baseline", "structure", "ranking"])
def test_every_level_passes_the_automatic_checks(tmp_path, make, name, method):
    path = make(tmp_path / name)
    record, blocks, src = load(path)
    levels = {lv: build(src, lv, method) for lv in LEVELS}
    texts = checks.unit_texts(record)
    for lv, s in levels.items():
        assert s.lines, lv
        assert checks.traceable(s, texts) == []
        assert checks.within_budget(s) == []
        assert checks.gaps_disclosed(s, blocks) == []
        assert checks.same(s, build(src, lv, method))                          # same input, same output
    assert checks.nested(levels) == []
    renamed = tmp_path / ("other name" + path.suffix)
    shutil.copyfile(path, renamed)
    _, _, moved = load(renamed)
    assert all(checks.same(levels[lv], build(moved, lv, method)) for lv in LEVELS)   # the name changes nothing


def test_budgets_follow_the_record():
    assert BUDGETS == {"brief": (30, 0.03), "key": (80, 0.10), "detailed": (150, 0.20), "comprehensive": (0, 0.40)}
    assert [budget(lv, 10_000) for lv in LEVELS] == [300, 1000, 2000, 4000]
    assert [budget(lv, 100) for lv in LEVELS] == [30, 80, 150, 40]


def test_a_long_document_keeps_every_budget_and_comprehensive_is_never_a_copy(tmp_path):
    record, blocks, src = load(make_text_pdf(tmp_path / "t.pdf", pages=30))
    levels = {lv: build(src, lv, "ranking") for lv in LEVELS}
    assert all(checks.within_budget(s) == [] for s in levels.values())
    assert levels["comprehensive"].words <= 0.4 * levels["comprehensive"].total
    assert len(levels["brief"].lines) <= 3 and len(levels["key"].lines) <= 12
    detailed = levels["detailed"]
    assert {s.heading.text for s, _ in detailed.sections if s.heading} >= {"Part 1 Overview of the model"}


def test_the_baseline_takes_the_opening_lines(tmp_path):
    _, _, src = load(make_text_pdf(tmp_path / "t.pdf", pages=4))
    key = build(src, "key", "baseline")
    ids = [l.id for l in key.lines]
    assert ids == sorted(ids) and key.lines[0].unit == 1


def test_slides_by_structure_brief_is_the_deck_title_and_the_summary_slide(tmp_path):
    _, _, src = load(make_slide_pdf(tmp_path / "s.pdf", slides=8))
    assert src.slides and method_for(src) == "structure"
    brief = build(src, "brief", "structure")
    assert brief.lines[0].text == "Invented Course on Networks"
    assert all(l.unit in (1, 8) for l in brief.lines)                         # the title slide and "Summary"
    detailed = build(src, "detailed", "structure")
    assert [s.heading.text for s, _ in detailed.sections][:2] == ["Invented Course on Networks", "Agenda"]


def test_speaker_notes_and_hidden_slides_appear_only_at_comprehensive(tmp_path):
    _, _, src = load(make_pptx(tmp_path / "a.pptx"))
    hidden = set(src.hidden)
    assert hidden
    for lv in ("brief", "key", "detailed"):
        s = build(src, lv, "structure")
        assert not any(l.kind == "note" or l.unit in hidden for l in s.lines), lv
    full = build(src, "comprehensive", "structure")
    assert any(l.kind == "note" for l in full.lines) and any(l.unit in hidden for l in full.lines)


def test_prose_uses_the_baseline_in_the_app_until_a_method_beats_it():
    src = source_from_text(from_text("One sentence here. Another one here."))
    assert method_for(src) == "baseline"


def test_ranking_removes_near_duplicates_and_prefers_central_sentences():
    text = ("Caching keeps query results in memory. "
            "Caching keeps query results in memory for later. "
            "The weather was mild that day in the old town. "
            "A cache stores query results so a repeated query is answered from memory. "
            "Query results in memory make a repeated query fast.")
    s = build(source_from_text(from_text(text)), "comprehensive", "ranking")
    texts = [l.text for l in s.lines]
    assert not ("Caching keeps query results in memory." in texts and
                "Caching keeps query results in memory for later." in texts)
    key = build(source_from_text(from_text(text)), "brief", "ranking")
    assert "The weather was mild that day in the old town." not in [l.text for l in key.lines]


def test_ocr_never_stands_alone_at_brief_when_there_is_native_text():
    blocks = [Block("lines", "Native sentence one is here. Native sentence two is here.", unit=1),
              Block("ocr", "Picture words read by OCR here", unit=2)]
    s = build(Source(blocks, "page", False), "brief", "ranking")
    assert s.lines and all(l.kind != "ocr" for l in s.lines)


def test_sentences_keep_every_word_and_do_not_split_abbreviations_or_list_marks():
    text = "1. First point, e.g. this one. Dr. Smith agreed. It costs 3.5 units! Next? Yes."
    parts = sentences(text)
    assert " ".join(parts).split() == text.split()
    assert parts == ["1. First point, e.g. this one.", "Dr. Smith agreed.", "It costs 3.5 units!", "Next?", "Yes."]


def test_pasted_text_is_summarized_and_linked_to_its_paragraphs():
    text = "\n\n".join(f"Paragraph {i} says something about caching and memory. It adds detail." for i in range(1, 9))
    blocks = from_text(text)
    s = build(source_from_text(blocks), "key", "baseline")
    assert checks.traceable(s, checks.unit_texts(blocks=blocks)) == []
    assert s.unit == "paragraph" and s.lines[0].unit == 1

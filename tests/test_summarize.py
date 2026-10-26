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
        assert checks.within_budget(s, blocks) == [] and checks.explained(s) == []
        assert checks.gaps_disclosed(s, blocks, record) == []
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
    assert all(checks.within_budget(s, blocks) == [] for s in levels.values())
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


# -- audit regressions (docs/FROM_CLASSIFILE.md, H1-H3; owner's answers to Q1 and Q2, 2026-10-20) -------------------
def many_headings(n=40, heading="Invented heading with seven plain words"):
    return [b for i in range(n) for b in (Block("heading", f"{heading} {i}", unit=i + 1),
                                          Block("lines", "Short factual sentence.", unit=i + 1))]


def test_headings_count_against_the_budget_and_sections_that_do_not_fit_are_named():
    blocks = many_headings()
    src = Source(blocks, "page", False)
    levels = {lv: build(src, lv, "baseline") for lv in LEVELS}
    for lv, s in levels.items():
        assert checks.within_budget(s, blocks) == [], lv
    assert checks.nested(levels) == []
    detailed, full = levels["detailed"], levels["comprehensive"]
    assert detailed.omitted and full.budget == max(budget("comprehensive", full.total), budget("detailed", full.total))
    shown = {s.heading.unit for s, _ in detailed.sections}
    assert {u for _, u in detailed.omitted} == set(range(1, 41)) - shown        # every section shown or named
    from summarease import present
    note = next(n for n in present.notes(detailed) if "didn't fit" in n)
    assert note.startswith(f"{len(detailed.omitted)} sections didn't fit this level's length")


def test_hidden_slide_headings_and_long_headings_never_exceed_comprehensive():
    blocks = many_headings(30, "An invented and rather long heading that goes on for many more words than usual")
    src = Source(blocks, "slide", True, hidden=frozenset(range(1, 31, 2)))
    s = build(src, "comprehensive", "structure")
    assert checks.within_budget(s, blocks) == []


def test_a_table_only_document_says_why_its_summary_is_empty():
    s = build(Source([Block("table", rows=[["Invented fact", "Meaningful value"]], unit=1)], "block", False),
              "detailed", "baseline")
    assert not s.lines and s.empty == "unusable" and s.tables == 1 and checks.explained(s) == []


def test_a_sentence_longer_than_the_budget_is_never_cut_and_the_reason_is_given():
    text = " ".join(["word"] * 199) + " end."
    s = build(source_from_text(from_text(text)), "brief", "baseline")
    assert not s.lines and s.empty == "none_fit" and checks.explained(s) == []


def test_an_empty_document_and_an_ocr_only_document_get_an_accurate_outcome():
    assert build(Source([], "page", False), "key", "baseline").empty == "no_text"
    ocr_only = build(Source([Block("ocr", "Picture words read by OCR here", unit=1)], "page", False), "brief", "baseline")
    assert ocr_only.lines and ocr_only.lines[0].kind == "ocr" and not ocr_only.empty


def test_a_short_document_is_shown_whole_and_says_so():
    s = build(source_from_text(from_text("Four invented words here.")), "comprehensive", "baseline")
    assert [l.text for l in s.lines] == ["Four invented words here."] and s.whole
    long = build(source_from_text(from_text(" ".join(f"Sentence {i} is invented." for i in range(400)))),
                 "comprehensive", "baseline")
    assert not long.whole


def test_the_checks_catch_deliberate_mutations():
    from dataclasses import replace

    blocks = from_text("Do not publish this. Keep the second sentence too.")
    texts = checks.unit_texts(blocks=blocks)
    s = build(source_from_text(blocks), "comprehensive", "baseline")
    assert checks.traceable(s, texts) == []
    mutate = lambda **kw: replace(s, sections=[(sec, [replace(ls[0], **kw)] + ls[1:]) for sec, ls in s.sections])
    assert checks.traceable(mutate(text="publish this."), texts)                       # a negation dropped
    assert checks.traceable(mutate(text="Do not publish"), texts)                      # a boundary moved
    assert checks.traceable(mutate(unit=2), texts)                                     # the wrong location
    assert checks.within_budget(replace(s, budget=999, sections=[(sec, ls * 40) for sec, ls in s.sections]), blocks)
    assert not checks.same(s, replace(s, labels=["Another label"]))                    # a reference label
    assert not checks.same(s, mutate(kind="ocr"))                                      # a marker
    assert not checks.same(s, replace(s, whole=not s.whole))                           # a note


def test_a_line_that_repeats_the_start_of_the_line_before_is_still_found():
    source = "Alpha beta gamma\nAlpha beta gamma delta epsilon zeta\nNext"
    assert checks.whole_unit("Alpha beta gamma delta epsilon zeta", source)


def test_generated_context_cases_from_the_second_handoff():
    """Diagnostic cases (second ClassiFile handoff), checked against the current method: a title repeated on every
    page is taken once and the one conclusion is kept; a line with "only if" is taken whole or not at all; the
    rejected alternative is never shown without the choice made. Generated text: no accuracy claim."""
    from summarease.readable import from_text
    from summarease.summarize import build, source_from_text

    def lines(text, level):
        s = build(source_from_text(from_text(text)), level, "baseline")
        return [l.text for l in s.lines]

    page = "Quarterly Network Review\n\nThe agenda covers routers, switches and links."
    conclusion = "Conclusion: replace the core switch before March because it drops packets under load."
    got = lines("\n\n".join([page] * 6 + [conclusion]), "key")
    assert got.count("Quarterly Network Review") == 1 and conclusion in got
    qualified = "Restoring is safe only if the database is stopped first; otherwise data is corrupted."
    text = ("Backups run every night.\n\n" + qualified + "\n\nThe team chose option B. Option A was considered "
            "first.\n\nLater, option A was rejected because it costs too much.")
    for level in ("brief", "key"):
        got = lines(text, level)
        assert all(l in text.split("\n\n") for l in got)                  # whole source units only
        assert not any("only if" in l and l != qualified for l in got)
        assert not any("rejected" in l for l in got) or any("chose option B" in l for l in got)

# SummarEase status

2026-10-15 · decision record version 0.2

## Done: M0 Project setup (2026-10-14)

- Python 3.12 virtual environment; pinned requirements: PyMuPDF and PySide6, and pytest for development.
- AGPL-3.0 licence (PyMuPDF is AGPL); `.gitignore` leaves out `data/` and test output.
- The reader, copied unchanged from ClassiFile (READER.md, option (a)). Since 2026-10-15 its source is ClassiFile's
  tag `reader-v6`, with the hash of each file in `summarease/reader/SOURCE.md`; the copy matches all six.
- The pre-push privacy audit (`tools/audit_terms.py`) with a local, untracked term list.
- An empty PySide6 window with the SummarEase icon.
- 10 tests: the reader reads a PDF, a PPTX, a DOCX and an ODT made for the tests without changing them; OCR reads
  text that is only in a picture; the reader imports nothing from the rest of SummarEase; the window opens with
  the network blocked; the audit matches plain and pattern terms; the reader check (added 2026-10-15, moved
  forward from M1 at the owner's request): `tests/test_reader_copy.py` fails if any file in `summarease/reader/`
  is added, missing or differs from the hashes in `SOURCE.md`.

## Planning, 2026-10-15 (documents only; no code changed)

- Record 0.2: four levels (C12) and extractive first (C13) confirmed by the owner, with testable definitions:
  what each level contains, length budgets relative to document length, nesting of sources, slides by structure,
  OCR trusted less. A local LLM (P3) stays a proposal.
- `EVALUATION.md`: the development set (copies of ClassiFile's development files), the owner's reference key
  points, the rubric, the automatic checks, one command, and a held-out set for a final check.
- `MILESTONES.md`: M1 starts with the reader check; M2 compares three methods against a baseline and keeps a
  method only if it beats the baseline on the rubric; M2's acceptance fixed (sentence, bullet or line, with a
  correct page, slide or section link).
- `DOS_AND_DONTS.md`: lessons since the handoff (themes and contrast, worker processes, in-place updates, safe
  exports, tests without timing, one evaluation command, update checks on everything) and the look.

## Open

- **What Export exports** (record P6): the owner's decision, below.
- **The owner's reference key points** for about 10 development documents, written before any method is tuned.
- **SummarEase's held-out set** (`data\final-check`), set aside by the owner before M2's tuning starts.
- ClassiFile's `data\validation` and `data\final-eval` stay unread until ClassiFile's CP5 is done.
- The repository's commits (M0, planning, reader check) are pushed to GitHub's `main` after the privacy audit
  (0 hits).

## Decision for the owner: what Export exports (P6)

The record confirms that Export makes a searchable PDF or a Word file, as new files only (C6). Which content it
holds is open.

| Option | What the user gets | Notes |
|---|---|---|
| a. The summary | the level on screen, each line with its page, slide or section | small; the links make it checkable |
| b. The readable text | the whole document as readable text (C5) | the words are the reader's, in order |
| c. A searchable copy of a scanned document | the scanned pages with their OCR text laid under them | a different feature: it writes OCR text into a copy of the document |
| d. Several of these | a and b; c later if wanted | |

**Recommendation: d, as "a and b".** Export what is on screen: the summary at its level, or the readable text,
each as a new PDF with real text (searchable by nature) or a Word file. Leave c out of v1:
- it is a separate feature with its own risks (OCR text placed under the wrong words, a copy that looks like the
  original but is not);
- ClariFile's rule so far is that OCR text is never inserted into any document, original or copy (ClassiFile's
  record A8). Option c would need the owner's explicit exception.

**How a Word file would be made.** A .docx file is a zip of a few XML parts. ClassiFile's and SummarEase's tests
already write .docx files by hand with the standard library (`tests/office_fixtures.py`). Recommendation: the
standard library (`zipfile` and plain XML for the document, its styles and its relationships), about 150 lines,
tested by reading the result back with the reader. The alternative is a new dependency (python-docx, MIT): less
code and richer formatting, but one more package to approve, pin and ship. A PDF needs nothing new: PyMuPDF,
already installed, writes PDF pages with real text.

## Next milestone

**M1 Read files and show the readable text view** (`MILESTONES.md`); its first task, the reader check, is already done. Only on the
owner's go-ahead, and after ClassiFile's own CP5 work: SummarEase must not delay it.

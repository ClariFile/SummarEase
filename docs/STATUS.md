# SummarEase status

2026-10-26 · decision record 0.5

## The second ClassiFile handoff (2026-10-26; [FROM_CLASSIFILE_PHASE2.md](FROM_CLASSIFILE_PHASE2.md))

Still waiting at the M2/M3 stop points below; M4 stays at its gate. Done from the handoff:
- **H8, partial OCR failures, fixed upstream and synced:** ClassiFile's reader keeps each OCR'd picture's outcome
  (extraction record 7, `ocr_pictures`, a `partial` status, `unread_gap()`), tagged `reader-v7` in ClassiFile (the
  tag is local there until the owner pushes it). The copy here was taken at that tag; `SOURCE.md` lists the new
  hashes and `tests/test_reader_copy.py` checks them.
- **Disclosure everywhere:** a unit that read one picture and not another keeps the text read and says "1 of its 2
  pictures couldn't be read (…)" in the gap details of every level, Copy, the view and both exports
  (`readable.gap_detail`). `checks.gaps_disclosed` reads the reader's own `unread_gap`, not the view's notes, so a
  disclosure the view loses is still caught (`tests/test_partial_ocr.py`). A fully read unit has no gap.
- **The whole worker job is bounded:** a watchdog ends the process at its time limit whatever it is doing, also
  when nothing polls it (`worker.Job`).
- **Stale results and source identity:** checked, no fault found: A's summary never lands on B, Copy and Export
  stay off until B's own summary, and the same path with new bytes is read anew (`tests/test_app.py`).
- **Generated context cases:** a repeated title, an "only if" qualification and a rejected alternative behave as
  the handoff asks with the current method; kept as regression cases (`tests/test_summarize.py`), not as accuracy.
- **Not done (the owner's part):** the independent reference key points and the blind method comparison; the M3
  review and packaging. 120 tests pass.

## Current checkpoint: audit fixes and M3 built (2026-10-20), waiting at the M2/M3 stop points

On 2026-10-20 the owner answered Q1–Q3 and asked for the fixes, M3 and the UX1/UX3/UX4 proposals to be built
(not UX5, the installer). Findings, questions and proposals are in [FROM_CLASSIFILE.md](FROM_CLASSIFILE.md).

**Owner's answers, to be written into the decision record by the owner** (the record is unchanged):
- **Q1:** strict budgets. A level never goes over its budget, headings included; a section that does not fit is
  left out and named in the summary, with a link to the Source. This changes C12's "every section that has
  readable text appears" for Detailed and Comprehensive.
- **Q2:** a document shorter than a level's budget is shown whole, and the summary says so.
- **Q3:** the user may choose the source document's folder for a new export. Nothing incidental is created there:
  the check copy is made in the system's temporary folder.

**Findings, as dispositioned:**

| Finding | State | Where |
|---|---|---|
| H1 headings over budget | Fixed: headings count against the room; omitted sections named; Comprehensive = max(40% W, Detailed's budget) | `summarize.build`, `_rounds` |
| H2 unexplained empty summaries | Fixed: no text / nothing usable / no whole line fits; tables said to be in the Source | `Summary.empty`, `present.notes` |
| H3 weak checks | Fixed: whole sentence/line at its location (overlapping occurrences included), budgets from W, visible output compared (pane, references, marks, notes, Copy/Export), reader-side gaps, empty results explained | `checks.py` |
| H4 parent folder bypass | Fixed: nested, any-case, symlink and junction paths refused before anything is opened or hashed | `tools/evaluate.collect` |
| H5 failures exit 0, unbounded | Fixed: exits 0/1/2/3, a worker with a deadline per document, duplicates counted, saved report with versions, OCR availability and set fingerprint, incomplete until done | `tools/evaluate.py` |
| H6 partial export left behind | Fixed: exclusive creation, fsync, read-back; the file this export made is removed on any failure | `export.publish` |
| H7 unbounded waits, export on UI thread | Fixed: bounded join and kill after a result; exports built in a worker and published by the window; Cancel (Esc) | `worker.Job`, `app.export_to` |
| H8 partial OCR failure hidden | Open: needs ClassiFile's reader to record it, then a tagged sync (`READER.md`) | upstream |

**Built for M3 and the accepted proposals:** readable-text Copy and Export (PDF, Word) from the Source pane, with
OCR, notes, labels and gaps kept; Cancel; find in the source (Ctrl+F, Enter / Shift+Enter); text zoom
(Ctrl+= / Ctrl+- / Ctrl+0, the reading column scales with it); a summary line's link selects that occurrence in
its own page, slide or paragraph, with Back to summary; offline Help/About (privacy, OCR availability, keys,
licences). UX3: green removed; `notice` and the application heading size match ClassiFile; document headings have
their own tokens; a test compares the shared values with a table copied from ClassiFile 1.0.0-rc.7 (commit
`454e720`, no tag yet: retake it at ClassiFile's v1 tag).

**Verified on 2026-10-20:**
- `python -m pytest -q`: 114 passed (commit `87a40de`).
- Screenshots at 125% (`python -m tools.screenshots --scale 1.25`, 1536x864 and the earlier sizes), both themes:
  line selection with Back to summary, find, zoom, Cancel while working, an empty summary that says why.
- `python -m tools.evaluate` (OCR on), development set: commit `87a40de`, 84 files, 84 unique documents
  (docx 5, odt 7, PDF prose 3, PDF slides 61, pptx 8), 84 checked, 0 left out, 0 problems, no empty summaries, exit code 0; report `data\reports\evaluation-20261020-155054.txt`
  (not tracked). Every method passes every check on every document of its format; the small format groups give
  wide ranges (3 PDF prose documents: 44%-100%). These are automatic checks on the development documents, not
  quality or accuracy results; the rubric comparison waits for the reference key points. An earlier run on
  `91912b7` found 4 problems in one document (D30): a bug in the new whole-line check (overlapping matches), fixed
  in `87a40de`.

**Not verified:** a live keyboard and screen-reader pass on Windows, 150% scaling of the new controls, Reduce
motion, and the exports opened in Word and a PDF reader by the owner. No held-out file was read.

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

## Built: UI redesign and M2 (2026-10-15), waiting at its stop point

**Interface**
- A compact header (the app, the document's name shortened with "…", Open document…, Paste text) and a workspace
  of two resizable panes, Source and Summary (Summary a little wider), each with one scroll area. Below 960 px the
  panes become tabs. Text lines stop at about 80 characters while the panes fill the window. 24/16/8 px spacing;
  violet only on Summarize, focus outlines, the current tab and links.
- The Summary pane: Copy and Export… on its caption row; the Detail level control, Summarize, the level's one-line
  explanation and a notice line. States: empty, working (the last summary stays), done, and error (the last summary
  stays). Changing the level never starts work or clears the summary; a summary of another level is said.
- Every summary line links to its page, slide or section; a click scrolls the Source pane there (and opens the
  Source tab when narrow).
- Reduce motion: the app has no animations of its own; when Windows' animation effects are off, Qt's animated
  menus, combo boxes and tooltips are switched off too.
- Screenshots: `python -m tools.screenshots` (invented documents; 100%, 125%, 150%; light and dark; wide and
  narrow; every summary state; keyboard focus), saved in `data\screenshots` (not tracked).

**Reading quality**
- PDF headings: only a short run of lines (12 words or fewer) at the start of a block, clearly larger than the
  page's body text (1.2 times) or bold where the body is not, and not ending like a sentence. The reader keeps
  sizes but not weights, so the worker reads the font weights from the same bytes (checked by hash).
- What couldn't be read: one short note per page at most, one line at the top, details behind "Show details".
  Dropped OCR noise is no longer mentioned.

**Summaries** (`summarease/summarize.py`, record C12, C13)
- Four levels built by one rule set from any method's ranking: Detailed first (each section's heading and up to
  3 lines), Key points and Brief chosen from it, Comprehensive adding to it, so the levels nest. The intended
  budgets are C12's; H1/H3 record why current construction/checks do not establish that promise on all inputs.
  Speaker notes and hidden slides appear only at Comprehensive; OCR never stands alone at Brief when there is native
  text; headers, footers and template lines are left out.
- Three methods: the opening-lines baseline; structure first for slides (PPTX, and PDFs that are mostly landscape
  with few words a page); sentence ranking with near-duplicates removed for prose. The app uses structure for slides
  (C12) and the baseline for prose until a method beats it on the rubric (MILESTONES.md).
- Copy and Export (PDF and Word) use the summary and its references, with OCR and notes marked. An export is
  read back before publication and uses no-overwrite creation; H6 documents incomplete-file cleanup on failure,
  and H3 calls for checking all presentation markers and labels.
- `python -m tools.evaluate`: initial automatic checks, with neutral IDs and per-format reporting in local
  work. The earlier development run has no available report; H3–H5 must be resolved before treating a successful
  exit as acceptance.
- **Tests (84) at that time;** the audit fixes on 2026-10-20 bring the suite to 114 (above).

## Done: M1 Read files and show the readable text view (2026-10-15)

- **The window** (`summarease/app.py`): open a document with the button, Ctrl+O or drag-and-drop, or paste text
  with the button or Ctrl+V. The text is shown in one reading column; the status line says what was read.
- **The readable text** (`summarease/readable.py`): the reader's words, laid out only. PDF: headings from the
  reader's font sizes (a short block clearly larger than the body text), paragraphs from its blocks, list items
  where a line starts with a list mark. PPTX: each slide's title as a heading, each shape's lines kept. DOCX and
  ODT: the reader's titles, headings, paragraphs, lists, tables and footnotes. Page and slide labels, captions and
  gap notes are SummarEase's own blocks, kept apart from the document's words. If a page's layout ever disagreed
  with its text, the text itself is shown.
- **OCR text** is shown in a shaded block under the caption "Text read by OCR from a picture. It may contain
  errors." **Gaps** are said where they are (OCR found no text, a picture couldn't be opened, OCR failed, not
  installed, out of time, switched off, or noise left out) and summed up at the top.
- **The worker** (`summarease/worker.py`): each file is read in its own process with a 5-minute limit; a timeout or
  a crash is reported plainly and nothing is shown for it. The window polls it and is updated in place.
- **Themes:** light and dark from one tokens file (`summarease/tokens.py`, ClassiFile's structure, violet), the
  style sheet and the Qt palette rebuilt when Windows' setting changes, keeping the scroll position.
- **Tests (35):** the words shown equal the reader's words, in order, for a PDF, a PPTX, a DOCX and an ODT made for
  the tests, and the rendered view adds or drops nothing; the original's hash is unchanged and nothing is written
  next to it; pasted text leaves no file anywhere and is not logged; no document text or file name is logged; every
  OCR gap is disclosed; a hung or crashed worker is reported; every colour pair in both themes is readable.
- **A read-only check on ClassiFile's development files** (78 documents: 58 PDF, 8 PPTX, 5 DOCX, 7 ODT; not part
  of the test suite), run with OCR off and again with OCR on: all 78 read both times; on every one, the view's
  words equal the reader's words and the rendered text equals the view. 35 of 1,148 PDF pages fell back to their
  plain text. With OCR on, 62 of the 78 show at least one gap note (this counts notes about OCR noise left out);
  the slowest document took 32 s.

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

## Open acceptance work

- **The owner's reference key points** for the 10 documents in `data\reference\` (set up 2026-10-15), written
  before any method is tuned. Then the rubric comparison of the baseline and ranking for prose; the app switches
  to ranking only if it wins.
- **SummarEase's held-out set** (`data\final-check`): copies of ClassiFile's `data\validation` and
  `data\final-eval`, taken under the owner's post-CP5 plan (`EVALUATION.md`). Routine development and this audit
  do not open them; any final check needs the owner's gate, a frozen version and the planned run ledger.
- **Record update by the owner:** Q1–Q3 as answered on 2026-10-20 (above).
- **H8:** partial OCR failures need an upstream reader fix; the accepted bullet-level deferral is separate.
- **The owner's review (M3 stop point):** the levels, the exports opened in common readers, keyboard focus and
  scaling in the live app.

## v1.1 list

- **Keep bullet levels in the reader**, so PowerPoint sub-bullets can wait for Comprehensive (record C12). It starts
  in ClassiFile's reader after ClassiFile v1 and is copied back at a new tag (READER.md). Until then, every slide
  line is treated as a top-level bullet.
- **Proposed, not confirmed:** original-page previews (UX6) and installer adaptation (UX5). Search, source
  highlighting/return, text zoom, Cancel, shared-token checks and Help/About were built on 2026-10-20 at the owner's
  request.

## Decided, 2026-10-15 (record 0.3; level names in 0.4; Comprehensive's budget in 0.5)

- **Export (C14, was P6):** the summary and the readable text, as PDF or Word; the Word file built with the
  standard library. A searchable copy of a scanned document is allowed later, as a new file made on request, but
  not in v1.
- **Length budgets (C12):** the table is accepted as starting defaults, tuned in M2 with the rubric.
- **Order:** M1 to M3 implementation need not wait for ClassiFile v1; evaluation uses SummarEase's development
  copies and independent references. Only M4 waits for ClassiFile v1, and milestone go-aheads still apply.
- **Held-out set:** ClassiFile's validation and final-eval files, copied after its CP5 (above).

## Background: the Export options (decided as d, "a and b")

This is historical decision background, not an open choice. C14 confirms new PDF/Word exports of both the
summary and the readable text. Both are implemented (readable text on 2026-10-20).

| Option | What the user gets | Notes |
|---|---|---|
| a. The summary | the level on screen, each line with its page, slide or section | small; the links make it checkable |
| b. The readable text | the whole document as readable text (C5) | the words are the reader's, in order |
| c. A searchable copy of a scanned document | the scanned pages with their OCR text laid under them | a different feature: it writes OCR text into a copy of the document |
| d. Several of these | a and b; c later if wanted | |

**Accepted: d, as "a and b".** Export the summary at its shown level, or the readable text, each as a new PDF
with real text or a Word file. A searchable scan copy is allowed as a possible later feature under C14, outside v1:
- it is a separate feature with its own risks (OCR text placed under the wrong words, a copy that looks like the
  original but is not);
- it must be a new file made on request; neither the original nor a ClassiFile-managed copy may be modified.

**Confirmed implementation choice:** Word uses standard-library ZIP/XML; PDF uses the already installed
PyMuPDF (C14). The writers read their output back; H6's failure cases are covered by tests. The earlier
alternative dependency proposal is not a new dependency request.

## Next milestone

The owner's review of M3 (levels and exports) and the record update for Q1–Q3. M2's rubric comparison waits for the
owner's reference key points. Only on the owner's go-ahead. Integration remains documentation-only until
ClassiFile v1 and M4 authorization.

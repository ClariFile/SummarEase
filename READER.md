# The reader question

SummarEase needs what ClassiFile's reader (`classifile/reader`) already does:
- native text from PDF, PPTX, DOCX and ODT;
- selective OCR, with junk lines dropped and counted;
- source locations (page, slide, block);
- layout (lines, blocks, positions, sizes), which ClassiFile keeps for SummarEase;
- a versioned record (record version 7 since `reader-v7`).

The reader is about 1,300 lines. It needs PyMuPDF, plus Tesseract for OCR. It imports nothing from the rest of
ClassiFile, by rule and by test.

## (a) Copy it into SummarEase, with a version tag and a sync rule

- Copy the package from a tagged ClassiFile commit into `summarease/reader/`.
- Note the source commit and the record version in `summarease/reader/SOURCE.md`.
- Sync rule: ClassiFile's reader is the source. A fix found in SummarEase goes to ClassiFile first, then is
  copied back. Copies are taken only at a tag.
- For: no packaging work; each app ships and tests on its own; SummarEase can start at once.
- Against: two copies can drift, and every fix has to be copied by hand.

## (b) A small shared package used by both

- A package (for example `clarifile-reader`) in its own repository, installed by both apps at a pinned version.
- For: one copy of the code, fixed once.
- Against:
  - a third repository to version and release;
  - ClassiFile's code and installer would change, right before its v1;
  - every reader change needs a release before either app can use it.

## Taken in M0: (a)

The copy is ClassiFile's tag `reader-v7` (first `reader-v6`); `summarease/reader/SOURCE.md` lists the hash of each file.
`tests/test_reader_copy.py` checks the files and hashes. It was completed early in M0 on 2026-10-15 at the
owner's request, rather than remaining M1's first task.

## Known limits and their owners (reviewed 2026-10-20)

- **PowerPoint bullet levels:** not retained in this copy. The owner accepted the limitation for now and added
  preservation of bullet levels to v1.1. It starts in ClassiFile's reader after ClassiFile v1, then comes back at
  a tag. Do not claim lower levels already distinguish sub-bullets.
- **Partial OCR failure (H8): fixed upstream at `reader-v7` (2026-10-26).** The record keeps each picture's
  outcome (`ocr_pictures`) and a `partial` status; `unread_gap()` is the reader's own answer. The view names the
  unread pictures and `checks.gaps_disclosed` tests against the reader's outcomes, not the view's notes. Records
  older than version 7 have no per-picture outcomes; their status alone decides.
- **Unsupported reader content:** chart text in PPTX is not read (`reader/ooxml.py`); equation structure is
  flattened to text. These are extraction limits, not evidence that the source has no information.
- **Summary exclusions are different:** the reader does extract table text, but SummarEase's summarizer skips
  table blocks (H2). Correct the summarizer's outcome/disclosure locally; do not describe this as an OCR failure
  or change the copied reader to work around it.
- **PDF bold flags:** the worker supplements the record by reading font weights from bytes checked against the
  reader's hash. Keep source identity checks when changing this path.

The findings and acceptance cases are in [the handoff](docs/FROM_CLASSIFILE.md). Fixes to reader behavior start
upstream; no local edit to the six pinned files, silent hash-table replacement, or import from ClassiFile's
working tree. A sync records the tag, commit, record/format versions and hashes, then runs the copy and regression
tests in both apps. Proposed original-page previews are not part of this reader sync.

## Recommendation: (a), for now

ClassiFile is frozen for v1 apart from launch work and bug fixes, so its code should not change for this. A tagged
copy lets SummarEase start at once. Move to (b) once both apps are released, if the copies have needed the same
fix more than once. ClassiFile's code is not changed for this now.

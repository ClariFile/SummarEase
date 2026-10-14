# The reader question

SummarEase needs what ClassiFile's reader (`classifile/reader`) already does:
- native text from PDF, PPTX, DOCX and ODT;
- selective OCR, with junk lines dropped and counted;
- source locations (page, slide, block);
- layout (lines, blocks, positions, sizes), which ClassiFile keeps for SummarEase;
- a versioned record (record version 6).

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

## Recommendation: (a), for now

ClassiFile is frozen for v1 apart from launch work and bug fixes, so its code should not change for this. A tagged
copy lets SummarEase start at once. Move to (b) once both apps are released, if the copies have needed the same
fix more than once. ClassiFile's code is not changed for this now.

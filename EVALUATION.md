# Evaluation

How SummarEase's summaries are measured. Document-check counts and quality results come from one evaluation
command with recorded inputs and versions. Unit-test counts, synthetic diagnostic cases and UI timings are
labelled separately. The counts describe the owner's development documents; they are not accuracy estimates,
and a score is never a probability.

**Implementation status, 2026-10-20:** the command implements automatic checks only. The review found weaknesses
in those checks and their execution (H1–H5/H8 in [the handoff](docs/FROM_CLASSIFILE.md)). Treat the checks below as
acceptance requirements, not guarantees already established by a successful command. The earlier development
run has no available saved report; no complete result is claimed.

## The documents

- **Development set:** copies of ClassiFile's development files (its `data\development`, `data\real-samples` and
  the six sample PDFs), placed in SummarEase's own `data\development`. The originals are never opened for
  writing; only the copies are read.
- **Never read ClassiFile's `data\validation` or `data\final-eval`** until ClassiFile's CP5 is done. They are
  ClassiFile's held-out sets, and reading them would turn them into development data.
- **SummarEase's own held-out set** (`data\final-check`): after ClassiFile's CP5 is done, copies of ClassiFile's
  `data\validation` and `data\final-eval` files become SummarEase's held-out set. SummarEase has never seen them,
  so they are held out for it too. Until then they are not read or copied. Once in place, the set is used once per
  frozen version, for a final check, as in ClassiFile. Refusal outside that gate is required; current path
  protection is incomplete (H4), and the final-run mechanism is not implemented.
- Documents are named in reports by neutral IDs (D1, D2, …), with a local, untracked map. No document text,
  title or name goes into tracked files.
- A reported CP5 completion is not permission to inspect held-out content in this audit or routine development.
  Follow the owner's gate and `AGENTS.md`. Before any future evaluation opens or hashes a file, validate its
  resolved location, protected descendants and aliases; reject parent-folder requests that include protected
  data. Test refusal with invented folders, never by probing the actual held-out sets.

## The owner's references

For 10 development documents (slides, PDFs, Word and ODT, one long and one short), the owner writes the **reference
key points**: the 5 to 8 points a reader must come away with. They are kept in `data\reference\` (not tracked), one
text file per document named by its neutral ID: the point in the owner's words, and the page, slide or section it
comes from. They are written before any method is tuned and are not changed to suit a method, and the owner sees
no SummarEase summary of these documents before writing them.

The ten existing templates and their private document-name mapping are preserved. Do not recreate, overwrite
or prefill them. An optional reference-entry aid may attach a source location to a point written by the owner;
it must not recommend points, display summaries, or replace the references with selected source line IDs.
Literal overlap is not a score for coverage, faithfulness or readability.

## The rubric (the owner scores)

Each summary, at each level being tested, is scored by the owner on four points, each 0, 1 or 2:

| Point | 0 | 1 | 2 |
|---|---|---|---|
| **Covers the main points** | misses most reference points | covers some | covers all, or all the level has room for |
| **Faithful** | a line misleads out of context | a line needs its context | every line reads true on its own |
| **Readable** | hard to follow | followable with effort | reads cleanly in order |
| **No repeats** | several lines say the same | one repeat | none |

- Scoring is blind: the owner sees the summaries without the method's name, in a shuffled order.
- A method is kept only if its total beats the baseline (opening lines) for the documents it is meant for
  (`MILESTONES.md`, M2). A tie keeps the baseline.
- The current prose default is the opening-lines baseline. Once references are complete, freeze them and the
  tested method versions, prepare anonymized baseline/ranking pairs in a reproducible shuffled order, and let
  the owner score the rubric. Publish paired denominators, exclusions and totals by document kind and level;
  switch prose to ranking only if it wins. Automatic checks alone cannot authorize the switch.

## Automatic checks (a test each, on every development document and level)

1. **Traceable:** every line equals a complete sentence, bullet or line of the document, word for word, and its
   page, slide or section link points to that occurrence. Substring membership alone is insufficient (H3).
2. **Gaps disclosed:** every gap the reader reported (unread pictures, failed OCR, unreadable pages) is said in
   the summary. Compare against reader outcomes as well as view blocks, so a lost disclosure in the view does
   not pass by agreement. The pinned reader still cannot represent every partial image failure (H8).
3. **Same input, same output:** fresh reads and repeated builds give identical user-visible output, references,
   OCR/notes/hidden-slide markers and disclosures, including Copy/Export text. Compare semantic content, not
   incidental PDF/ZIP metadata.
4. **Renaming changes nothing:** the same bytes under another file name give that same output and source links.
5. **Levels nest and keep their budgets** (record C12): calculate permitted limits from W independently of the
   result's `budget` field. Comprehensive's limit is at least Detailed's budget, not whatever length a faulty
   Detailed result happens to have. The section-coverage conflict is awaiting the owner's decision (Q1).
6. **Empty outcomes are explicit:** distinguish no readable text, readable material excluded by the method,
   and no whole eligible line fitting the budget. Report counts by format/level; an empty result is not evidence
   that useful summarization passed (H2).

## One command

**Available now:** `python -m tools.evaluate` runs the baseline and the relevant alternative (structure for slides,
ranking for prose) at all four levels. It reports automatic document pass counts per format, with PDF slides and
prose separated, and descriptive ranges. `--set` selects development folders; `--no-ocr` requests OCR off.
It does not write blind-scoring summaries, consume references, or support `--final`.

**Required corrections before trusting the gate (H3–H5):**

- Check input locations before opening or hashing. A missing/empty input set is an explicit unsuccessful outcome,
  not a successful zero-document report.
- Bound each read and build in a worker. Report crashes/timeouts separately from check failures; use neutral
  IDs for progress and redact native-library errors as well as Python exceptions.
- Return a nonzero exit code for failed checks or an incomplete run. Record counts found, checked, failed and
  excluded, with fixed reasons and denominators per format/method. Say whether counts are files or unique byte
  hashes, and expose duplicates rather than counting repeated copies as independent evidence.
- Save a local report with the invocation (private paths omitted), code revision and dirty state, reader and
  dependency versions, effective OCR availability/settings, set fingerprint, counts and completion status.
  Keep private mappings in `data/`. An interrupted report must not look complete.

**Later, after references and owner authorization:** add blind rubric scoring to this command. Any shuffle uses
a fixed seed; show rubric totals separately from automatic checks. The planned `--final` must identify a frozen
version and set fingerprint, persist a run ledger and refuse a second completed run for that frozen version.
Its implementation and crash/retry policy need review before the first held-out run; it is not available now.

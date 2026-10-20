# Notes from ClassiFile for SummarEase's next session

Originally written 2026-10-20 during ClassiFile's look-and-feel patch. Reviewed and extended on 2026-10-20 against
SummarEase's existing M0–M2 implementation. This is a documentation handoff, not authorization to rebuild the app,
change a requirement, start another milestone, or edit the copied reader.

[DECISION_RECORD.md](../DECISION_RECORD.md) remains authoritative. Section 1 records owner direction reported by
the original handoff; the audit distinguishes verified behavior from proposed corrections. New design ideas are
proposals until the owner confirms them. Read with [STATUS.md](STATUS.md) for current implementation and verification
state, including work left uncommitted by the previous session. Section 9 adds what changed in ClassiFile later that day
(rc.6 and rc.7).

## 1. Decided by the owner on 2026-10-20 (for both apps)

- **Few colours, chosen to sit together.** At most 4 or 5 colours across the suite, all blending with the accents.
  ClassiFile now uses neutral greys plus teal (its accent), amber (waiting, warnings) and red (failures only);
  violet is reserved in ClassiFile for anything that opens SummarEase. Green, the colour per file format and the
  colour per category were removed. Green sat too close to teal and read as a second accent.
- **Each app's accent is its own icon's colour.** SummarEase: icon and accent are both `#6C47FF` (record C11), already
  right. ClassiFile: icon teal `#0D9488`, accent `#0F766E` (its darker shade, for a white label at 4.5:1). The
  ClariFile icon carries both.
- **Close in colour and layout:** the two apps should look like one suite. The intended shared foundation is greys,
  amber, red, font, spacing steps (24/16/8/4), radii (6/8), control height and role names, with each app's accent.
  This is the target, not a claim that the current values all match; see section 2.
- **Spacing only where it is needed, and the same everywhere:** no cramped spots next to empty bands. In ClassiFile
  this meant: every card's number, icon and text start at the same x; every dropdown on a settings page has one
  width so the edges line up; one style for column names; a reminder about other work is a quiet line, not a
  filled panel, on pages that are about something else.

## 2. What to change in SummarEase to match (small)

1. `summarease/tokens.py`: propose dropping the unused `green` roles from both themes and updating
   `tests/test_theme.py`. The suite uses neutral shades plus the accent family, amber and red. "4 or 5 colours"
   means colour families, not a ban on shades needed for contrast, dark mode and focus states.
2. Write in the tokens' header that violet is the SummarEase icon's colour, and that greys, amber and red are the
   suite's, kept equal to ClassiFile's (`classifile/app/tokens.py`).
3. A **suite colour check**, like the reader check: a test that compares the shared values (greys, amber, red,
   font, spacing, radii) with a table copied from ClassiFile at a tag, so the two apps cannot drift apart unseen.
4. Actual differences checked on 2026-10-20: `notice` is `#EEF1F4` / `#2A2D32` in SummarEase's light/dark themes,
   versus `#E8EDF2` / `#272A2F` in ClassiFile. `TEXT_HEADING` is 18 versus 16. Propose matching shared application
   roles at a pinned ClassiFile tag, while keeping document typography separately named; do not reduce every
   document heading merely to match an application label.
5. **Keep `READING_CHARS = 80`.** The owner explicitly requested about 70–90 characters for SummarEase's reading
   panes. ClassiFile's full-width card rule does not replace that instruction. Panes fill the workspace; text
   wraps within them. A later change to this behavior needs the owner's decision.

## 3. Sharpness at 125% and 150% (the owner's laptop runs at 125%)

ClassiFile's icons and page previews were blurry because they were drawn at 100% and stretched by Windows. Fixes
that SummarEase can reuse when the corresponding feature is built:
- **Icons drawn in code:** a `QIconEngine` subclass that paints on a 16-unit square at whatever size and scale it
  is asked for (`_Painted` in ClassiFile's `classifile/app/widgets.py`), instead of a fixed 16 px `QPixmap`.
- **Page pictures:** render at `width * widget.devicePixelRatioF()` pixels and call `setDevicePixelRatio()` on the
  pixmap; compare sizes with `deviceIndependentSize()`.
- **Speed:** pass page pictures to Qt as PPM (`pixmap.tobytes("ppm")`), not PNG: no compression on the way in.
- Take screenshots at 125% by default (`QT_SCALE_FACTOR=1.25`), since that is what the owner sees.

## 4. Ideas to move faster

1. **Optional reference-entry aid.** The ten private files in `data\reference\` already exist. Keep them and the
   owner's 5–8 key points in their own words. An aid based on ClassiFile's `tools/label_window.py` could show source
   text and capture a location alongside a typed point, without displaying summaries or recommending points.
   Source line IDs are optional locators, never replacements for the independent references. Overlap is not a
   rubric score. This aid is not required to finish the references.
2. **Adapt ClassiFile's installer pattern.** Its `installer/` has a PyInstaller spec, per-user Inno Setup script,
   English OCR data, licences, portable testing and a counts-only `--self-test`. SummarEase needs its own stable
   AppId, executable, install/data paths, shortcuts and registration ownership; copying the existing AppId could
   update or uninstall the wrong app. Build dependencies still need approval. Test installation, upgrade,
   coexistence and uninstall on disposable Windows, never the owner's laptop. See proposal UX5 below.
3. **Prepare M4 documentation only.** Clarify the draft in [INTEGRATION.md](../INTEGRATION.md). Building or testing
   registration, a caller or a receiver still waits for ClassiFile v1 and the owner's M4 go-ahead. ClassiFile's
   reserved violet button is visual preparation, not evidence that integration is available.
4. **A timing tool**, like ClassiFile's `tools/measure_ui.py`: open, summarize at each level, switch levels, export,
   on made-up documents, with times per step. It turns "feels slow" into a number before and after a change.
5. **Check every page at 1536x864 and 125%** before reporting (ClassiFile's habit): look at the right edge of every
   panel, at alignment down the page, and at spacing between groups.
6. **Keep one evaluation command for document checks and quality results.** Any proposed UI timing tool reports
   performance on invented documents separately, with its command and environment; it must not become a second
   source of quality counts. Test counts and screenshots likewise describe their own checks.

## 5. Lessons from ClassiFile worth keeping

- One tokens file, two complete themes, the style sheet and the Qt palette built from it: already done in
  SummarEase; keep it so.
- Link colour is the accent everywhere (ClassiFile had black links in one place and teal in another).
- Errors are the only red, and an error never looks like normal state.
- A draft must survive a refresh: text typed, an open panel and the cursor (ClassiFile measures this in
  `tools/measure_ui.py`).

## 6. Findings register — 2026-10-20

Scope: the current single-user Windows app, evaluation/export paths and handoffs. All **84 existing tests passed**
with `python -m pytest -q` (a fresh temporary base directory was used). The cases below are synthetic diagnostics,
not development-set quality measurements. No private source text or held-out documents were used.

**P1** means a release blocker or a prerequisite to trusting evaluation. **P2** means a verification or usability
gap to resolve before acceptance. "Proposed correction" and the acceptance cases describe future work; no code is
fixed by this handoff. H1 and Q1 need a requirement decision before a complete correction is possible.

### H1 — P1: headings can exceed Detailed's budget

- **Evidence (reproduced):** in [summarize.py](../summarease/summarize.py), `build()` inserts all eligible section
  headings before allocating the remaining budget. Forty invented seven-word headings, each followed by
  "Short factual sentence.", give W=400 and Detailed=280 words against a 150-word budget. Comprehensive also
  allows `_words(detailed)` to increase its limit, beyond the confirmed floor rule.
- **Consequence:** the result breaks C12's budget promise; silently enlarging Comprehensive can conceal the cause.
- **Proposed correction:** count headings within an independently calculated limit. Ask the owner to resolve
  mandatory section coverage versus the limit (Q1); recommend strict budgets with omitted sections disclosed.
- **Acceptance:** many headings, long headings and hidden-slide headings cannot silently exceed either budget.
  Verify the owner-approved coverage behavior, nesting, and the Comprehensive floor separately.

### H2 — P2: readable documents can yield an unexplained empty summary

- **Evidence (reproduced):** `sections_of()` skips tables. A table containing "Invented fact" and "Meaningful value"
  gives four readable words and no Detailed lines. A single 200-word sentence also gives no Brief lines.
  `checks.traceable()` and `checks.within_budget()` accept empty results.
- **Consequence:** the user cannot distinguish extraction failure, unsupported summary material and a budget
  that cannot fit one whole sentence.
- **Proposed correction:** give these distinct outcomes with a Source link. Use "No extractable lines fit this
  level" when appropriate; never truncate a sentence or claim that readable table text was unread.
- **Acceptance:** table-only, empty, OCR-only and long-sentence documents get an accurate outcome. An empty result
  must be explicitly counted in evaluation, rather than treated as evidence of useful summarization.

### H3 — P1: the automatic checks accept weaker guarantees than their names promise

- **Evidence (reproduced):** [checks.py](../summarease/checks.py) accepts "publish this." as a substring of
  "Do not publish this." It accepts a 100-word Brief with W=100 if the result supplies `budget=999`. Changing
  `Summary.labels` changes copied references while `same()` still returns true.
- **Consequence:** a passing report does not prove intact source lines, C12 budgets or identical visible output.
- **Proposed correction:** verify complete sentence/bullet/line boundaries and locations against the source;
  derive permitted budgets independently of the result; compare visible reference labels, OCR/hidden/notes
  markers, disclosures and Copy/Export content. Mechanical traceability still does not establish faithfulness.
- **Acceptance:** deliberate mutations of a negation, boundary, location, budget, label and marker must fail the
  relevant check. Run the same-input check across fresh reads as well as repeated builds of one extraction.

### H4 — P1: selecting a parent folder bypasses held-out protection

- **Evidence (reproduced with invented files):** [evaluate.py](../tools/evaluate.py), `main()`, checks only the
  supplied root. Selecting its parent enumerates a nested `validation/invented.pdf` and hashes it.
- **Consequence:** development evaluation can read protected data before any refusal.
- **Proposed correction:** validate candidate locations before opening or hashing, including resolved aliases
  and protected descendants. Prune protected directories and reject a request that would include them.
- **Acceptance:** protected roots, parent roots, mixed-case names and supported symlink/junction aliases are
  refused before a sentinel file can be opened. Use invented files only, never the actual held-out sets.

### H5 — P1: evaluation failure does not fail the command, and work is unbounded

- **Evidence:** a synthetic failing result still makes `main()` return 0 (reproduced). Inspection shows direct
  `analyse()` calls without a worker deadline. Missing/empty roots can produce a successful zero-document report.
- **Consequence:** automation can treat failure as success; a hung read prevents the final report.
- **Proposed correction:** nonzero failure exits, explicit invalid/empty-set outcomes, per-file worker deadlines,
  progress using neutral IDs, and separate counts for checked, failed and excluded documents.
  Save the command, code/reader versions, effective OCR availability, set fingerprint and completed/partial state.
- **Acceptance:** failing checks, unreadable files, timeouts, crashes and no input are distinguishable from success.
  The report retains denominators and contains no private paths/text. Duplicate bytes are counted explicitly.

### H6 — P1: failed exports can leave a partial final file

- **Evidence (reproduced):** [export.py](../summarease/export.py), `save()`, falls back to exclusive creation when
  hard links fail. Injecting a disk-full error after 16 bytes leaves a 16-byte file at the final destination.
  The `finally` block cleans the temporary file only.
- **Consequence:** an unusable file looks like a completed export and occupies the requested name.
- **Proposed correction:** publish only verified complete output; on failure, clean up only files created by
  that export. Preserve the no-overwrite behavior under races. If a filesystem cannot publish safely, report
  that limitation instead of leaving an apparently complete result.
- **Acceptance:** existing-name collisions, a competing writer, unsupported hard links, write/close failures,
  read-back failure and disk-full leave existing files byte-identical and no incomplete final output.

### H7 — P1: deadlines do not cover all worker cleanup or export work

- **Evidence (inspection):** [worker.py](../summarease/worker.py), `Job.poll()`, receives synchronously and then
  calls `_finish()`, whose `join()` has no timeout. A worker that sends a result and stays alive can block the UI.
  [app.py](../summarease/app.py), `export_to()`, performs rendering, checking and saving on the UI thread.
- **Consequence:** the window can stop responding despite the documented time limits.
- **Proposed correction:** bounded result receipt and cleanup, cancellation that reaps the worker, and background
  export coordinated with H6. Keep the last completed result usable and reject stale results after source changes.
- **Acceptance:** a send-then-hang worker, interrupted result transfer, cancellation, window close and slow export
  leave the UI responsive. Wait on conditions with a generous watchdog; do not rely on fixed sleeps.

### H8 — P1: successful OCR on one image can hide a failure on another

- **Evidence (inspection):** [reader/ocr.py](../summarease/reader/ocr.py), `run()`, sets the unit status to `done`
  whenever any usable OCR text exists, even when another image failed. [readable.py](../summarease/readable.py)
  adds gap notices only for failure statuses; the resulting summary can omit that partial gap.
- **Consequence:** C8's disclosure is incomplete. Agreement between view and summary does not catch a lost reader
  failure, because both use the same incomplete status.
- **Proposed correction:** retain partial failures upstream in ClassiFile's reader, sync only at a tag, then
  consume them in SummarEase. Keep one short note per page and details behind the disclosure; do not revive
  dropped-noise notices. Document the limitation until the reader contract can represent it.
- **Acceptance:** a page with one successful image and one failed/unopenable image retains the usable text and
  reports the partial gap in Source, Summary, Copy and Export. The pinned reader test still passes after an
  explicitly recorded upstream sync.

## 7. Requirement questions for the owner

These are proposals for a future record update, not edits to the authoritative record.

- **Q1 — section coverage versus budgets (H1):** C12 requires every readable section in Detailed and a strict
  budget, but the headings alone can exceed it. Recommend keeping the budget and disclosing omitted sections
  with Source links. The alternative is an explicit coverage exception; the current code's implicit increase
  is not an approved exception.
- **Q2 — short documents:** C12 says Comprehensive is "never a copy" but permits a document shorter than a
  level's floor to appear whole. A four-word invented sentence currently appears whole in Comprehensive.
  Recommend making the short-document exception explicit in the wording and UI, rather than dropping useful
  text just to make the output shorter. The owner decides the wording; no new rule is assumed here.
- **Q3 — export location:** C6 permits a user-chosen destination; agent rules prohibit creating files beside
  originals. Recommend an explicit exception only for a user-requested new export, never incidental files or
  changes to originals. Until decided, the handoffs must not imply such an exception is already authorized.

## 8. Prioritized design and feature proposals

Use the existing Python/PySide6/PyMuPDF stack and tokens; no new runtime dependencies. These ideas are not
requirements merely because they appear here. Target milestones below are proposals, not permission to start.

| ID / priority | Proposal and benefit | Target and constraint | Acceptance before calling it complete |
|---|---|---|---|
| UX1 / v1 candidate | Source search, exact source highlighting, a return-to-summary action and text zoom make long documents easier to inspect. Visible Cancel makes waiting controllable. | M3 review, after H7; preserve 70–90-character reading width, source words, keyboard focus and the last result. Highlight exact locations, not the first matching duplicate. | Search/zoom work in panes and tabs in both themes; a repeated sentence links to the right occurrence; return restores position; Cancel is keyboard accessible and blocks late results. |
| UX2 / correctness first | Distinguish unread content, readable material excluded by the method and lines that do not fit. Link each outcome to Source. | M2 corrections H1/H2/H8; one short page note plus details, not a stream of OCR-noise notices. | Synthetic cases show the right reason and location; an empty summary is never reported as a useful completed summary; Copy/Export preserve the disclosures. |
| UX3 / v1 candidate | Pin shared suite tokens; separate application typography from document typography; use restrained colours and visible focus. | M3 visual review; remove unused green, resolve notice colours, keep accessible accent shades. Snapshot at a tag, with no runtime import from ClassiFile. | Shared-role comparison and contrast tests pass; active-window keyboard review covers wide/narrow layouts, long names, 125%/150% scaling and Reduce motion. Record logical size and scale separately. |
| UX4 / finish promises, then optional help | Readable-text Copy/Export and a clear Summary/Source choice finish C5/C6/C14. Local Help/About explains privacy, OCR availability, licences and shortcuts. | Readable-text export is remaining M3 work; selection controls and Help/About are proposals. Reuse existing writers; never auto-save pasted text or open network resources. | The selected content and shown summary level are unambiguous; PDF/Word text round-trips and opens in common readers; original hashes stay unchanged; Help works offline. |
| UX5 / release candidate | Adapt ClassiFile's packaging pattern to ship a standalone app with English OCR and a counts-only self-test. | Release planning after core acceptance; own stable AppId, paths and registration ownership; build dependencies need approval. Registration implementation remains M4-gated. | On disposable Windows, install, upgrade and uninstall preserve documents and both apps coexist; each works alone; a foreign registration is never removed; licences ship. No test install on the owner's laptop. |
| UX6 / later | Keep PowerPoint bullet hierarchy; optional original-page previews help check extraction against appearance. | Bullet levels are already accepted for v1.1, starting in ClassiFile after v1. Previews are a separate proposal, not a searchable scan-copy feature. | Tagged reader sync retains hierarchy; higher-detail bullet inclusion is tested. If previews are approved, render read-only at device scale with bounded memory and correct source links. |

The optional reference aid in section 4 supports M2 but never changes its scoring gate. A proposed timing tool
uses invented documents and reports repeatable performance only. Neither justifies tuning before independent
references exist.

**Review limits:** the full development evaluation was not rerun; its earlier temporary report was unavailable.
Live Windows focus/scaling, installer execution and held-out data were not checked. The green existing suite
does not close H1–H8. Runtime/API/data-format changes remain a later, separately authorized implementation step.

## 9. ClassiFile rc.6 and rc.7 (later on 2026-10-20)

ClassiFile went from rc.5 to rc.7 the same day: a polish pass the owner asked for, then fixes from an outside
review of ClassiFile that the owner had worked through. Nothing in SummarEase changed. Items marked "owner" were
the owner's requests for ClassiFile; everything else is a proposal for SummarEase, like the rest of this file.

### Look (ClassiFile, at the owner's request)

- **Still few colours (owner).** Nothing was added: greys, the accent, amber, red. "More colours mean less
  professional" (the owner's words). This confirms section 1.
- **Sidebar (owner).** The categories sit in their own quiet panel, a step lighter than the sidebar with a hairline
  edge and rounded corners, with no empty band above it. Help, About and Settings at the foot are one rounded group:
  the same width, a drawn icon each (a ring with "?", a ring with "i", a gear), the text in one column. Settings
  keeps a grey outline so it is easy to find; the selected one is a single accent outline with the tint, never a
  bar inside an outline (the owner saw the overlap and asked for it to go). Panel and foot line up, 8 px from each
  edge of the sidebar. Proposal: if SummarEase gets a sidebar or a Help/About entry (UX4), use the same foot.
- **Focus ring.** Shown after a key press since the last click, not by Qt's focus reason: Qt moves the focus on
  from a hidden control (a row that folds away) with the same reason as Tab, so the ring appeared after mouse
  clicks. ClassiFile's `FocusRing` (`classifile/app/widgets.py`) tracks key presses. Relevant to UX3's visible
  focus review.
- **Scroll bars:** thin, grey, no arrows, darker under the mouse (one style-sheet block).
- **Page pictures** get a hairline edge in the divider colour, so a white page shows on a white panel (UX6, if
  previews are approved).
- **Motion:** exits ease out at once (ease-in felt slow), and a panel leaves a little faster than it arrives.
- **Table headers** start where the values below them start (Qt's item text sits about 4 px inside its padding).
- **Full width (owner, ClassiFile's card rule).** The open "Choose another…" panel had a 680 px cap and lost it;
  buttons inside keep their own width. This does not change SummarEase's reading width (section 2, item 5).

### Structure worth reusing (proposals)

1. **Page previews in a worker process.** ClassiFile drew PDF pages in the window's own process, so a damaged or
   slow file could freeze or end the window. Now `classifile/pages.py` (no Qt in it) answers one request at a time
   in a long-lived worker process (`classifile.worker.Worker`); a background thread waits for it and stale answers
   are dropped. The wait is bounded (`conn.poll(timeout)`), a page not drawn within 20 s kills that process (its
   `join` is bounded too) and the page says it can't be previewed. A model for H7's bounded receipt and cleanup,
   and for UX6's previews; keep the drawing module outside the GUI package so the worker never loads Qt.
2. **One session per data folder.** A `QLockFile` beside the catalog, taken before it is opened
   (`catalog_lock` in `classifile/app/main.py`); a second window says the app is already open, and tools that
   write the catalog take the same lock.
3. **Held-out measurements that really run once.** `once()` in ClassiFile's `tools/__init__.py`: one fixed record
   per measurement, reserved before the first document is read; another `--out` name only gets a copy. It
   complements H4 (refusing protected folders before reading) and H5 (saving completed or partial state).
4. **Safety tests on generated documents.** `tests/test_safety.py` and the `make_pdf` fixture in ClassiFile's
   `tests/conftest.py`: the copy and recovery invariants run in any checkout, without private files. The same
   approach fits H6's export-failure cases.
5. **AGENTS.md for Codex.** ClassiFile now has one at the repository root: it points to CLAUDE.md and the decision
   record and repeats the non-negotiable rules in short form. Codex skills run only when the owner types `$name`
   (`agents/openai.yaml` per skill, untracked).

### The boundary with SummarEase (ClassiFile record A10, A11)

- ClassiFile no longer shows document text anywhere, not even as a fallback preview: an Office file without a
  stored picture now says "No page picture is stored in this file." Reading text stays SummarEase's job, so
  SummarEase's readable view is the only place text is shown in the suite.
- ClassiFile's decision record is at 2.12 (installer packaging is no longer deferred). Nothing in A11 changed;
  M4 still waits for ClassiFile v1 and the owner's go-ahead (section 4, item 3).

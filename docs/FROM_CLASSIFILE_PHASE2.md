# SummarEase — second handoff from the ClassiFile inspection

2026-10-26 · ClassiFile inspected at `4d2b25b` · SummarEase context read at `20dfc69`

This is a new handoff, supplementing `docs/FROM_CLASSIFILE.md`. It records lessons from a second ClassiFile audit and proposes a focused path toward useful, trustworthy summarization. It does not change SummarEase's decision record, copied reader, implementation, references or milestone permissions.

Read `CLAUDE.md`, `DECISION_RECORD.md` 0.5, `DOS_AND_DONTS.md`, `docs/STATUS.md`, `EVALUATION.md`, `READER.md` and `INTEGRATION.md` first. The current status records M2/M3 built with acceptance work outstanding. M4 still requires ClassiFile v1 and the owner's go-ahead. This documentation request is not that go-ahead.

## What is already fixed, and what remains

The status dated 2026-10-20 records fixes H1–H7: strict budgets including headings, explained empty results, stronger automatic checks, protected-path refusal, bounded evaluation/reporting, export cleanup, and worker/export responsiveness. It records 114 tests passing at `87a40de`; this inspection did not rerun SummarEase's suite or repeat its private-document evaluation. Do not present those historical results as fresh verification.

The owner's Q1–Q3 answers and their implementation are already recorded in STATUS: strict budgets with omission disclosure, whole short documents when they fit, and explicitly chosen new exports allowed in the source folder without incidental side files. They still need the owner's decision-record update; do not ask for those decisions again or replace them with the older questions in historical prose.

The largest open product question is **whether the summaries select the right information and remain true in context**. Passing structural checks does not answer that. The prose baseline stays in place until the existing independent-reference comparison justifies replacing it. The owner has no spare dataset; reuse the development material and existing reference workflow.

## Priority 1: finish the shared extraction contract

### H8 is now independently reproduced upstream

In ClassiFile's `reader/ocr.py`, a synthetic unit had two picture regions: one yielded usable OCR text and the other failed to render. The unit ended as `done`, with no unresolved-gap flag. Successful OCR is working; partial-failure accounting is not complete enough to support trustworthy downstream statements.

Fix this in **ClassiFile's isolated reader first**. Record located per-region outcomes or equivalent explicit partial outcomes, retaining all successful text. Distinguish unsuccessful rendering, OCR engine failure, no readable text and work not attempted. Do not flatten them into “no text.” Version the changed extraction record, handle older records conservatively, test it upstream, then make a new reader tag and follow `READER.md` for the pinned copy and hash check.

SummarEase then needs the new observation to survive `source` construction, all four summary levels, notes, Copy, PDF/Word export and evaluation. Test disclosure against the reader's outcomes independently of the summary builder, so builder and checker cannot agree on the same lost warning. Do not silently patch the copied reader or update hashes merely to make its check pass.

**Acceptance case:** one unit with native text, one readable image, and one failed image still shows the successful content and identifies the unread region in every presentation/export path. A completely successful counterpart has no false warning. The patch must preserve content and OCR provenance; it does not need a new OCR engine.

Keep the separately accepted limitations separate: slide bullet nesting, chart understanding, equations and table-summary coverage are not all “OCR problems.” A reader can extract words correctly while losing a relationship needed to summarize them safely. Existing table omissions must remain disclosed; changing table selection requires its own scoped proposal and evidence.

## Priority 2: improve summary quality using the existing material

### Finish the evidence already planned

- Preserve the ten existing reference templates and their private mapping. The owner's 5–8 key points must remain independently authored before exposure to candidate summaries. Do not prefill them from this model, from ClassiFile's hidden digest, or from SummarEase's output.
- Make completing those references easier with a source-only view and optional location capture, if the owner wants the aid. Reduce clerical effort, not the independence of the answers. No additional document collection is required.
- Compare frozen methods blindly in reproducibly shuffled order using the existing coverage, faithfulness, readability and repetition rubric. Report by document kind and summary level, with denominators and exclusions. A tie retains the baseline.
- Keep automatic checks and human quality scores separate. Whole-line traceability, nesting, budgets, rename invariance and gap disclosure establish important invariants; they do not prove a useful summary.
- Record a private failure ledger with neutral IDs and short reason codes. Correct one recurring failure class at a time, then rerun the same comparison. Do not repeatedly rewrite the reference points to fit the new method.

### Test the kinds of mistakes extractive summaries can still make

The following are proposed diagnostic fixtures, not claims that each currently fails:

| Generated case | What a trustworthy result must preserve |
| --- | --- |
| A statement followed by “only if,” an exception or a limitation | Do not select a sentence that reverses the practical meaning by omitting its necessary qualification. Keep a complete contextual unit or choose a different unit within budget. |
| Two alternatives, one explicitly rejected later | Do not present the rejected alternative as the document's recommendation. |
| An acronym or pronoun whose explanation is outside the selected sentence | Prefer a self-contained unit, or include its required context within budget; never invent an expansion. |
| A numeric result with units, range and a qualifying population | Preserve the entire meaning-bearing unit. Source traceability alone is insufficient when the selected line is misleading without its label or qualifier. |
| A title/agenda repeated many times with a key conclusion only once | Repetition should not consume the budget at the expense of the actual result. |
| Two sections with different subjects and a short minority section | Disclose omissions under the owner's strict-budget rule. Comprehensive must not imply every section is represented when a section could not fit. |
| Image-only key content beside native boilerplate | Keep OCR provenance and location. Respect the current rule about OCR-only material in Brief; disclose consequences rather than quietly changing the method. |
| A table-dominated document or a document with no whole eligible line fitting | Explain the exact empty/limited outcome and direct the user to Source. Do not present a blank area as successful summarization. |
| Equivalent content under a new filename or harmless layout change | The same eligible meaning and provenance should survive; filenames never choose summary content. |

Use fixtures to reveal defects in selection and presentation; do not count them as real-world accuracy evidence. Generate variations within a case family and keep that family together in any evaluation. All actual reference points, document text and identifiable titles remain private and untracked.

### Smallest useful algorithm work

Start with context-preserving selection and duplicate/template suppression, measured against the current baseline. Keep whole source units, original wording and source order under the existing budget and nesting rules. Context requirements must consume the same budget; never add a hidden overflow or silently paraphrase to squeeze content in.

Long-document coverage should be a measured trade-off, with a short omitted-section note when strict budgets prevent inclusion. Keep source location navigation, OCR markers and export consistency as part of the result, not decoration added afterward. An explanation of why a level is short or empty often helps more than an extra control.

No automatic “learning” claim is warranted simply because users press Copy or spend time reading. SummarEase currently has extractive methods, not an approved training loop. If feedback is added, make it an explicit private quality note tied to the exact source/reader/method/settings version. Use it to identify failure types; do not turn unreviewed feedback into training data. LLM rewriting and new ML dependencies remain separate owner decisions under C13 and the project rules.

## Priority 3: carry the safety lessons across, without copying ClassiFile's architecture

The ClassiFile audit reproduced a matching update reinstalling forgotten examples, removal retaining model influence, and the catalog lock being released while a background job remained active. Those are ClassiFile findings, not allegations that SummarEase has the same bugs. They suggest concrete SummarEase acceptance tests:

- **Reject stale results:** open source A, start a slow summary, switch to B or change the requested level, then finish A. Only the current request may update the panes or enable Copy/Export. Tie a result to source identity and method/settings revision, not a displayed filename alone.
- **Define cancellation ownership:** cancel or close during reading, summarization and export. A late callback cannot reopen the result or publish an export after cancellation. During an already-committed publication, explain the safe completion boundary rather than promising an impossible rollback.
- **Bound the whole operation:** retain the H7 bounded cleanup, and test partial result transfer as well as parser timeouts. ClassiFile's `poll(timeout)` followed by blocking `recv()` shows why a parser deadline alone is not an end-to-end guarantee. SummarEase's own transfer path deserves the same deliberate stalled-result test; its join fix does not itself prove that property.
- **Preserve source identity:** changed bytes at the same path invalidate cached extraction and provenance. Reusing a path or UI title must not reuse an earlier document's source links.
- **Keep publication checks:** unique new destination, exclusive creation, read-back validation, and cleanup only of files the operation actually created. Test cancel/failure around the publication boundary, not just before export starts.
- **Keep diagnostics private:** operation kind, versions, durations, counts and fixed failure reasons are sufficient. No document text, pasted content, source paths or identifiable filenames in a copied report. No automatic upload.

ClassiFile's hidden internal summary is for naming/checks and is not a gold summary or replacement for SummarEase's extraction record. Do not classify from generated summaries, train from them, or make SummarEase depend on ClassiFile's catalog. Share the versioned reader contract and carefully scoped suite conventions only.

## Layout and interaction improvements worth making

Keep the existing Source/summary relationship clear. The primary action depends on state: open/paste when empty, summarize when content is ready, cancel while working, then copy/export or follow a source link. Explain an unread/unsupported outcome at that location with a useful next step.

ClassiFile's new motion is optional polish, not a reason to redesign SummarEase. If adopting hover fades, pressed feedback or collapsible panels, use the same motion preference semantics and immediate reduced-motion behavior. Source navigation must not wait for an animation, and keyboard focus must remain visible when a panel collapses.

Keep the established suite palette and semantic roles, pinned token checks and high-DPI rendering. **Preserve SummarEase's owner-approved 70–90-character reading width (`READING_CHARS = 80`).** Its panes fill the workspace; its document text has its own reading measure. ClassiFile's full-width running-text rule must not be copied over it.

For long documents, preserve scroll position when switching level where sensible, make the current source target identifiable, provide a clear route back, and avoid resetting zoom unexpectedly. Some navigation/zoom features are already implemented according to STATUS: verify their interaction before proposing another implementation. Disclosures must remain visible and travel with copied/exported output; do not bury them only in a tooltip or an expandable technical panel.

Test native keyboard focus, menu operation, high contrast and screen-reader names at the owner's scaling. Watch animations actually play. Screenshot and timing checks are useful evidence for geometry and cost, not proof of comfortable live use.

## Packaging and eventual integration

Finish M2/M3 acceptance before describing SummarEase as ready. A future package needs its own stable application identity and locations, a uniquely versioned build tied to source, and clean-Windows checks covering offline reading/OCR, summary generation, preview/source navigation and PDF/Word export. Test exports in common readers on disposable material when that application launch is authorized. Reuse ClassiFile's release checklist structure, not its AppId or mutable development state.

For M4 planning, keep `INTEGRATION.md` as the authority: explicit user invocation, bounded work, compatible protocol/extraction versions, source identity and temporary-file lifetime, clear cancellation/error behavior, and no writes into ClassiFile's catalog. Test coexistence and caller/receiver version mismatch when M4 is authorized. The present handoff does not implement or register an integration.

## Recommended next session

1. Read the current status and owner answers; reconcile stale evaluation/milestone wording through proposals rather than editing the decision record.
2. Coordinate the upstream H8 contract fix, then sync the tagged reader and test disclosure throughout SummarEase.
3. Finish the independent references and frozen baseline comparison using existing development files. Pick one evidenced quality weakness, not a wholesale summarizer rewrite.
4. Add a small set of generated context, stale-result and cancellation cases. Verify the current implementation against them, then fix only demonstrated failures.
5. Finish the M3 owner review and package acceptance. Leave M4 at its explicit gate.

**Verdict:** the fastest credible improvement is better selection evidence, context and disclosure, supported by the existing reference process. It is not more generated training data or another layer called an agent. Preserve the working OCR and the safety fixes already made.

**Not checked in this handoff:** a fresh SummarEase test run, private reference contents or quality scoring, held-out sets, clean-machine packaging, external-reader exports, and live motion/accessibility behavior. The only change requested here is this handoff document.

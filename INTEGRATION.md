# Integration with ClassiFile (draft)

A draft for M4, built only after ClassiFile v1 and the owner's M4 go-ahead. C1 already confirms the boundaries
below; the protocol and lifecycle details remain proposals. Reviewing this document is allowed preparation,
not authorization to implement registration, a receiver or a fake-caller test now.

## Confirmed boundaries (C1, C2, C9 and standing rules)

- ClassiFile asks the user every time before calling SummarEase.
- SummarEase never writes ClassiFile's catalog, folders or settings. It reads only what a request gives it.
- Each app works when the other is not installed.
- Discovery uses a registration file in `%LOCALAPPDATA%\ClariFile`; its exact format is still a draft.
- Runtime stays offline. Pasted text is not stored unless the user chooses to store it.

## Proposed discovery

The proposed installation registration is `%LOCALAPPDATA%\ClariFile\summarease.json`:

```json
{
  "app": "SummarEase",
  "version": "1.0.0",
  "protocol": 1,
  "executable": "C:\\path\\to\\SummarEase.exe"
}
```

ClassiFile reads it to see whether SummarEase is installed and which protocol it speaks. A missing or unreadable
file means that SummarEase is not available.

Validate the app identity, supported protocol and executable location before launch; pass arguments without a
shell. Installation/update/uninstall must own only SummarEase's registration and never remove a registration
belonging to another installation or app. SummarEase needs a distinct installer AppId and paths from ClassiFile.
No implementation of these lifecycle rules exists in this repository yet.

## Request (protocol 1)

Illustrative file-input request, proposed as JSON in a private temporary folder owned by the caller:

```json
{
  "protocol": 1,
  "input": {"kind": "file", "path": "C:\\...\\copy.pdf"},
  "level": "key"
}
```

- `input.kind`:
  - `"file"`: the path of a document, opened read-only;
  - `"record"`: an extraction record (the reader's format, with its record version);
  - `"text"`: pasted text.
- `level`: propose stable IDs `brief`, `key`, `detailed`, `comprehensive`, mapped to the four C12 display names.
  Display wording or localization must not change protocol identifiers. Reject an unknown level.
- `record` and `text` payloads are not specified by the example. Before adding either, define and validate their
  fields, size limits and source/provenance requirements. Refuse unknown protocol/reader-record versions and
  malformed input rather than silently guessing.
- Temporary JSON containing pasted text is storage under C9. Prefer memory transport for text; if disk transport
  is proposed, obtain explicit storage consent. Per-call consent to summarize is not automatically storage consent.

## Proposed response and lifecycle

```json
{
  "protocol": 1,
  "status": "ok",
  "lines": [{"text": "…", "page": 3}],
  "unread": [{"page": 7, "note": "a picture with no readable text"}],
  "warnings": ["Pages 12 to 14 are OCR text and may contain errors."]
}
```

- The example illustrates `"ok"`; refusal, operational error, cancellation and timeout must be distinct outcomes
  in the final protocol, with fixed text-free reasons. A partial response is never an `"ok"` result.
- `lines`: the summary, each line with its page, slide or section.
- `unread` and `warnings`: what couldn't be read and which text is OCR, not a numerical confidence claim.
  These disclosures are never left out.
- No document text appears in either app's logs.

Proposed lifecycle requirements: associate each request/result with the intended document and request identity;
bound work; support cancellation; reject stale responses; keep the previous completed result visible. The caller
retains temporary inputs until the receiver has finished or acknowledged cancellation, then cleans only files it
created. Recovery from a caller/receiver crash must not delete user documents or another request's files.
Response transport and recovery details are to be confirmed with the protocol before coding.

## M4 acceptance cases (future work)

- A missing app or missing/malformed/foreign registration leaves the other app usable.
- Unsupported versions/levels, malformed payloads, inaccessible files and oversized requests are refused plainly.
- Paths with spaces are passed as arguments, never shell text; the receiver opens documents read-only.
- Refusing the consent prompt launches nothing. Text transport does not persist pasted text without storage consent.
- Cancellation, timeout and caller/receiver crashes have bounded cleanup; stale results cannot replace the active
  document's result. No successful result loses source references or OCR/gap disclosures.
- Upgrade and uninstall affect only the intended SummarEase installation. Test coexistence and registration
  ownership on disposable Windows; never install or uninstall on the owner's laptop.

These are draft acceptance requirements for the future M4 implementation, not evidence it has been built.

# Integration with ClassiFile (draft)

A draft for M4, built only after ClassiFile v1. Nothing here is confirmed; the owner decides at M4.

## Rules

- ClassiFile asks the user every time before calling SummarEase.
- SummarEase never writes ClassiFile's catalog, folders or settings. It reads only what a request gives it.
- Each app works when the other is not installed.

## Finding SummarEase: the registration file

SummarEase writes `%LOCALAPPDATA%\ClariFile\summarease.json` when it is installed, and removes it when it is
uninstalled:

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

## Request (protocol 1)

Passed as a JSON file in a temporary folder that ClassiFile creates and later deletes:

```json
{
  "protocol": 1,
  "input": {"kind": "file", "path": "C:\\...\\copy.pdf"},
  "level": "key points"
}
```

- `input.kind`:
  - `"file"`: the path of a document, opened read-only;
  - `"record"`: an extraction record (the reader's format, with its record version);
  - `"text"`: pasted text.
- `level`: one of the levels the record confirms.

## Response

```json
{
  "protocol": 1,
  "status": "ok",
  "lines": [{"text": "…", "page": 3}],
  "unread": [{"page": 7, "note": "a picture with no readable text"}],
  "warnings": ["Pages 12 to 14 are OCR text and may contain errors."]
}
```

- `status` is `"ok"` or `"refused"` (with a plain `reason`, for example an unknown protocol).
- `lines`: the summary, each line with its page, slide or section.
- `unread` and `warnings`: what couldn't be read, and how sure the text is. These are never left out.
- No document text appears in either app's logs.

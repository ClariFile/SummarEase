# Source of this reader

Copied unchanged from ClassiFile's `classifile/reader/` (READER.md, option (a)).

- Source: ClassiFile tag **`reader-v7`** (commit `bd9214396b62a810e91aff80ad004fcf33fdccfb`), taken on 2026-10-26.
  The tag is local in ClassiFile until the owner pushes it. The previous copy was `reader-v6`
  (commit `015b4160c8f671cf2575ecb488c73ce98e96098b`, 2026-10-14).
- Record version: 7. Format reader versions: pdf-6, docx-7, pptx-7, odt-6.
- What changed since `reader-v6`: each OCR'd picture's outcome is kept (`UnitRecord.ocr_pictures`: read, no_text,
  render_failed, engine_failed, not_attempted), a unit that read some pictures and not others says `partial`
  (H8), and `unread_gap()` answers whether a unit still holds content nothing has read. Also the installed app's
  bundled OCR data (`bundled_tessdata`), from ClassiFile's installer work.
- The OCR switch keeps ClassiFile's name: `CLASSIFILE_OCR=off`.

Sync rule: ClassiFile's reader is the source. Do not edit these files here. A fix found in SummarEase goes to
ClassiFile first and is copied back; copies are taken only at a tag, and this file is updated with the new tag
and hashes.

## The files at `reader-v7`

SHA-256 of each file as stored at the tag (line breaks as `
`; a Windows checkout's `
` is read as `
`
before hashing). Checked on 2026-10-26: the copy here matches all six.

| File | SHA-256 |
|---|---|
| `__init__.py` | `19bc9c5bf236320b301ab321b33cd625252781f2ba5d5e80088da0478d97df52` |
| `common.py` | `21c72a81cd4ee773ebc8ac8d7294e828141226b1bc37bf53404567ac5b70daca` |
| `ocr.py` | `c19038fdc6bba5ce45053d063270e1ec4194b580ede6561fc1916a1f98ca623c` |
| `odt.py` | `d97a0e7164f97fec08bb66a13f6efeda0069fa807ae999e7781696ef71c60da4` |
| `ooxml.py` | `850a2afd20c736a1800c7f5effafed003f38eb83b21a64a66b6bdf775083ba8f` |
| `pdf.py` | `4ecdf1d10d05416608d8f5fecee3ebef8f80eb37bf984515940949a8923c6e73` |

**The reader check** (`tests/test_reader_copy.py`, done 2026-10-15): a test that fails if the files in `summarease/reader/` differ
from this table: the same six files (no more, no fewer), each with the hash above. `SOURCE.md` itself is not
hashed.

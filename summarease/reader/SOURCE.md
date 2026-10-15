# Source of this reader

Copied unchanged from ClassiFile's `classifile/reader/` (READER.md, option (a)).

- Source: ClassiFile tag **`reader-v6`** (commit `015b4160c8f671cf2575ecb488c73ce98e96098b`). The copy was taken
  at that commit on 2026-10-14, with the owner's approval; the tag was added and pushed on 2026-10-15.
- Record version: 6. Format reader versions: pdf-5, docx-6, pptx-6, odt-5.
- The OCR switch keeps ClassiFile's name: `CLASSIFILE_OCR=off`.

Sync rule: ClassiFile's reader is the source. Do not edit these files here. A fix found in SummarEase goes to
ClassiFile first and is copied back; copies are taken only at a tag, and this file is updated with the new tag
and hashes.

## The files at `reader-v6`

SHA-256 of each file as stored at the tag (line breaks as `\n`; a Windows checkout's `\r\n` is read as `\n`
before hashing). Checked on 2026-10-15: the copy here matches all six.

| File | SHA-256 |
|---|---|
| `__init__.py` | `67e24200455111e1dcc052027172d6062f23b104d644ccd558e3a01f532be30d` |
| `common.py` | `12e118f65c6bb9d0af4f5c625caf1b194e512af4b891a7552c9c30c3ba53f223` |
| `ocr.py` | `ca780923b4e8f3e4a07f487e8d3f841f5875a702ede321aa9c0d330ba86ead6f` |
| `odt.py` | `bdec632a84d33c52b6a4ecffba6fd2cb05137690d82ffc5366057cf5eac5fc2c` |
| `ooxml.py` | `1f145d22a81e5a9d1d8ecca64ef2b24cd5b74faa4879229d1f5066e644027fc1` |
| `pdf.py` | `b18be433f20d29ddeb2d310ac0d5ee9fcf3b5ea3672b92434ef8bfdf2494bf54` |

**The reader check** (`tests/test_reader_copy.py`, done 2026-10-15): a test that fails if the files in `summarease/reader/` differ
from this table: the same six files (no more, no fewer), each with the hash above. `SOURCE.md` itself is not
hashed.

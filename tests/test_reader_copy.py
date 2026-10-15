"""The copied reader equals ClassiFile's tag reader-v6: the files and hashes listed in summarease/reader/SOURCE.md."""
import hashlib
import re
from pathlib import Path

READER = Path(__file__).resolve().parent.parent / "summarease" / "reader"


def expected_hashes():
    rows = re.findall(r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|$", (READER / "SOURCE.md").read_text(encoding="utf-8"), re.M)
    return dict(rows)


def test_source_table_lists_the_six_reader_files():
    assert sorted(expected_hashes()) == ["__init__.py", "common.py", "ocr.py", "odt.py", "ooxml.py", "pdf.py"]


def test_reader_copy_matches_reader_v6():
    actual = {
        p.name: hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        for p in READER.iterdir()
        if p.is_file() and p.name != "SOURCE.md"
    }
    assert actual == expected_hashes()

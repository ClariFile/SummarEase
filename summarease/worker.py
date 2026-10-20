"""Heavy work runs in a worker process with a time limit (DOS_AND_DONTS.md): a crash, a hang or a timeout is an
operational failure, reported plainly, never a result. The workers only read; the one file a worker writes is an
export's temporary check copy, in the system's temporary folder (export.prepare). Waiting on a worker is always
bounded: a worker that sends its result and then hangs is stopped, so the window never waits for it."""
import hashlib
import multiprocessing as mp
import time

from .reader import ReadResult, read_document

TIME_LIMIT = 300    # seconds per file; the reader's own OCR budget (240 s) fits inside it
TIMED_OUT = "it took longer than the time limit"
STOPPED = "the worker stopped unexpectedly"
JOIN_LIMIT = 2      # seconds a worker gets to exit after its result, or after it is killed
BOLD = 16           # PyMuPDF span flag


def read(conn, path):
    """Read a document: ("ok", (ReadResult, bold)) where bold is pdf_bold's map for a PDF, else None."""
    try:
        res = read_document(path)
        bold = pdf_bold(path, res.sha256) if res.status == "ok" and res.record.format == "pdf" else None
    except Exception as e:     # the reason is the error's type only: never document text
        res, bold = ReadResult("failed", f"error while reading ({type(e).__name__})", None, None), None
    conn.send(("ok", (res, bold)))
    conn.close()


def pdf_bold(path, sha256):
    """{page: [[line is bold, ...] per text block]}, in the order of the reader's layout blocks and lines. The reader
    keeps sizes but not weights, so the fonts are read here, from the same bytes (checked by hash), read-only."""
    import pymupdf

    from .reader.pdf import LAYOUT_FLAGS

    with open(path, "rb") as f:
        data = f.read()
    if hashlib.sha256(data).hexdigest() != sha256:
        return None
    out = {}
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        for i, page in enumerate(doc, 1):
            blocks = [b for b in page.get_text("dict", flags=LAYOUT_FLAGS)["blocks"] if b.get("type") == 0]
            out[i] = [[all(s["flags"] & BOLD or "bold" in s["font"].lower() for s in l["spans"] if s["text"].strip())
                       and any(s["text"].strip() for s in l["spans"]) for l in b["lines"]] for b in blocks]
    return out


def call(conn, fn, *args):
    """Run fn(*args) and send its result, or an Exception's type name (never its message, which may hold text)."""
    try:
        conn.send(("ok", fn(*args)))
    except Exception as e:
        conn.send(("failed", type(e).__name__))
    conn.close()


class Job:
    """target(conn, *args) in its own process; the target sends ("ok", result) or ("failed", reason). poll() returns
    None while it runs, then that pair once, or ("failed", reason) for a crash or a timeout."""

    def __init__(self, target, *args, time_limit=TIME_LIMIT):
        ctx = mp.get_context("spawn")
        self._conn, child = ctx.Pipe(duplex=False)
        self._proc = ctx.Process(target=target, args=(child, *args), daemon=True)
        self._proc.start()
        child.close()
        self._deadline = time.monotonic() + time_limit
        self.started = time.monotonic()

    def poll(self):
        try:
            if self._conn.poll():
                res = self._conn.recv()
                self._finish()
                return res
        except (EOFError, OSError):     # the process ended without sending a result (a broken pipe on Windows)
            self._finish()
            return ("failed", STOPPED)
        if time.monotonic() > self._deadline:
            self.cancel()
            return ("failed", TIMED_OUT)
        return None

    def cancel(self):
        if self._proc.is_alive():
            self._proc.kill()
        self._finish()

    def _finish(self):
        self._proc.join(JOIN_LIMIT)
        if self._proc.is_alive():
            self._proc.kill()
            self._proc.join(JOIN_LIMIT)
        self._conn.close()

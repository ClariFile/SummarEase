"""Reading runs in a worker process with a time limit per file (DOS_AND_DONTS.md): a crash, a hang or a timeout is
an operational failure, reported plainly, never a result. The worker only reads; it writes no file."""
import multiprocessing as mp
import time

from .reader import ReadResult, read_document

TIME_LIMIT = 300    # seconds per file; the reader's own OCR budget (240 s) fits inside it
TIMED_OUT = "reading took longer than the time limit"
STOPPED = "the reader stopped unexpectedly"


def _read(path, conn):
    try:
        res = read_document(path)
    except Exception as e:     # the reason is the error's type only: never document text
        res = ReadResult("failed", f"error while reading ({type(e).__name__})", None, None)
    conn.send(res)
    conn.close()


class ReadJob:
    """One file read in its own process. poll() returns None while it runs, then a ReadResult once."""

    def __init__(self, path, time_limit=TIME_LIMIT, target=_read):
        ctx = mp.get_context("spawn")
        self._conn, child = ctx.Pipe(duplex=False)
        self._proc = ctx.Process(target=target, args=(str(path), child), daemon=True)
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
            return ReadResult("failed", STOPPED, None, None)
        if time.monotonic() > self._deadline:
            self.cancel()
            return ReadResult("failed", TIMED_OUT, None, None)
        return None

    def cancel(self):
        if self._proc.is_alive():
            self._proc.kill()
        self._finish()

    def _finish(self):
        self._proc.join()
        self._conn.close()

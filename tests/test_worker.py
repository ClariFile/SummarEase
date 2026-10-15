"""M1: reading runs in a worker process with a time limit; a hang or a crash is reported plainly, never a result.
No test depends on timing: each waits for the condition itself, with a generous limit that only stops a hung test."""
import hashlib
import os
import threading
import time

from summarease.worker import STOPPED, TIMED_OUT, ReadJob
from test_reader import make_pdf

LIMIT = 120


def wait(job):
    end = time.monotonic() + LIMIT
    while time.monotonic() < end:
        res = job.poll()
        if res is not None:
            return res
        time.sleep(0.05)
    job.cancel()
    raise AssertionError("the worker gave no result")


def _hang(path, conn):
    threading.Event().wait()


def _crash(path, conn):
    os._exit(3)


def test_a_document_is_read_in_the_worker_without_changing_it(tmp_path):
    path = make_pdf(tmp_path / "a.pdf")
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    res = wait(ReadJob(path))
    assert res.status == "ok" and res.record.unit_count == 2
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before == res.sha256
    assert [p.name for p in tmp_path.iterdir()] == ["a.pdf"]


def test_a_worker_past_its_time_limit_is_stopped_and_reported(tmp_path):
    job = ReadJob(make_pdf(tmp_path / "a.pdf"), time_limit=0, target=_hang)
    res = wait(job)
    assert (res.status, res.reason, res.record) == ("failed", TIMED_OUT, None)
    assert not job._proc.is_alive()


def test_a_worker_that_crashes_is_reported(tmp_path):
    res = wait(ReadJob(make_pdf(tmp_path / "a.pdf"), target=_crash))
    assert (res.status, res.reason, res.record) == ("failed", STOPPED, None)

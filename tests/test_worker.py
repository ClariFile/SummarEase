"""Heavy work runs in a worker process with a time limit; a hang or a crash is reported plainly, never a result.
No test depends on timing: each waits for the condition itself, with a generous limit that only stops a hung test."""
import hashlib
import os
import threading
import time

from summarease.worker import STOPPED, TIMED_OUT, Job, call, read
from test_reader import make_pdf
from tools.sample_docs import make_text_pdf

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


def _hang(conn, path):
    threading.Event().wait()


def _crash(conn, path):
    os._exit(3)


def test_a_document_is_read_in_the_worker_without_changing_it(tmp_path):
    path = make_pdf(tmp_path / "a.pdf")
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    state, (res, bold) = wait(Job(read, str(path)))
    assert state == "ok" and res.status == "ok" and res.record.unit_count == 2 and set(bold) == {1, 2}
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before == res.sha256
    assert [p.name for p in tmp_path.iterdir()] == ["a.pdf"]


def test_bold_lines_are_found_in_the_order_of_the_readers_layout(tmp_path):
    path = make_text_pdf(tmp_path / "t.pdf", pages=1)
    _, (res, bold) = wait(Job(read, str(path)))
    layout = res.record.units[0].layout["blocks"]
    assert [len(b) for b in bold[1]] == [len(b["lines"]) for b in layout]
    flagged = [l["text"] for b, f in zip(layout, bold[1]) for l, x in zip(b["lines"], f) if x]
    assert "Design notes" in flagged and "Invented Handbook of Systems" not in flagged


def test_a_worker_past_its_time_limit_is_stopped_and_reported(tmp_path):
    job = Job(_hang, str(make_pdf(tmp_path / "a.pdf")), time_limit=0)
    assert wait(job) == ("failed", TIMED_OUT)
    assert not job._proc.is_alive()


def test_a_worker_that_crashes_is_reported(tmp_path):
    assert wait(Job(_crash, str(make_pdf(tmp_path / "a.pdf")))) == ("failed", STOPPED)


def test_a_function_that_raises_reports_only_the_error_type():
    assert wait(Job(call, int, "not a number with private words")) == ("failed", "ValueError")


def _send_then_hang(conn, path):
    conn.send(("ok", "result"))
    threading.Event().wait()


def test_a_worker_that_sends_its_result_and_hangs_is_stopped_without_blocking(tmp_path):
    job = Job(_send_then_hang, str(make_pdf(tmp_path / "a.pdf")))
    start = time.monotonic()
    assert wait(job) == ("ok", "result")
    assert not job._proc.is_alive() and time.monotonic() - start < LIMIT


def test_cancel_reaps_the_worker(tmp_path):
    job = Job(_hang, str(make_pdf(tmp_path / "a.pdf")))
    job.cancel()
    assert not job._proc.is_alive()

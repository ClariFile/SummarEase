import socket

import pytest


def _blocked(*a, **k):
    raise RuntimeError("Network access attempted during tests")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    for name in ("connect", "connect_ex"):
        monkeypatch.setattr(socket.socket, name, _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(socket, "getaddrinfo", _blocked)


@pytest.fixture(autouse=True)
def ocr_off_unless_marked(request, monkeypatch):
    """Only tests marked "ocr" run Tesseract; the switch name comes from the copied reader."""
    if "ocr" not in request.keywords:
        monkeypatch.setenv("CLASSIFILE_OCR", "off")

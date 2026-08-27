"""Unit tests for host-safe archive extraction (T081, FR-001/016)."""
from __future__ import annotations

import io
import os
import tarfile
import tempfile
import zipfile

import pytest

from src.services.archive_extraction import (
    UnsafeArchiveError,
    UnsupportedArchiveError,
    extract_archive,
)


def _dest() -> str:
    return tempfile.mkdtemp(prefix="agon-x-")


def _write(path: str, data: bytes) -> str:
    with open(path, "wb") as fh:
        fh.write(data)
    return path


def _zip_bytes(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


def _targz_bytes(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for name, content in files.items():
            data = content.encode()
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def test_extracts_zip():
    d = _dest()
    archive = _write(os.path.join(_dest(), "a.zip"), _zip_bytes({"main.py": "x = 1\n"}))
    result = extract_archive(archive, d)
    assert "main.py" in result.file_names
    assert os.path.exists(os.path.join(d, "main.py"))


def test_extracts_targz():
    d = _dest()
    archive = _write(os.path.join(_dest(), "a.tar.gz"), _targz_bytes({"pkg/main.py": "y = 2\n"}))
    result = extract_archive(archive, d)
    assert os.path.join("pkg", "main.py") in result.file_names
    assert os.path.exists(os.path.join(d, "pkg", "main.py"))


def test_rejects_unknown_format():
    d = _dest()
    archive = _write(os.path.join(_dest(), "a.bin"), b"not an archive")
    with pytest.raises(UnsupportedArchiveError):
        extract_archive(archive, d)


def test_rejects_zip_path_traversal():
    d = _dest()
    archive = _write(os.path.join(_dest(), "evil.zip"), _zip_bytes({"../escape.py": "bad"}))
    with pytest.raises(UnsafeArchiveError):
        extract_archive(archive, d)


def test_rejects_tar_absolute_path():
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        data = b"bad"
        info = tarfile.TarInfo(name="/etc/agon_pwn")
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    d = _dest()
    archive = _write(os.path.join(_dest(), "abs.tar.gz"), buf.getvalue())
    with pytest.raises(UnsafeArchiveError):
        extract_archive(archive, d)


def test_rejects_tar_symlink():
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        info = tarfile.TarInfo(name="link.py")
        info.type = tarfile.SYMTYPE
        info.linkname = "/etc/passwd"
        tf.addfile(info)
    d = _dest()
    archive = _write(os.path.join(_dest(), "link.tar.gz"), buf.getvalue())
    with pytest.raises(UnsafeArchiveError):
        extract_archive(archive, d)


def test_rejects_too_many_members(monkeypatch):
    from src.services import archive_extraction

    monkeypatch.setattr(archive_extraction, "MAX_MEMBERS", 2)
    d = _dest()
    archive = _write(
        os.path.join(_dest(), "many.zip"),
        _zip_bytes({"a.py": "1", "b.py": "2", "c.py": "3"}),
    )
    with pytest.raises(UnsafeArchiveError):
        extract_archive(archive, d)

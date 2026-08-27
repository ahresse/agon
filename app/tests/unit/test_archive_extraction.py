"""Unit tests for host-safe archive extraction (FR-001, FR-016; Constitution II).

Organized into topic subsections (one class per concern):

- TestFormatDetection  — accepted formats and content-based detection
- TestPathSafety       — zip-slip / tar-slip / absolute-path rejection
- TestLinkSafety       — symlink / hardlink / device member rejection
- TestResourceLimits   — member-count and uncompressed-size (bomb) guards
- TestCorruptedArchives— truncated / malformed inputs
- TestExtractionResult — returned file list, nesting, non-.py members
"""
from __future__ import annotations

import bz2
import io
import lzma
import os
import tarfile
import tempfile
import zipfile

import pytest

from src.services import archive_extraction
from src.services.archive_extraction import (
    UnsafeArchiveError,
    UnsupportedArchiveError,
    extract_archive,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _dest() -> str:
    return tempfile.mkdtemp(prefix="agon-x-")


def _write(name: str, data: bytes) -> str:
    path = os.path.join(_dest(), name)
    with open(path, "wb") as fh:
        fh.write(data)
    return path


def _zip_bytes(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


def _tar_bytes(files: dict[str, str], mode: str = "w:gz") -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode=mode) as tf:
        for name, content in files.items():
            data = content.encode()
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _tar_special(name: str, typeflag: bytes, linkname: str = "") -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        info = tarfile.TarInfo(name=name)
        info.type = typeflag
        info.linkname = linkname
        tf.addfile(info)
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# Format detection
# --------------------------------------------------------------------------- #
class TestFormatDetection:
    """Accepted archive formats and content-based (not extension-based) detection."""

    def test_extracts_zip(self):
        d = _dest()
        archive = _write("a.zip", _zip_bytes({"main.py": "x = 1\n"}))
        result = extract_archive(archive, d)
        assert "main.py" in result.file_names

    def test_extracts_targz(self):
        d = _dest()
        archive = _write("a.tar.gz", _tar_bytes({"pkg/main.py": "y = 2\n"}))
        result = extract_archive(archive, d)
        assert os.path.join("pkg", "main.py") in result.file_names

    def test_extracts_plain_tar(self):
        d = _dest()
        archive = _write("a.tar", _tar_bytes({"main.py": "z = 3\n"}, mode="w:"))
        result = extract_archive(archive, d)
        assert "main.py" in result.file_names

    def test_extracts_tar_bz2(self):
        d = _dest()
        archive = _write("a.tar.bz2", _tar_bytes({"main.py": "b = 1\n"}, mode="w:bz2"))
        result = extract_archive(archive, d)
        assert "main.py" in result.file_names

    def test_extracts_tar_xz(self):
        d = _dest()
        archive = _write("a.tar.xz", _tar_bytes({"main.py": "c = 1\n"}, mode="w:xz"))
        result = extract_archive(archive, d)
        assert "main.py" in result.file_names

    def test_detection_is_content_based_not_filename(self):
        # tar.gz bytes deceptively named ".zip" must still be detected as tar.
        d = _dest()
        archive = _write("liar.zip", _tar_bytes({"main.py": "x = 1\n"}))
        result = extract_archive(archive, d)
        assert "main.py" in result.file_names

    def test_rejects_unknown_format(self):
        d = _dest()
        archive = _write("a.bin", b"not an archive at all")
        with pytest.raises(UnsupportedArchiveError):
            extract_archive(archive, d)

    def test_rejects_empty_file(self):
        d = _dest()
        archive = _write("empty.zip", b"")
        with pytest.raises(UnsupportedArchiveError):
            extract_archive(archive, d)


# --------------------------------------------------------------------------- #
# Path safety (traversal / absolute paths)
# --------------------------------------------------------------------------- #
class TestPathSafety:
    """Members must never resolve outside the extraction directory."""

    def test_rejects_zip_parent_traversal(self):
        d = _dest()
        archive = _write("evil.zip", _zip_bytes({"../escape.py": "bad"}))
        with pytest.raises(UnsafeArchiveError):
            extract_archive(archive, d)

    def test_rejects_zip_nested_traversal(self):
        d = _dest()
        archive = _write("evil.zip", _zip_bytes({"a/b/../../../escape.py": "bad"}))
        with pytest.raises(UnsafeArchiveError):
            extract_archive(archive, d)

    def test_rejects_zip_absolute_path(self):
        d = _dest()
        # zipfile normalizes leading "/", so craft the member via raw name.
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            info = zipfile.ZipInfo(filename="/etc/agon_pwn")
            zf.writestr(info, "bad")
        archive = _write("abs.zip", buf.getvalue())
        with pytest.raises(UnsafeArchiveError):
            extract_archive(archive, d)

    def test_rejects_tar_parent_traversal(self):
        d = _dest()
        archive = _write("evil.tar.gz", _tar_bytes({"../escape.py": "bad"}))
        with pytest.raises(UnsafeArchiveError):
            extract_archive(archive, d)

    def test_rejects_tar_absolute_path(self):
        d = _dest()
        archive = _write("abs.tar.gz", _tar_bytes({"/etc/agon_pwn": "bad"}))
        with pytest.raises(UnsafeArchiveError):
            extract_archive(archive, d)


# --------------------------------------------------------------------------- #
# Link safety (symlink / hardlink / device)
# --------------------------------------------------------------------------- #
class TestLinkSafety:
    """Non-regular members that could point outside the sandbox are rejected."""

    def test_rejects_tar_symlink(self):
        d = _dest()
        archive = _write("link.tar.gz", _tar_special("link.py", tarfile.SYMTYPE, "/etc/passwd"))
        with pytest.raises(UnsafeArchiveError):
            extract_archive(archive, d)

    def test_rejects_tar_hardlink(self):
        d = _dest()
        archive = _write("hl.tar.gz", _tar_special("hl.py", tarfile.LNKTYPE, "main.py"))
        with pytest.raises(UnsafeArchiveError):
            extract_archive(archive, d)

    def test_rejects_tar_device(self):
        d = _dest()
        archive = _write("dev.tar.gz", _tar_special("dev0", tarfile.CHRTYPE))
        with pytest.raises(UnsafeArchiveError):
            extract_archive(archive, d)

    def test_rejects_zip_symlink(self):
        # Symlink encoded via the unix mode bits in external_attr.
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            info = zipfile.ZipInfo("link.py")
            info.external_attr = (0o120777 << 16)  # S_IFLNK
            zf.writestr(info, "/etc/passwd")
        d = _dest()
        archive = _write("zlink.zip", buf.getvalue())
        with pytest.raises(UnsafeArchiveError):
            extract_archive(archive, d)


# --------------------------------------------------------------------------- #
# Resource limits (decompression bombs)
# --------------------------------------------------------------------------- #
class TestResourceLimits:
    """Member-count and total-uncompressed-size guards must trip before writing."""

    def test_rejects_too_many_zip_members(self, monkeypatch):
        monkeypatch.setattr(archive_extraction, "MAX_MEMBERS", 2)
        d = _dest()
        archive = _write("many.zip", _zip_bytes({"a.py": "1", "b.py": "2", "c.py": "3"}))
        with pytest.raises(UnsafeArchiveError):
            extract_archive(archive, d)

    def test_rejects_too_many_tar_members(self, monkeypatch):
        monkeypatch.setattr(archive_extraction, "MAX_MEMBERS", 2)
        d = _dest()
        archive = _write("many.tar.gz", _tar_bytes({"a.py": "1", "b.py": "2", "c.py": "3"}))
        with pytest.raises(UnsafeArchiveError):
            extract_archive(archive, d)

    def test_rejects_zip_size_bomb(self, monkeypatch):
        monkeypatch.setattr(archive_extraction, "MAX_TOTAL_UNCOMPRESSED_BYTES", 10)
        d = _dest()
        archive = _write("bomb.zip", _zip_bytes({"big.py": "x" * 100}))
        with pytest.raises(UnsafeArchiveError):
            extract_archive(archive, d)

    def test_rejects_tar_size_bomb(self, monkeypatch):
        monkeypatch.setattr(archive_extraction, "MAX_TOTAL_UNCOMPRESSED_BYTES", 10)
        d = _dest()
        archive = _write("bomb.tar.gz", _tar_bytes({"big.py": "x" * 100}))
        with pytest.raises(UnsafeArchiveError):
            extract_archive(archive, d)

    def test_accepts_at_size_boundary(self, monkeypatch):
        monkeypatch.setattr(archive_extraction, "MAX_TOTAL_UNCOMPRESSED_BYTES", 5)
        d = _dest()
        archive = _write("edge.zip", _zip_bytes({"m.py": "12345"}))  # exactly 5 bytes
        result = extract_archive(archive, d)
        assert "m.py" in result.file_names


# --------------------------------------------------------------------------- #
# Corrupted archives
# --------------------------------------------------------------------------- #
class TestCorruptedArchives:
    """Malformed inputs raise UnsupportedArchiveError, never crash."""

    def test_truncated_gzip(self):
        d = _dest()
        archive = _write("trunc.tar.gz", b"\x1f\x8b\x08\x00 truncated garbage")
        with pytest.raises(UnsupportedArchiveError):
            extract_archive(archive, d)

    def test_corrupt_zip_central_directory(self):
        good = _zip_bytes({"main.py": "x = 1\n"})
        # Corrupt the end-of-central-directory region.
        archive = _write("corrupt.zip", good[:-8] + b"\x00\x00\x00\x00\x00\x00\x00\x00")
        d = _dest()
        with pytest.raises((UnsupportedArchiveError, UnsafeArchiveError)):
            extract_archive(archive, d)

    def test_garbage_with_gzip_magic_only(self):
        d = _dest()
        archive = _write("fake.tgz", b"\x1f\x8b not a real gzip stream")
        with pytest.raises(UnsupportedArchiveError):
            extract_archive(archive, d)


# --------------------------------------------------------------------------- #
# Extraction result shape
# --------------------------------------------------------------------------- #
class TestExtractionResult:
    """The returned file list and on-disk layout are correct and complete."""

    def test_preserves_nested_directories(self):
        d = _dest()
        archive = _write("n.tar.gz", _tar_bytes({"a/b/c/main.py": "x = 1\n"}))
        result = extract_archive(archive, d)
        assert os.path.exists(os.path.join(d, "a", "b", "c", "main.py"))
        assert os.path.join("a", "b", "c", "main.py") in result.file_names

    def test_includes_non_python_files(self):
        # Language detection runs on the returned names, so non-.py must be listed.
        d = _dest()
        archive = _write("mix.zip", _zip_bytes({"main.py": "x = 1\n", "README.md": "hi"}))
        result = extract_archive(archive, d)
        assert "main.py" in result.file_names
        assert "README.md" in result.file_names

    def test_returned_paths_are_relative(self):
        d = _dest()
        archive = _write("r.zip", _zip_bytes({"pkg/main.py": "x = 1\n"}))
        result = extract_archive(archive, d)
        assert all(not os.path.isabs(n) for n in result.file_names)

    def test_directory_only_members_excluded(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("emptydir/", "")
            zf.writestr("emptydir/main.py", "x = 1\n")
        d = _dest()
        archive = _write("dir.zip", buf.getvalue())
        result = extract_archive(archive, d)
        assert result.file_names == [os.path.join("emptydir", "main.py")]

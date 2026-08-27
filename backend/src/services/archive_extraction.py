"""Host-safe archive extraction (FR-001, FR-016; Constitution II).

Accepts zip and gzip-compressed tar archives (``.zip``, ``.tar.gz``, ``.tgz``,
``.tar``) and extracts them into a target directory while defending the host:

- Rejects members whose resolved path escapes the extraction directory
  (zip-slip / tar-slip via ``..`` or absolute paths).
- Rejects symlink / hardlink / device members (tar) which could point outside.
- Enforces a maximum member count and a maximum total uncompressed size to
  resist zip/tar bombs.

Detection is content-based (magic bytes) with an extension fallback, so a
correctly-formed archive is accepted regardless of the uploaded filename.
"""
from __future__ import annotations

import os
import tarfile
import zipfile
from dataclasses import dataclass

# Guards against archive bombs / abuse. Conservative for the Pi target.
MAX_MEMBERS = 10_000
MAX_TOTAL_UNCOMPRESSED_BYTES = 200 * 1024 * 1024  # 200 MiB


class UnsafeArchiveError(ValueError):
    """Raised when an archive member would escape the extraction dir or is unsafe."""


class UnsupportedArchiveError(ValueError):
    """Raised when the archive is not a supported/valid format."""


@dataclass(frozen=True)
class ExtractionResult:
    file_names: list[str]  # relative paths of extracted regular files


def extract_archive(archive_path: str, dest_dir: str) -> ExtractionResult:
    """Extract a supported archive into ``dest_dir`` safely.

    Raises UnsupportedArchiveError for unknown/corrupt formats and
    UnsafeArchiveError for members that would escape the destination.
    """
    if zipfile.is_zipfile(archive_path):
        return _extract_zip(archive_path, dest_dir)
    if tarfile.is_tarfile(archive_path):
        return _extract_tar(archive_path, dest_dir)
    raise UnsupportedArchiveError(
        "Unsupported or corrupted archive. Upload a .zip or .tar.gz of Python source."
    )


def _is_within(base: str, target: str) -> bool:
    base_abs = os.path.realpath(base)
    target_abs = os.path.realpath(target)
    return target_abs == base_abs or target_abs.startswith(base_abs + os.sep)


def _safe_member_path(dest_dir: str, name: str) -> str:
    if os.path.isabs(name) or name.startswith(("/", "\\")):
        raise UnsafeArchiveError(f"Absolute path in archive rejected: {name}")
    resolved = os.path.join(dest_dir, name)
    # Guard against traversal before touching the filesystem.
    normalized = os.path.normpath(resolved)
    if not _is_within(dest_dir, normalized):
        raise UnsafeArchiveError(f"Path traversal in archive rejected: {name}")
    return normalized


def _extract_zip(archive_path: str, dest_dir: str) -> ExtractionResult:
    names: list[str] = []
    try:
        with zipfile.ZipFile(archive_path) as zf:
            infos = [i for i in zf.infolist() if not i.is_dir()]
            if len(infos) > MAX_MEMBERS:
                raise UnsafeArchiveError("Archive has too many members.")
            total = 0
            for info in infos:
                total += info.file_size
                if total > MAX_TOTAL_UNCOMPRESSED_BYTES:
                    raise UnsafeArchiveError("Archive uncompressed size exceeds limit.")
                # Symlinks in zip are encoded in the high bits of external_attr.
                mode = (info.external_attr >> 16) & 0o170000
                if mode == 0o120000:
                    raise UnsafeArchiveError(f"Symlink in archive rejected: {info.filename}")
            for info in infos:
                target = _safe_member_path(dest_dir, info.filename)
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with zf.open(info) as src, open(target, "wb") as out:
                    out.write(src.read())
                names.append(os.path.relpath(target, dest_dir))
    except zipfile.BadZipFile as exc:
        raise UnsupportedArchiveError("Corrupted zip archive.") from exc
    return ExtractionResult(file_names=names)


def _extract_tar(archive_path: str, dest_dir: str) -> ExtractionResult:
    names: list[str] = []
    try:
        with tarfile.open(archive_path, mode="r:*") as tf:
            members = tf.getmembers()
            regular = [m for m in members if m.isfile()]
            if len(regular) > MAX_MEMBERS:
                raise UnsafeArchiveError("Archive has too many members.")
            total = 0
            for m in members:
                if m.issym() or m.islnk() or m.isdev():
                    raise UnsafeArchiveError(f"Unsafe archive member rejected: {m.name}")
                if m.isfile():
                    total += m.size
                    if total > MAX_TOTAL_UNCOMPRESSED_BYTES:
                        raise UnsafeArchiveError("Archive uncompressed size exceeds limit.")
                # Validate path safety for every member (files and dirs).
                _safe_member_path(dest_dir, m.name)
            for m in regular:
                target = _safe_member_path(dest_dir, m.name)
                os.makedirs(os.path.dirname(target), exist_ok=True)
                extracted = tf.extractfile(m)
                if extracted is None:
                    continue
                with extracted as src, open(target, "wb") as out:
                    out.write(src.read())
                names.append(os.path.relpath(target, dest_dir))
    except tarfile.TarError as exc:
        raise UnsupportedArchiveError("Corrupted tar archive.") from exc
    return ExtractionResult(file_names=names)

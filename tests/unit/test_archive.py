"""Unit tests for REQ002 — archive upload and extraction."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from agon.archive import extract_archive, upload_archive


# ---------------------------------------------------------------------------
# Correctness review
#   - We mock container-boundary calls (container_exec / container_exec_result)
#     because real LXC containers are not available in the test environment.
#   - Tests assert on return values (the remote path) not on mock call counts.
# ---------------------------------------------------------------------------


def test_upload_archive_returns_remote_path(mock_container: str, fake_archive: Path) -> None:
    """upload_archive shall return the full path inside the container."""
    with patch("agon.archive.container_exec") as mock_exec:
        mock_exec.return_value = None

        result = upload_archive(mock_container, fake_archive, "/home/ubuntu")

    assert result == "/home/ubuntu/project.tar.gz"


def test_extract_archive_tar_gz_returns_project_directory(mock_container: str) -> None:
    """Extracting a .tar.gz with a single top-level folder shall return that folder."""
    with (
        patch("agon.archive.container_exec") as mock_exec,
        patch("agon.archive.container_exec_result") as mock_result,
    ):
        mock_result.return_value = __import__("subprocess").CompletedProcess(
            args=[], returncode=0, stdout="project_dir\n", stderr=""
        )

        result = extract_archive(mock_container, "/tmp/project.tar.gz", "/tmp/extracted")

    assert result == "/tmp/extracted/project_dir"


def test_extract_archive_zip_returns_project_directory(mock_container: str) -> None:
    """Extracting a .zip with a single top-level folder shall return that folder."""
    with (
        patch("agon.archive.container_exec") as mock_exec,
        patch("agon.archive.container_exec_result") as mock_result,
    ):
        mock_result.return_value = __import__("subprocess").CompletedProcess(
            args=[], returncode=0, stdout="project_dir\n", stderr=""
        )

        result = extract_archive(mock_container, "/tmp/project.zip", "/tmp/extracted")

    assert result == "/tmp/extracted/project_dir"


def test_extract_archive_multiple_items_returns_extract_dir(mock_container: str) -> None:
    """When the archive contains multiple top-level items, return the extract root."""
    with (
        patch("agon.archive.container_exec") as mock_exec,
        patch("agon.archive.container_exec_result") as mock_result,
    ):
        mock_result.return_value = __import__("subprocess").CompletedProcess(
            args=[], returncode=0, stdout="file1\nfile2\n", stderr=""
        )

        result = extract_archive(mock_container, "/tmp/project.tar.gz", "/tmp/extracted")

    assert result == "/tmp/extracted"

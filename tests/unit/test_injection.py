"""Unit tests for REQ004 — test file injection without mutating the original archive."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from agon.injection import inject_files


# ---------------------------------------------------------------------------
# Correctness review
#   - We mock the container boundary (container_exec) because real containers
#     are unavailable in the test environment.
#   - Tests assert on the remote file paths, not on internal helper names.
# ---------------------------------------------------------------------------


def test_inject_files_after_extraction(mock_container: str) -> None:
    """inject_files with timing='post-extract' shall place auxiliary files into
    the extracted source tree without touching the original archive (REQ004)."""
    files = {"conftest.py": b"import pytest\n"}

    with patch("agon.injection.container_exec") as mock_exec:
        mock_exec.return_value = None

        inject_files(mock_container, files, "/tmp/project", timing="post-extract")

    written_path = mock_exec.call_args[0][1]
    assert "/tmp/project/conftest.py" in written_path


def test_inject_files_before_extraction(mock_container: str) -> None:
    """inject_files with timing='pre-extract' shall place files into the upload
    directory so they are present before the archive is extracted (REQ004)."""
    files = {"helper.sh": b"#!/bin/bash\necho ok\n"}

    with patch("agon.injection.container_exec") as mock_exec:
        mock_exec.return_value = None

        inject_files(mock_container, files, "/home/ubuntu/uploads", timing="pre-extract")

    written_path = mock_exec.call_args[0][1]
    assert "/home/ubuntu/uploads/helper.sh" in written_path


def test_inject_files_multiple_files(mock_container: str) -> None:
    """inject_files shall support injecting more than one file in a single call."""
    files = {"a.py": b"a", "b.py": b"b"}

    with patch("agon.injection.container_exec") as mock_exec:
        mock_exec.return_value = None

        inject_files(mock_container, files, "/tmp/project", timing="post-extract")

    assert mock_exec.call_count == 2

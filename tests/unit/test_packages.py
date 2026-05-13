"""Unit tests for REQ010 — automatic Debian package installation."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from agon.packages import ensure_packages


# ---------------------------------------------------------------------------
# Correctness review
#   - We mock container_exec_result (the boundary to the container) to simulate
#     dpkg checks, apt install, and verification.
#   - Tests assert on the boolean return value: True == success, False == failure.
# ---------------------------------------------------------------------------


def test_ensure_packages_installs_when_missing(mock_container: str) -> None:
    """When a package is not present, ensure_packages shall install it and return
    True on success (REQ010)."""
    with patch("agon.packages.container_exec_result") as mock_exec:
        mock_exec.side_effect = [
            subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr=""),  # dpkg check
            subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr=""),  # apt install
            subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr=""),  # verify
        ]

        result = ensure_packages(mock_container, ("pylint",))

    assert result is True


def test_ensure_packages_skips_when_already_installed(mock_container: str) -> None:
    """When a package is already present, ensure_packages shall skip installation."""
    with patch("agon.packages.container_exec_result") as mock_exec:
        mock_exec.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )  # dpkg says already installed

        result = ensure_packages(mock_container, ("python3",))

    assert result is True
    assert mock_exec.call_count == 1  # only the check


def test_ensure_packages_returns_false_on_install_failure(mock_container: str) -> None:
    """If apt install fails, ensure_packages shall return False so the caller can
    assign a zero grade (REQ010)."""
    with patch("agon.packages.container_exec_result") as mock_exec:
        mock_exec.side_effect = [
            subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr=""),  # dpkg check
            subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="apt error"
            ),  # install fails
        ]

        result = ensure_packages(mock_container, ("nonexistent-pkg",))

    assert result is False

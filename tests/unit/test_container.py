"""Unit tests for REQ001 and REQ012 — ephemeral container lifecycle."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from agon.container import ContainerManager


# ---------------------------------------------------------------------------
# Correctness review
#   - Container interactions are mocked at the subprocess boundary (lxc commands).
#   - Tests verify behaviour: launch returns a name, delete sends the right cmd,
#     exec returns captured output.
# ---------------------------------------------------------------------------


def test_container_manager_launch_returns_generated_name() -> None:
    """launch shall create a container and return its unique name."""
    with patch("agon.container.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )

        mgr = ContainerManager()
        name = mgr.launch("ubuntu:24.04")

    assert name.startswith("agon-")


def test_container_manager_delete_runs_lxc_delete() -> None:
    """delete shall invoke lxc delete --force for the given container."""
    with patch("agon.container.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )

        mgr = ContainerManager()
        mgr.delete("agon-abc123")

    call_args = mock_run.call_args[0][0]
    assert call_args == ["lxc", "delete", "--force", "agon-abc123"]


def test_container_manager_exec_returns_completed_process() -> None:
    """exec shall run a command inside the container and return captured output."""
    with patch("agon.container.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="hello world\n", stderr=""
        )

        mgr = ContainerManager()
        result = mgr.exec("agon-abc123", "echo hello world")

    assert result.returncode == 0
    assert result.stdout == "hello world\n"


def test_container_manager_upload_file_runs_lxc_file_push(mock_container: str) -> None:
    """upload_file shall push a local file into the container via lxc file push."""
    with patch("agon.container.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )

        mgr = ContainerManager()
        mgr.upload_file(mock_container, "/host/src.py", "/tmp/src.py")

    call_args = mock_run.call_args[0][0]
    assert call_args[0] == "lxc"
    assert call_args[1] == "file"
    assert call_args[2] == "push"

"""Shared pytest fixtures for the agon framework test suite."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_container() -> str:
    """Return a deterministic fake container name."""
    return "agon-test-container-1234"


@pytest.fixture
def fake_archive(tmp_path: Path) -> Path:
    """Create a fake archive file on disk and return its path."""
    archive = tmp_path / "project.tar.gz"
    archive.write_text("fake archive payload", encoding="utf-8")
    return archive


@pytest.fixture
def success_process() -> subprocess.CompletedProcess[str]:
    """Return a CompletedProcess representing a successful shell invocation."""
    return subprocess.CompletedProcess(args=[], returncode=0, stdout="ok\n", stderr="")


@pytest.fixture
def failure_process() -> subprocess.CompletedProcess[str]:
    """Return a CompletedProcess representing a failed shell invocation."""
    return subprocess.CompletedProcess(
        args=[], returncode=1, stdout="", stderr="something went wrong"
    )


@pytest.fixture
def mock_container_manager() -> MagicMock:
    """Return a pre-configured MagicMock stand-in for ContainerManager."""
    mgr = MagicMock()
    mgr.launch.return_value = "agon-test-container-1234"
    mgr.exec.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    )
    return mgr

"""Unit tests for REQ013, REQ014, REQ015, REQ016 — setup instruction detection,
execution, failure handling, and skip-setup flag.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from agon.setup import (
    SetupStep,
    execute_setup_steps,
    infer_steps,
    scan_source_tree,
)


# ---------------------------------------------------------------------------
# Correctness review
#   - scan_source_tree and infer_steps work on the local filesystem (host-side)
#     so they can be tested with tmp_path without mocking.
#   - execute_setup_steps mocks the container boundary.
#   - Every assertion is deterministic; no loops or conditionals in test bodies.
# ---------------------------------------------------------------------------


def test_scan_source_tree_detects_readme(tmp_path: Path) -> None:
    """scan_source_tree shall flag a README file as a setup instruction candidate."""
    (tmp_path / "README").write_text("Build with make", encoding="utf-8")
    files = scan_source_tree(str(tmp_path))
    assert any(f["filename"] == "README" for f in files)


def test_scan_source_tree_detects_requirements_txt(tmp_path: Path) -> None:
    """scan_source_tree shall flag requirements.txt."""
    (tmp_path / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    files = scan_source_tree(str(tmp_path))
    assert any(f["filename"] == "requirements.txt" for f in files)


def test_scan_source_tree_detects_makefile(tmp_path: Path) -> None:
    """scan_source_tree shall flag Makefile."""
    (tmp_path / "Makefile").write_text("build:\n\techo ok\n", encoding="utf-8")
    files = scan_source_tree(str(tmp_path))
    assert any(f["filename"] == "Makefile" for f in files)


def test_scan_source_tree_detects_pyproject_toml(tmp_path: Path) -> None:
    """scan_source_tree shall flag pyproject.toml."""
    (tmp_path / "pyproject.toml").write_text("[build-system]\n", encoding="utf-8")
    files = scan_source_tree(str(tmp_path))
    assert any(f["filename"] == "pyproject.toml" for f in files)


def test_infer_steps_orders_dependencies_before_build(tmp_path: Path) -> None:
    """infer_steps shall order dependency installation before compilation."""
    (tmp_path / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    (tmp_path / "Makefile").write_text("build:\n\techo ok\n", encoding="utf-8")

    steps = infer_steps(str(tmp_path))

    commands = [s.command for s in steps]
    install_idx = next(i for i, c in enumerate(commands) if "pip" in c or "requirements" in c)
    build_idx = next(i for i, c in enumerate(commands) if "make" in c)
    assert install_idx < build_idx


def test_execute_setup_steps_captures_output(mock_container: str) -> None:
    """execute_setup_steps shall run each step and capture stdout/stderr/returncode."""
    steps = [SetupStep(command="echo hello", description="Say hello")]

    with patch("agon.setup.container_exec_result") as mock_exec:
        mock_exec.return_value = __import__("subprocess").CompletedProcess(
            args=[], returncode=0, stdout="hello\n", stderr=""
        )

        outputs = execute_setup_steps(mock_container, steps)

    assert len(outputs) == 1
    assert outputs[0].returncode == 0
    assert outputs[0].stdout == "hello\n"
    assert outputs[0].stderr == ""


def test_execute_setup_steps_aborts_on_non_zero_exit(mock_container: str) -> None:
    """On the first non-zero exit code, execute_setup_steps shall stop and skip
    remaining steps (REQ015)."""
    steps = [
        SetupStep(command="false", description="Intentional failure"),
        SetupStep(command="echo skipped", description="Should not run"),
    ]

    with patch("agon.setup.container_exec_result") as mock_exec:
        mock_exec.return_value = __import__("subprocess").CompletedProcess(
            args=[], returncode=1, stdout="", stderr="boom"
        )

        outputs = execute_setup_steps(mock_container, steps)

    assert len(outputs) == 1
    assert outputs[0].returncode == 1
    assert mock_exec.call_count == 1


def test_execute_setup_steps_exposes_failure_in_summary(mock_container: str) -> None:
    """When a setup step fails, its captured output shall be available for the
    final summary (REQ014)."""
    steps = [SetupStep(command="bad-cmd", description="Bad command")]

    with patch("agon.setup.container_exec_result") as mock_exec:
        mock_exec.return_value = __import__("subprocess").CompletedProcess(
            args=[], returncode=127, stdout="", stderr="command not found"
        )

        outputs = execute_setup_steps(mock_container, steps)

    assert outputs[0].returncode == 127
    assert outputs[0].stderr == "command not found"


def test_skip_setup_flag_bypasses_execution(mock_container: str) -> None:
    """When skip_setup=True, execute_setup_steps shall return an empty list
    without invoking the container (REQ016)."""
    steps = [SetupStep(command="echo hello", description="Say hello")]

    with patch("agon.setup.container_exec_result") as mock_exec:
        outputs = execute_setup_steps(mock_container, steps, skip_setup=True)

    assert outputs == []
    mock_exec.assert_not_called()

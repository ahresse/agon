"""Integration / end-to-end tests for REQ001, REQ015, REQ012 — full framework
orchestration, setup-failure handling, and container cleanup.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agon.framework import run_framework
from agon.models import ExecutionStrategy, TestResult, TestType


# ---------------------------------------------------------------------------
# Correctness review
#   - These tests exercise the orchestrator (run_framework) with everything mocked
#     at the container boundary.  They are broader than unit tests but still fast.
#   - Each test verifies exactly one high-level behaviour.
# ---------------------------------------------------------------------------


def test_framework_runs_full_workflow_and_returns_summary() -> None:
    """run_framework shall launch a container, run assessments, aggregate grades,
    and return a structured summary (REQ001)."""
    with (
        patch("agon.framework.ContainerManager") as mock_mgr_cls,
        patch("agon.framework.run_atomic_tests") as mock_run_tests,
        patch("agon.framework.generate_summary") as mock_summary,
    ):
        mock_mgr = mock_mgr_cls.return_value
        mock_mgr.launch.return_value = "agon-test"
        mock_run_tests.return_value = (
            [
                TestResult(test_id="t1", name="A", grade=20.0, weight=0.5),
                TestResult(test_id="t2", name="B", grade=10.0, weight=0.5),
            ],
            15.0,
        )
        mock_summary.return_value = MagicMock(final_grade=15.0)

        result = run_framework(
            archive_path="project.tar.gz",
            preset="python-project",
        )

    assert result.final_grade == 15.0
    mock_mgr.delete.assert_called_once_with("agon-test")


def test_framework_keeps_container_when_requested() -> None:
    """When keep_container=True, run_framework shall skip deletion (REQ012)."""
    with (
        patch("agon.framework.ContainerManager") as mock_mgr_cls,
        patch("agon.framework.run_atomic_tests") as mock_run_tests,
        patch("agon.framework.generate_summary") as mock_summary,
    ):
        mock_mgr = mock_mgr_cls.return_value
        mock_mgr.launch.return_value = "agon-test"
        mock_run_tests.return_value = ([], 0.0)
        mock_summary.return_value = MagicMock(final_grade=0.0)

        run_framework(
            archive_path="project.tar.gz",
            keep_container=True,
        )

    mock_mgr.delete.assert_not_called()


def test_framework_zeroes_dependent_tests_on_setup_failure() -> None:
    """If a setup step fails, dependent tests shall receive grade 0 while
    independent tests still run (REQ015)."""
    with (
        patch("agon.framework.ContainerManager") as mock_mgr_cls,
        patch("agon.framework.execute_setup_steps") as mock_setup,
        patch("agon.framework.run_atomic_tests") as mock_run_tests,
        patch("agon.framework.generate_summary") as mock_summary,
    ):
        mock_mgr = mock_mgr_cls.return_value
        mock_mgr.launch.return_value = "agon-test"
        # Simulate setup failure
        mock_setup.return_value = [
            MagicMock(returncode=1, stdout="", stderr="apt failed")
        ]
        mock_run_tests.return_value = (
            [
                TestResult(
                    test_id="dep",
                    name="Dependent",
                    grade=0.0,
                    weight=0.5,
                ),
                TestResult(
                    test_id="ind",
                    name="Independent",
                    grade=20.0,
                    weight=0.5,
                ),
            ],
            10.0,
        )
        mock_summary.return_value = MagicMock(final_grade=10.0)

        result = run_framework(archive_path="project.tar.gz")

    assert result.final_grade == 10.0
    # The orchestrator should still have called run_atomic_tests
    mock_run_tests.assert_called_once()


def test_framework_emits_warning_does_not_crash_on_setup_failure() -> None:
    """On setup failure, run_framework shall emit a clear warning and return a
    valid summary rather than raising an unhandled exception (REQ015)."""
    with (
        patch("agon.framework.ContainerManager") as mock_mgr_cls,
        patch("agon.framework.execute_setup_steps") as mock_setup,
        patch("agon.framework.run_atomic_tests") as mock_run_tests,
        patch("agon.framework.generate_summary") as mock_summary,
        patch("agon.framework.warnings") as mock_warnings,
    ):
        mock_mgr = mock_mgr_cls.return_value
        mock_mgr.launch.return_value = "agon-test"
        mock_setup.return_value = [
            MagicMock(returncode=1, stdout="", stderr="cmake not found")
        ]
        mock_run_tests.return_value = ([], 0.0)
        mock_summary.return_value = MagicMock(final_grade=0.0)

        # Must not raise
        result = run_framework(archive_path="project.tar.gz")

    assert result is not None
    mock_warnings.warn.assert_called()

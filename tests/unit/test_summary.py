"""Unit tests for REQ008 — structured summary generation."""

from __future__ import annotations

import pytest

from agon.models import TestResult, TestType
from agon.summary import generate_summary


# ---------------------------------------------------------------------------
# Correctness review
#   - Tests assert on the shape and content of the returned Summary object.
#   - One concept per test: deterministic fields, agent-based fields, setup output
#     inclusion, and final grade propagation.
# ---------------------------------------------------------------------------


def test_summary_contains_deterministic_test_fields() -> None:
    """A deterministic test result shall appear in the summary with id, name,
    grade, weight, and exit_code (REQ008)."""
    results = [
        TestResult(
            test_id="test-001",
            name="Syntax check",
            grade=20.0,
            weight=0.5,
            exit_code=0,
            ai_reasoning=None,
        ),
    ]

    summary = generate_summary(results, final_grade=20.0)

    assert summary.final_grade == 20.0
    assert len(summary.results) == 1
    assert summary.results[0].test_id == "test-001"
    assert summary.results[0].name == "Syntax check"
    assert summary.results[0].exit_code == 0
    assert summary.results[0].ai_reasoning is None


def test_summary_contains_agent_based_fields() -> None:
    """An agent-based test result shall appear in the summary with AI reasoning
    (REQ008)."""
    results = [
        TestResult(
            test_id="test-002",
            name="Doc quality",
            grade=15.0,
            weight=0.5,
            exit_code=None,
            ai_reasoning="Good structure, could use more examples.",
        ),
    ]

    summary = generate_summary(results, final_grade=15.0)

    assert summary.results[0].exit_code is None
    assert summary.results[0].ai_reasoning == "Good structure, could use more examples."


def test_summary_exposes_setup_outputs() -> None:
    """The summary shall expose the setup phase stdout/stderr/returncode so that
    graders can account for setup failures (REQ008 + REQ014)."""
    setup_outputs = [
        {"command": "pip install -r requirements.txt", "returncode": 0, "stdout": "ok", "stderr": ""}
    ]

    summary = generate_summary([], final_grade=0.0, setup_outputs=setup_outputs)

    assert summary.setup_outputs == setup_outputs
    assert summary.setup_outputs[0]["returncode"] == 0


def test_summary_computes_final_weighted_grade() -> None:
    """The summary shall carry the pre-computed final weighted grade."""
    results = [
        TestResult(test_id="t1", name="A", grade=10.0, weight=0.5),
        TestResult(test_id="t2", name="B", grade=20.0, weight=0.5),
    ]

    summary = generate_summary(results, final_grade=15.0)

    assert summary.final_grade == 15.0


def test_summary_carries_grade_scale_maximum() -> None:
    """The summary shall expose the grade scale maximum used for the assessment (REQ029)."""
    summary = generate_summary([], final_grade=0.0, grade_scale_maximum=100.0)
    assert summary.grade_scale_maximum == 100.0

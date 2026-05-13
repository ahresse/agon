"""Unit tests for REQ005, REQ006, REQ007 — deterministic grading, agent-based
grading, and weighted aggregation.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from agon.grading import (
    aggregate_grades,
    evaluate_agent_based,
    evaluate_deterministic,
)
from agon.models import ExecutionData, TestResult, TestType


# ---------------------------------------------------------------------------
# Correctness review
#   - Deterministic tests: assert on the numeric score produced by an evaluator.
#   - Agent-based tests: mock the external AI boundary and assert on score + reasoning.
#   - Aggregation: pure function with no side effects; easy to verify.
# ---------------------------------------------------------------------------


def test_evaluate_deterministic_max_grade_on_zero_exit() -> None:
    """A deterministic evaluator shall be able to award the maximum score of 20
    when execution succeeds (REQ005)."""
    data = ExecutionData(stdout="", stderr="", returncode=0)
    evaluator = lambda e: 20.0  # noqa: E731

    score = evaluate_deterministic(data, evaluator)

    assert score == 20.0


def test_evaluate_deterministic_zero_grade_on_non_zero_exit() -> None:
    """A deterministic evaluator shall be able to award 0 when execution fails."""
    data = ExecutionData(stdout="", stderr="error", returncode=1)
    evaluator = lambda e: 0.0 if e.returncode != 0 else 20.0  # noqa: E731

    score = evaluate_deterministic(data, evaluator)

    assert score == 0.0


def test_evaluate_deterministic_score_clamped_to_zero_twenty() -> None:
    """The public evaluate_deterministic wrapper shall clamp the evaluator output
    to the [0, 20] interval (REQ005)."""
    data = ExecutionData(stdout="", stderr="", returncode=0)
    bad_evaluator = lambda e: 999.0  # noqa: E731

    score = evaluate_deterministic(data, bad_evaluator)

    assert score == 20.0


def test_evaluate_agent_based_returns_score_and_reasoning() -> None:
    """Agent-based grading shall return a numeric score in [0, 20] and a textual
    reasoning string (REQ006)."""
    with patch("agon.grading.call_ai_agent") as mock_agent:
        mock_agent.return_value = (18.5, "Well documented but lacks examples.")

        score, reasoning = evaluate_agent_based(
            prompt="Rate documentation clarity.",
            source_tree="# README\n\nShort but clear.",
        )

    assert 0 <= score <= 20
    assert score == 18.5
    assert reasoning == "Well documented but lacks examples."


def test_evaluate_agent_based_clamps_score() -> None:
    """If the AI agent returns an out-of-range score, it shall be clamped."""
    with patch("agon.grading.call_ai_agent") as mock_agent:
        mock_agent.return_value = (-5.0, "Too harsh.")

        score, _ = evaluate_agent_based(prompt="Rate.", source_tree="x")

    assert score == 0.0


def test_aggregate_grades_equal_weights() -> None:
    """aggregate_grades shall compute a simple weighted mean on the 0-20 scale
    when weights sum to 1.0 (REQ007)."""
    results = [
        TestResult(test_id="t1", name="A", grade=10.0, weight=0.5),
        TestResult(test_id="t2", name="B", grade=20.0, weight=0.5),
    ]

    final = aggregate_grades(results)

    assert final == 15.0


def test_aggregate_grades_unequal_weights() -> None:
    """aggregate_grades shall handle arbitrary positive weights."""
    results = [
        TestResult(test_id="t1", name="A", grade=20.0, weight=2.0),
        TestResult(test_id="t2", name="B", grade=10.0, weight=1.0),
    ]

    final = aggregate_grades(results)

    assert final == (20.0 * 2.0 + 10.0 * 1.0) / 3.0


def test_aggregate_grades_zero_results() -> None:
    """aggregate_grades shall return 0.0 when no results are supplied."""
    final = aggregate_grades([])
    assert final == 0.0


def test_aggregate_grades_is_public_utility() -> None:
    """aggregate_grades shall be importable as a top-level public symbol
    (REQ007 — "aggregation formula must be exposed as a public utility")."""
    import agon.grading

    assert hasattr(agon.grading, "aggregate_grades")
    assert callable(agon.grading.aggregate_grades)

"""Grading utilities for deterministic and agent-based tests."""

from __future__ import annotations

from agon.models import ExecutionData, TestResult


def evaluate_deterministic(
    execution_data: ExecutionData, evaluator, grade_scale_maximum: float = 20.0
) -> float:
    """Run an evaluator over captured execution data and clamp the score."""
    raw_score = evaluator(execution_data)
    return max(0.0, min(grade_scale_maximum, float(raw_score)))


def evaluate_agent_based(
    prompt: str, source_tree: str, grade_scale_maximum: float = 20.0
) -> tuple[float, str]:
    """Request an AI grade for *prompt* against *source_tree* and clamp."""
    from agon.llm import call_ai_agent

    score, reasoning = call_ai_agent(prompt, source_tree)
    return max(0.0, min(grade_scale_maximum, float(score))), reasoning


def aggregate_grades(test_results: list[TestResult]) -> float:
    """Compute the weighted mean grade on the 0–scale_max scale."""
    if not test_results:
        return 0.0
    weighted_sum = sum(r.grade * r.weight for r in test_results)
    total_weight = sum(r.weight for r in test_results)
    return weighted_sum / total_weight if total_weight else 0.0

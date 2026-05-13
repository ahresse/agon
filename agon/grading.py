"""Grading utilities for deterministic and agent-based tests."""

from __future__ import annotations

from agon.models import ExecutionData, TestResult


def evaluate_deterministic(execution_data: ExecutionData, evaluator) -> float:
    """Run an evaluator over captured execution data and clamp the score to [0, 20]."""
    raw_score = evaluator(execution_data)
    return max(0.0, min(20.0, raw_score))


def call_ai_agent(prompt: str, source_tree: str) -> tuple[float, str]:
    """Placeholder for an external AI grading agent."""
    raise NotImplementedError("call_ai_agent must be provided or mocked")


def evaluate_agent_based(prompt: str, source_tree: str) -> tuple[float, str]:
    """Request an AI grade for *prompt* against *source_tree* and clamp to [0, 20]."""
    score, reasoning = call_ai_agent(prompt, source_tree)
    return max(0.0, min(20.0, score)), reasoning


def aggregate_grades(test_results: list[TestResult]) -> float:
    """Compute the weighted mean grade on the 0–20 scale."""
    if not test_results:
        return 0.0
    weighted_sum = sum(r.grade * r.weight for r in test_results)
    total_weight = sum(r.weight for r in test_results)
    return weighted_sum / total_weight if total_weight else 0.0

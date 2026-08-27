"""Grading service (FR-006, FR-007, FR-010, FR-017).

Pure functions over already-computed test results. Contains no I/O and no
dependency on the ORM, so the weighted-mean logic is fully unit-testable and can
be re-run instantly on weight changes without re-executing any test.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResultInput:
    """A single test's contribution to a review's grade."""

    test_id: str
    grade: float  # 0-100; failed/timed-out tests pass 0 here (FR-007)
    weight: float  # effective weight (override else default)


class NoPositiveWeightError(ValueError):
    """Raised when no enabled test carries a positive weight (FR-017)."""


def effective_weight(default_weight: float, override: float | None) -> float:
    """Return the reviewer override if present, else the admin default (FR-009)."""
    return override if override is not None else default_weight


def weighted_mean(results: list[ResultInput]) -> float:
    """Compute the final grade as the weighted mean of test grades (FR-006).

    Failed tests still count (their grade is 0 with weight retained, FR-007).
    Raises NoPositiveWeightError if the total weight is not positive (FR-017).
    """
    total_weight = sum(r.weight for r in results)
    if total_weight <= 0:
        raise NoPositiveWeightError(
            "At least one enabled test must have a positive weight to compute a grade."
        )
    weighted_sum = sum(r.grade * r.weight for r in results)
    return weighted_sum / total_weight


def contribution(result: ResultInput, total_weight: float) -> float:
    """Portion of the final grade attributable to a single test result."""
    if total_weight <= 0:
        return 0.0
    return (result.grade * result.weight) / total_weight

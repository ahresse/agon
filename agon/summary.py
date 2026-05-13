"""Summary generation utilities."""

from __future__ import annotations

from agon.models import Summary, TestResult


def generate_summary(
    results: list[TestResult],
    final_grade: float,
    setup_outputs: list | None = None,
) -> Summary:
    """Build a structured summary from test results and setup phase data."""
    return Summary(
        results=results,
        final_grade=final_grade,
        setup_outputs=setup_outputs if setup_outputs is not None else [],
    )

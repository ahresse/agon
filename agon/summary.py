"""Summary generation utilities."""

from __future__ import annotations

from agon.models import Summary, TestResult


def generate_summary(
    results: list[TestResult],
    final_grade: float,
    setup_outputs: list | None = None,
    grade_scale_maximum: float = 20.0,
) -> Summary:
    """Build a structured summary from test results and setup phase data."""
    return Summary(
        results=results,
        final_grade=final_grade,
        grade_scale_maximum=grade_scale_maximum,
        setup_outputs=setup_outputs if setup_outputs is not None else [],
    )

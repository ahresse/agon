"""Review orchestration service (US1): scheduling + running + grading + persist.

Coordinates enabled tests for a review, executes each via a container runner with
failure isolation, persists TestResults, and computes the final weighted grade.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.models import Review, ReviewStatus, Test, TestResult
from src.models.enums import ResultStatus
from src.runners.container_runner import ContainerRunner
from src.runners.test_runner import run_single_test
from src.services.grading import NoPositiveWeightError, ResultInput, weighted_mean
from src.tests_plugins.registry import PluginInput, registry


def run_review(
    db: Session,
    review: Review,
    submission_path: str,
    runner: ContainerRunner,
    timeout_seconds: int,
) -> Review:
    """Execute all enabled tests for a review and persist the final grade."""
    review.status = ReviewStatus.RUNNING
    db.add(review)
    db.commit()

    enabled_tests = db.query(Test).filter(Test.enabled.is_(True)).all()
    result_inputs: list[ResultInput] = []
    any_success = False

    for test in enabled_tests:
        try:
            plugin = registry.create(test.key)
        except KeyError:
            continue
        payload = PluginInput(
            submission_path=submission_path,
            config={"theme": test.theme} if test.theme else {},
            timeout_seconds=timeout_seconds,
        )
        executed = run_single_test(runner, plugin, payload)
        if executed.status == ResultStatus.SUCCESS:
            any_success = True
        db.add(
            TestResult(
                review_id=review.id,
                test_id=test.id,
                grade=executed.grade,
                status=executed.status,
                pros=executed.pros,
                cons=executed.cons,
                ran_at=datetime.now(timezone.utc),
            )
        )
        result_inputs.append(
            ResultInput(test_id=test.id, grade=executed.grade, weight=test.default_weight)
        )

    try:
        review.final_grade = weighted_mean(result_inputs) if result_inputs else 0.0
    except NoPositiveWeightError:
        review.final_grade = 0.0

    review.status = ReviewStatus.COMPLETED if any_success else ReviewStatus.FAILED
    review.completed_at = datetime.now(timezone.utc)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review

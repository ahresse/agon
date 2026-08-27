"""Review progress + ETA computation (feature 006).

Pure, side-effect-free derivation of a running review's advancement from existing
data: the review's status, the count of enabled tests (total units of work), the
count of persisted test results (completed units — successes and failures alike),
and the elapsed time since the assessment started. No schema change; nothing is
stored.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.models import Job, Review, Test, TestResult
from src.models.enums import JobStatus, ReviewStatus

_TERMINAL = {ReviewStatus.COMPLETED, ReviewStatus.FAILED}


@dataclass(frozen=True)
class ReviewProgress:
    status: ReviewStatus
    total: int
    completed: int
    is_terminal: bool
    eta_seconds: int | None  # None => not yet estimable ("estimating…")

    @property
    def fraction(self) -> float:
        """Completed / total in 0.0–1.0; 1.0 when there is nothing to do."""
        if self.total <= 0:
            return 1.0
        return max(0.0, min(1.0, self.completed / self.total))

    @property
    def percent(self) -> int:
        return int(round(self.fraction * 100))


def compute_progress(
    total: int,
    completed: int,
    status: ReviewStatus,
    elapsed_seconds: float,
) -> ReviewProgress:
    """Pure core: derive progress + ETA from counts, status, and elapsed time.

    - Failed/timed-out tests count as completed (caller passes the total result
      count), so progress never stalls (FR-007).
    - ETA = max(0, (elapsed / completed) * remaining); None when no test has
      completed yet (=> "estimating…"); 0 when terminal (FR-004).
    """
    is_terminal = status in _TERMINAL
    completed = max(0, min(completed, total)) if total > 0 else completed

    if is_terminal:
        return ReviewProgress(status, total, total if total > 0 else completed, True, 0)

    remaining = max(0, total - completed)
    if completed <= 0:
        eta: int | None = None  # not yet estimable
    else:
        per_test = elapsed_seconds / completed
        eta = int(max(0.0, round(per_test * remaining)))
    return ReviewProgress(status, total, completed, False, eta)


def get_review_progress(db: Session, review: Review, now: datetime | None = None) -> ReviewProgress:
    """Assemble progress for a review from live database state."""
    now = now or datetime.now(timezone.utc)
    total = db.query(Test).filter(Test.enabled.is_(True)).count()
    completed = db.query(TestResult).filter(TestResult.review_id == review.id).count()
    elapsed = _elapsed_seconds(db, review, now)
    return compute_progress(total=total, completed=completed, status=review.status, elapsed_seconds=elapsed)


def _elapsed_seconds(db: Session, review: Review, now: datetime) -> float:
    """Seconds since the assessment started (job start, else review creation)."""
    start = None
    job = (
        db.query(Job)
        .filter(Job.review_id == review.id)
        .order_by(Job.created_at.asc())
        .first()
    )
    if job is not None and job.started_at is not None and job.status != JobStatus.PENDING:
        start = job.started_at
    if start is None:
        start = review.created_at
    if start is None:
        return 0.0
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    return max(0.0, (now - start).total_seconds())

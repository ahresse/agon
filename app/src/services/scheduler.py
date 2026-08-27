"""Scheduling service (T041, FR-003).

Enqueues the assessment work for a review onto the job queue. Enabled-test
selection happens inside the review run; the scheduler's responsibility is to
turn "assess this review" into a persisted, asynchronously-executed job so the
reviewer can leave the page and return for results.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from src.models import Job
from src.services.job_queue import JobQueue, queue


def schedule_review(
    db: Session,
    review_id: str,
    submission_path: str,
    job_queue: JobQueue | None = None,
) -> Job:
    """Enqueue a review assessment job. Returns the persisted Job row."""
    jq = job_queue or queue
    return jq.enqueue(db, review_id=review_id, submission_path=submission_path)

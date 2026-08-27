"""Unit tests for job queue status transitions (T072, FR-003)."""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("AGON_DATABASE_URL", "sqlite:///:memory:")

pytest.importorskip("sqlalchemy")

from src.db import SessionLocal, engine, init_db  # noqa: E402
from src.models import Base, Job, Review, Submission, User  # noqa: E402
from src.models.enums import JobStatus, Role  # noqa: E402
from src.services.job_queue import JobQueue  # noqa: E402


@pytest.fixture
def db():
    Base.metadata.drop_all(bind=engine)
    init_db()
    session = SessionLocal()
    yield session
    session.close()


def _make_review(db) -> Review:
    user = User(username="r", password_hash="x", role=Role.REVIEWER)
    db.add(user)
    db.flush()
    sub = Submission(
        candidate_label="c", detected_language="python", storage_path="/tmp/x", uploaded_by=user.id
    )
    db.add(sub)
    db.flush()
    review = Review(submission_id=sub.id, reviewer_id=user.id)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def test_enqueue_creates_pending_job(db):
    review = _make_review(db)
    q = JobQueue(executor=lambda s, j: None)
    job = q.enqueue(db, review.id, "/tmp/x")
    assert job.status == JobStatus.PENDING


def test_inline_run_completes_job(db):
    review = _make_review(db)
    q = JobQueue(executor=lambda s, j: None)
    q.enqueue(db, review.id, "/tmp/x")
    processed = q.run_pending_inline(db)
    assert processed == 1
    job = db.query(Job).first()
    assert job.status == JobStatus.COMPLETED
    assert job.started_at is not None and job.finished_at is not None


def test_failed_executor_marks_job_failed(db):
    review = _make_review(db)

    def boom(session, job):
        raise RuntimeError("kaboom")

    q = JobQueue(executor=boom)
    q.enqueue(db, review.id, "/tmp/x")
    q.run_pending_inline(db)
    job = db.query(Job).first()
    assert job.status == JobStatus.FAILED
    assert "kaboom" in (job.error or "")


def test_no_pending_jobs_processes_zero(db):
    q = JobQueue(executor=lambda s, j: None)
    assert q.run_pending_inline(db) == 0

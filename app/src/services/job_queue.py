"""In-process, SQLite-backed job queue with a worker pool (T021, FR-003).

Jobs (review runs) are persisted as rows with a status lifecycle
(PENDING -> RUNNING -> COMPLETED/FAILED). A pool of worker threads claims pending
jobs and executes them, letting the reviewer leave the page and return for
results (FR-003). No external broker is used, keeping the footprint minimal for
the Raspberry Pi target (Constitution Principle V).

The queue is deliberately simple and self-contained:
- `enqueue` persists a Job row and signals workers.
- Workers atomically claim a PENDING job (guarded by a lock over the single
  in-process queue) and run it to completion, updating status.
- `run_pending_inline` executes all pending jobs synchronously in the caller's
  thread; used in tests and environments where background threads are undesirable.
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy.orm import Session

from src.db import SessionLocal
from src.models import Job, Review
from src.models.enums import JobStatus
from src.runners.selection import get_runner
from src.services.review_service import run_review

logger = logging.getLogger("agon.job_queue")

# A job executor takes a DB session + the Job and runs the review to completion.
JobExecutor = Callable[[Session, Job], None]


def _default_executor(db: Session, job: Job) -> None:
    review = db.get(Review, job.review_id)
    if review is None:
        raise ValueError(f"Job {job.id} references missing review {job.review_id}")
    from src.config import settings

    run_review(db, review, job.submission_path, get_runner(), settings.test_timeout_seconds)


class JobQueue:
    def __init__(self, workers: int = 2, executor: JobExecutor | None = None) -> None:
        self._workers = workers
        self._executor = executor or _default_executor
        self._threads: list[threading.Thread] = []
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._claim_lock = threading.Lock()

    # -- enqueue -----------------------------------------------------------
    def enqueue(self, db: Session, review_id: str, submission_path: str) -> Job:
        job = Job(review_id=review_id, submission_path=submission_path, status=JobStatus.PENDING)
        db.add(job)
        db.commit()
        db.refresh(job)
        self._wake.set()
        return job

    # -- claiming ----------------------------------------------------------
    def _claim_next(self, db: Session) -> Job | None:
        """Atomically claim one PENDING job and mark it RUNNING."""
        with self._claim_lock:
            job = (
                db.query(Job)
                .filter(Job.status == JobStatus.PENDING)
                .order_by(Job.created_at.asc())
                .first()
            )
            if job is None:
                return None
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now(timezone.utc)
            db.add(job)
            db.commit()
            db.refresh(job)
            return job

    def _run_job(self, db: Session, job: Job) -> None:
        try:
            self._executor(db, job)
            job.status = JobStatus.COMPLETED
        except Exception as exc:  # noqa: BLE001 - record failure, keep worker alive
            logger.exception("Job %s failed", job.id)
            job.status = JobStatus.FAILED
            job.error = f"{type(exc).__name__}: {exc}"
        finally:
            job.finished_at = datetime.now(timezone.utc)
            db.add(job)
            db.commit()

    # -- synchronous drain (tests / inline mode) ---------------------------
    def run_pending_inline(self, db: Session) -> int:
        """Run all currently pending jobs synchronously. Returns count processed."""
        processed = 0
        while True:
            job = self._claim_next(db)
            if job is None:
                break
            self._run_job(db, job)
            processed += 1
        return processed

    # -- background worker pool --------------------------------------------
    def _worker_loop(self) -> None:
        db = SessionLocal()
        try:
            while not self._stop.is_set():
                job = self._claim_next(db)
                if job is None:
                    self._wake.wait(timeout=0.5)
                    self._wake.clear()
                    continue
                self._run_job(db, job)
        finally:
            db.close()

    def start(self) -> None:
        if self._threads:
            return
        self._stop.clear()
        for i in range(self._workers):
            t = threading.Thread(target=self._worker_loop, name=f"agon-worker-{i}", daemon=True)
            t.start()
            self._threads.append(t)
        logger.info("Started %d job-queue workers", self._workers)

    def stop(self) -> None:
        self._stop.set()
        self._wake.set()
        for t in self._threads:
            t.join(timeout=2.0)
        self._threads.clear()


# Module-level singleton used by the API layer.
queue = JobQueue()

"""Job model: a persisted unit of background work (T021, FR-003).

A Job represents an asynchronous review run. Persisting job state in the DB makes
progress observable and survives restarts, matching the in-process SQLite-backed
queue decision (research.md §4).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, IdMixin, TimestampMixin
from .enums import JobStatus


class Job(Base, IdMixin, TimestampMixin):
    __tablename__ = "jobs"

    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id"), nullable=False)
    submission_path: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus), nullable=False, default=JobStatus.PENDING
    )
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

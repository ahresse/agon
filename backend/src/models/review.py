"""Review model: one assessment of a Submission by a reviewer."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, IdMixin, TimestampMixin
from .enums import ReviewStatus


class Review(Base, IdMixin, TimestampMixin):
    __tablename__ = "reviews"

    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id"), nullable=False)
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[ReviewStatus] = mapped_column(
        SAEnum(ReviewStatus), nullable=False, default=ReviewStatus.PENDING
    )
    final_grade: Mapped[float | None] = mapped_column(Float, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

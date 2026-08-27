"""TestResult model: the outcome of one Test within a Review."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, IdMixin
from .enums import ResultStatus


class TestResult(Base, IdMixin):
    __tablename__ = "test_results"

    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id"), nullable=False)
    test_id: Mapped[str] = mapped_column(ForeignKey("tests.id"), nullable=False)
    grade: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[ResultStatus] = mapped_column(SAEnum(ResultStatus), nullable=False)
    pros: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    cons: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    ran_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

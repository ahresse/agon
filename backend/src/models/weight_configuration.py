"""WeightConfiguration model: per-review reviewer weight overrides (FR-009)."""
from __future__ import annotations

from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, IdMixin


class WeightConfiguration(Base, IdMixin):
    __tablename__ = "weight_configurations"

    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id"), nullable=False)
    test_id: Mapped[str] = mapped_column(ForeignKey("tests.id"), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)

"""Submission model: an uploaded candidate code package under assessment."""
from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, IdMixin, TimestampMixin


class Submission(Base, IdMixin, TimestampMixin):
    __tablename__ = "submissions"

    candidate_label: Mapped[str] = mapped_column(String, nullable=False)
    detected_language: Mapped[str] = mapped_column(String, nullable=False)
    storage_path: Mapped[str] = mapped_column(String, nullable=False)
    uploaded_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

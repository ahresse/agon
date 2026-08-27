"""Test model: a self-contained assessment plugin configured by admins."""
from __future__ import annotations

from sqlalchemy import Boolean, Enum as SAEnum, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, IdMixin
from .enums import TestType


class Test(Base, IdMixin):
    __tablename__ = "tests"

    key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[TestType] = mapped_column(SAEnum(TestType), nullable=False)
    theme: Mapped[str | None] = mapped_column(String, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    default_weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

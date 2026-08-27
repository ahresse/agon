"""Domain enumerations shared across the Agon backend."""
from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    REVIEWER = "REVIEWER"
    ADMIN = "ADMIN"


class TestType(str, Enum):
    METRIC = "METRIC"
    AI_AGENT = "AI_AGENT"


class ReviewStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ResultStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

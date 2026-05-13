"""Data models for the agon framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple


class ExecutionStrategy(Enum):
    """When an atomic test should run relative to archive extraction."""

    PRE_EXTRACT = "pre-extract"
    POST_EXTRACT = "post-extract"
    INDEPENDENT = "independent"


class TestType(Enum):
    """Classification of an atomic test."""

    DETERMINISTIC = "deterministic"
    AGENT_BASED = "agent_based"

    __test__ = False


@dataclass(frozen=True)
class AtomicTest:
    """Definition of a single assessable unit."""

    id: str
    name: str
    test_type: TestType
    command: Optional[str] = None
    grading_prompt: Optional[str] = None
    target_path: str = "."
    execution_strategy: ExecutionStrategy = ExecutionStrategy.POST_EXTRACT
    weight: float = 1.0
    required_debian_packages: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ExecutionData:
    """Captured output of a deterministic test run."""

    stdout: str
    stderr: str
    returncode: int


@dataclass
class TestResult:
    """Graded outcome for one atomic test."""

    __test__ = False

    test_id: str
    name: str
    grade: float
    weight: float
    exit_code: Optional[int] = None
    ai_reasoning: Optional[str] = None


@dataclass
class Summary:
    """Structured summary of a full assessment run."""

    results: list[TestResult]
    final_grade: float
    setup_outputs: list = field(default_factory=list)

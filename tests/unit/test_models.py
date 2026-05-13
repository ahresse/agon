"""Unit tests for REQ003 — atomic test definitions."""

from __future__ import annotations

import pytest

from agon.models import AtomicTest, ExecutionStrategy, TestType


# ---------------------------------------------------------------------------
# Correctness review
#   - Each test targets exactly one behaviour of the AtomicTest dataclass.
#   - Assertions are deterministic and use literal values.
#   - No logic (if/for/while) inside test bodies.
# ---------------------------------------------------------------------------


def test_atomic_test_exposes_all_required_fields() -> None:
    """An AtomicTest shall store every field mandated by REQ003."""
    # Arrange
    test = AtomicTest(
        id="test-001",
        name="Valid Python syntax",
        test_type=TestType.DETERMINISTIC,
        command="python3 -m py_compile *.py",
        grading_prompt=None,
        target_path=".",
        execution_strategy=ExecutionStrategy.POST_EXTRACT,
        weight=0.5,
        required_debian_packages=("python3",),
    )

    # Assert
    assert test.id == "test-001"
    assert test.name == "Valid Python syntax"
    assert test.test_type == TestType.DETERMINISTIC
    assert test.command == "python3 -m py_compile *.py"
    assert test.target_path == "."
    assert test.execution_strategy == ExecutionStrategy.POST_EXTRACT
    assert test.weight == 0.5
    assert test.required_debian_packages == ("python3",)


def test_atomic_test_default_weight_is_one() -> None:
    """When no weight is supplied, AtomicTest shall default to 1.0."""
    test = AtomicTest(
        id="test-002",
        name="Default weight check",
        test_type=TestType.DETERMINISTIC,
        command="true",
    )
    assert test.weight == 1.0


def test_atomic_test_agent_based_carries_grading_prompt() -> None:
    """Agent-based tests shall carry an AI grading prompt and no shell command."""
    test = AtomicTest(
        id="test-003",
        name="Comment quality",
        test_type=TestType.AGENT_BASED,
        grading_prompt="Rate comment quality from 0 to 20.",
        weight=0.3,
    )
    assert test.grading_prompt == "Rate comment quality from 0 to 20."
    assert test.command is None


def test_atomic_test_execution_strategy_pre_extract() -> None:
    """The execution strategy enum shall support pre-extract placement."""
    test = AtomicTest(
        id="test-004",
        name="Archive layout check",
        test_type=TestType.DETERMINISTIC,
        command="ls -R",
        execution_strategy=ExecutionStrategy.PRE_EXTRACT,
    )
    assert test.execution_strategy == ExecutionStrategy.PRE_EXTRACT


def test_atomic_test_execution_strategy_independent() -> None:
    """The execution strategy enum shall support independent placement."""
    test = AtomicTest(
        id="test-005",
        name="Standalone check",
        test_type=TestType.DETERMINISTIC,
        command="true",
        execution_strategy=ExecutionStrategy.INDEPENDENT,
    )
    assert test.execution_strategy == ExecutionStrategy.INDEPENDENT

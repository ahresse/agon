"""Test runner service: executes a plugin via a container runner with failure
isolation (FR-007). A crash or timeout yields grade 0 / FAILED; it never aborts
the surrounding review.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.models.enums import ResultStatus
from src.runners.container_runner import ContainerRunner
from src.tests_plugins.registry import PluginInput, TestPlugin


@dataclass(frozen=True)
class ExecutedResult:
    test_key: str
    grade: float
    status: ResultStatus
    pros: list[str]
    cons: list[str]


def run_single_test(
    runner: ContainerRunner,
    plugin: TestPlugin,
    payload: PluginInput,
) -> ExecutedResult:
    """Run one plugin, isolating any failure into a FAILED result with grade 0."""
    try:
        output = runner.run(plugin, payload)
        return ExecutedResult(
            test_key=plugin.key,
            grade=output.grade,
            status=ResultStatus.SUCCESS,
            pros=list(output.pros),
            cons=list(output.cons),
        )
    except Exception as exc:  # noqa: BLE001 - failure isolation is intentional (FR-007)
        return ExecutedResult(
            test_key=plugin.key,
            grade=0.0,
            status=ResultStatus.FAILED,
            pros=[],
            cons=[f"Test failed to complete: {type(exc).__name__}: {exc}"],
        )

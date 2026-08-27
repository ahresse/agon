"""Test runner service: executes a plugin via a container runner with failure
isolation (FR-007). A crash or timeout yields grade 0 / FAILED; it never aborts
the surrounding review.

Each result also carries an evidence `log` (feature 004): for a passing test the
plugin's focused findings excerpt; for a failure a sanitized reason followed by
the raw error output.
"""
from __future__ import annotations

import traceback
from dataclasses import dataclass

from src.models.enums import ResultStatus
from src.runners.container_runner import ContainerRunner
from src.tests_plugins.registry import PluginInput, TestPlugin, truncate_log


@dataclass(frozen=True)
class ExecutedResult:
    test_key: str
    grade: float
    status: ResultStatus
    pros: list[str]
    cons: list[str]
    log: str = ""


def run_single_test(
    runner: ContainerRunner,
    plugin: TestPlugin,
    payload: PluginInput,
) -> ExecutedResult:
    """Run one plugin, isolating any failure into a FAILED result with grade 0."""
    try:
        output = runner.run(plugin, payload)
        pros = list(output.pros)
        cons = list(output.cons)
        log = getattr(output, "log", "") or ""
        if not log:
            # Default evidence log: a readable summary of the plugin's findings so
            # the reviewer always has something to inspect (feature 004).
            log = _log_from_findings(pros, cons)
        return ExecutedResult(
            test_key=plugin.key,
            grade=output.grade,
            status=ResultStatus.SUCCESS,
            pros=pros,
            cons=cons,
            log=truncate_log(log),
        )
    except Exception as exc:  # noqa: BLE001 - failure isolation is intentional (FR-007)
        reason = f"{type(exc).__name__}: {exc}"
        raw = traceback.format_exc()
        failure_log = f"Test failed to complete: {reason}\n\n--- details ---\n{raw}"
        return ExecutedResult(
            test_key=plugin.key,
            grade=0.0,
            status=ResultStatus.FAILED,
            pros=[],
            cons=[f"Test failed to complete: {reason}"],
            log=truncate_log(failure_log),
        )


def _log_from_findings(pros: list[str], cons: list[str]) -> str:
    """Compose a readable evidence log from a plugin's structured findings."""
    lines: list[str] = []
    if pros:
        lines.append("Positive findings:")
        lines.extend(f"  + {p}" for p in pros)
    if cons:
        if lines:
            lines.append("")
        lines.append("Issues found:")
        lines.extend(f"  - {c}" for c in cons)
    return "\n".join(lines)

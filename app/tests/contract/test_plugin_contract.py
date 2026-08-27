"""Contract test: test plugin conformance (Constitution Principle III, II).

Verifies grade bounds, timeout/crash → FAILED with grade 0 (FR-007), and that
execution goes through a container runner boundary.
"""
import pytest

from src.models.enums import ResultStatus
from src.runners.container_runner import LocalSubprocessRunner
from src.runners.test_runner import run_single_test
from src.tests_plugins.registry import PluginInput, PluginOutput


class _GoodPlugin:
    key = "test.good"

    def run(self, payload: PluginInput) -> PluginOutput:
        return PluginOutput(grade=87.5, pros=["clean"], cons=[])


class _CrashingPlugin:
    key = "test.crash"

    def run(self, payload: PluginInput) -> PluginOutput:
        raise RuntimeError("boom")


def test_grade_out_of_range_rejected():
    with pytest.raises(ValueError):
        PluginOutput(grade=120.0)


def test_successful_plugin_result():
    runner = LocalSubprocessRunner()
    result = run_single_test(runner, _GoodPlugin(), PluginInput(submission_path="/x"))
    assert result.status == ResultStatus.SUCCESS
    assert result.grade == 87.5
    assert "clean" in result.pros


def test_crashing_plugin_is_isolated():
    runner = LocalSubprocessRunner()
    result = run_single_test(runner, _CrashingPlugin(), PluginInput(submission_path="/x"))
    assert result.status == ResultStatus.FAILED
    assert result.grade == 0.0
    assert result.cons  # failure reason recorded

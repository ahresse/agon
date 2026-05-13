"""Unit tests for plugin loading, validation, and evaluators.

Covers REQ017–REQ027, REQ032.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from agon.models import AtomicTest, ExecutionStrategy, TestType
from agon.plugins import (
    PluginLoadError,
    PluginLoader,
    PluginRegistry,
    run_custom_evaluator,
    run_regex_evaluator,
    run_script_evaluator,
)


def _make_plugin(
    atomic_tests: list[dict] | None = None,
    presets: list[dict] | None = None,
    version: str = "1.0",
) -> dict:
    return {
        "version": version,
        "atomic_tests": atomic_tests or [],
        "presets": presets or [],
    }


# ----------------------------------------------------------------------
# PluginLoader — schema version
# ----------------------------------------------------------------------


def test_plugin_loader_rejects_missing_version(tmp_path: Path) -> None:
    """Plugin loader shall reject a file without a version field (REQ024)."""
    plugin_file = tmp_path / "plugin.yaml"
    plugin_file.write_text(yaml.dump({"atomic_tests": []}), encoding="utf-8")
    loader = PluginLoader()
    with pytest.raises(PluginLoadError):
        loader.load_plugin(plugin_file)


def test_plugin_loader_rejects_unsupported_version(tmp_path: Path) -> None:
    """Plugin loader shall reject an unsupported version (REQ024)."""
    plugin_file = tmp_path / "plugin.yaml"
    plugin_file.write_text(yaml.dump(_make_plugin(version="9.9")), encoding="utf-8")
    loader = PluginLoader()
    with pytest.raises(PluginLoadError):
        loader.load_plugin(plugin_file)


# ----------------------------------------------------------------------
# PluginLoader — mandatory fields (REQ027)
# ----------------------------------------------------------------------


def test_plugin_loader_skips_test_missing_mandatory_field(tmp_path: Path) -> None:
    """A test missing a mandatory field shall be skipped (REQ027)."""
    plugin_file = tmp_path / "plugin.yaml"
    plugin_file.write_text(
        yaml.dump(
            _make_plugin(
                atomic_tests=[
                    {"id": "bad", "name": "Bad", "test_type": "deterministic"}
                ]
            )
        ),
        encoding="utf-8",
    )
    loader = PluginLoader()
    result = loader.load_plugin(plugin_file)
    assert result.atomic_tests == []


def test_plugin_loader_accepts_complete_test(tmp_path: Path) -> None:
    """A test with all mandatory fields shall be loaded (REQ027)."""
    plugin_file = tmp_path / "plugin.yaml"
    plugin_file.write_text(
        yaml.dump(
            _make_plugin(
                atomic_tests=[
                    {
                        "id": "good",
                        "name": "Good",
                        "test_type": "deterministic",
                        "target_path": ".",
                        "execution_strategy": "post_extract",
                        "weight": 1.0,
                    }
                ]
            )
        ),
        encoding="utf-8",
    )
    loader = PluginLoader()
    result = loader.load_plugin(plugin_file)
    assert len(result.atomic_tests) == 1
    assert result.atomic_tests[0].id == "good"


# ----------------------------------------------------------------------
# PluginLoader — custom evaluator (REQ032)
# ----------------------------------------------------------------------


def test_plugin_loader_rejects_custom_evaluator_without_source(tmp_path: Path) -> None:
    """A custom evaluator without a source field shall be rejected (REQ032)."""
    plugin_file = tmp_path / "plugin.yaml"
    plugin_file.write_text(
        yaml.dump(
            _make_plugin(
                atomic_tests=[
                    {
                        "id": "custom",
                        "name": "Custom",
                        "test_type": "deterministic",
                        "target_path": ".",
                        "execution_strategy": "post_extract",
                        "weight": 1.0,
                        "command": "true",
                        "evaluator": {"type": "custom"},
                    }
                ]
            )
        ),
        encoding="utf-8",
    )
    loader = PluginLoader()
    result = loader.load_plugin(plugin_file)
    assert result.atomic_tests == []


def test_plugin_loader_rejects_custom_evaluator_with_bad_signature(tmp_path: Path) -> None:
    """A custom evaluator with the wrong signature shall be rejected (REQ032)."""
    plugin_file = tmp_path / "plugin.yaml"
    plugin_file.write_text(
        yaml.dump(
            _make_plugin(
                atomic_tests=[
                    {
                        "id": "custom",
                        "name": "Custom",
                        "test_type": "deterministic",
                        "target_path": ".",
                        "execution_strategy": "post_extract",
                        "weight": 1.0,
                        "command": "true",
                        "evaluator": {
                            "type": "custom",
                            "source": "def evaluate(x, y): return 0.0",
                        },
                    }
                ]
            )
        ),
        encoding="utf-8",
    )
    loader = PluginLoader()
    result = loader.load_plugin(plugin_file)
    assert result.atomic_tests == []


def test_plugin_loader_accepts_custom_evaluator_with_valid_signature(tmp_path: Path) -> None:
    """A custom evaluator with a valid signature shall be accepted (REQ032)."""
    plugin_file = tmp_path / "plugin.yaml"
    plugin_file.write_text(
        yaml.dump(
            _make_plugin(
                atomic_tests=[
                    {
                        "id": "custom",
                        "name": "Custom",
                        "test_type": "deterministic",
                        "target_path": ".",
                        "execution_strategy": "post_extract",
                        "weight": 1.0,
                        "command": "true",
                        "evaluator": {
                            "type": "custom",
                            "source": "def evaluate(exit_code, stdout, stderr):\n    return 20.0 if exit_code == 0 else 0.0",
                        },
                    }
                ]
            )
        ),
        encoding="utf-8",
    )
    loader = PluginLoader()
    result = loader.load_plugin(plugin_file)
    assert len(result.atomic_tests) == 1
    assert result.atomic_tests[0].evaluator is not None
    assert result.atomic_tests[0].evaluator["type"] == "custom"


# ----------------------------------------------------------------------
# Custom evaluator runtime
# ----------------------------------------------------------------------


def test_run_custom_evaluator_returns_expected_grade() -> None:
    """run_custom_evaluator shall execute the plugin source and return the grade."""
    evaluator = {
        "source": "def evaluate(exit_code, stdout, stderr):\n    return 15.0 if exit_code == 0 else 5.0"
    }
    grade = run_custom_evaluator(evaluator, exit_code=0, stdout="", stderr="")
    assert grade == 15.0


def test_run_custom_evaluator_clamps_to_maximum() -> None:
    """run_custom_evaluator shall clamp the result to [0, grade_scale_maximum]."""
    evaluator = {
        "source": "def evaluate(exit_code, stdout, stderr):\n    return 999.0"
    }
    grade = run_custom_evaluator(
        evaluator, exit_code=0, stdout="", stderr="", grade_scale_maximum=10.0
    )
    assert grade == 10.0


def test_run_custom_evaluator_blocks_disallowed_import() -> None:
    """run_custom_evaluator shall block imports of disallowed modules."""
    evaluator = {
        "source": "import os\ndef evaluate(exit_code, stdout, stderr):\n    return 0.0"
    }
    grade = run_custom_evaluator(evaluator, exit_code=0, stdout="", stderr="")
    assert grade == 0.0


def test_run_custom_evaluator_allows_safe_imports() -> None:
    """run_custom_evaluator shall permit imports of safe modules like re and math."""
    evaluator = {
        "source": "import re, math\ndef evaluate(exit_code, stdout, stderr):\n    return math.sqrt(16.0)"
    }
    grade = run_custom_evaluator(evaluator, exit_code=0, stdout="", stderr="")
    assert grade == 4.0


# ----------------------------------------------------------------------
# Regex evaluator
# ----------------------------------------------------------------------


def test_run_regex_evaluator_clamps_to_configurable_maximum() -> None:
    """run_regex_evaluator shall clamp the score to [0, grade_scale_maximum] (REQ029)."""
    from unittest.mock import MagicMock, patch

    fake_proc = MagicMock()
    fake_proc.stdout = "30.0\n"
    fake_proc.stderr = ""
    fake_proc.returncode = 0

    with patch("agon.plugins.container_exec_result", return_value=fake_proc):
        grade = run_regex_evaluator(
            "c",
            "/tmp/src",
            {"pattern": "x", "score_on_no_match": 30.0},
            grade_scale_maximum=10.0,
        )
    assert grade == 10.0


# ----------------------------------------------------------------------
# Script evaluator
# ----------------------------------------------------------------------


def test_run_script_evaluator_clamps_to_configurable_maximum() -> None:
    """run_script_evaluator shall clamp the score to [0, grade_scale_maximum] (REQ029)."""
    from unittest.mock import MagicMock, patch

    fake_proc = MagicMock()
    fake_proc.stdout = ""
    fake_proc.stderr = ""
    fake_proc.returncode = 0

    with patch("agon.plugins.container_exec_result", return_value=fake_proc):
        test = AtomicTest(
            id="t",
            name="T",
            test_type=TestType.DETERMINISTIC,
            command="true",
            evaluator={"type": "script", "grade_on_zero_exit": 30.0},
        )
        grade = run_script_evaluator("c", "/tmp/src", test, grade_scale_maximum=10.0)
    assert grade == 10.0


# ----------------------------------------------------------------------
# PluginRegistry
# ----------------------------------------------------------------------


def test_registry_loads_multiple_plugins_and_deduplicates_tests(tmp_path: Path) -> None:
    """PluginRegistry shall deduplicate atomic tests by id across plugins."""
    p1 = tmp_path / "a.yaml"
    p2 = tmp_path / "b.yaml"
    p1.write_text(
        yaml.dump(
            _make_plugin(
                atomic_tests=[
                    {
                        "id": "shared",
                        "name": "Shared A",
                        "test_type": "deterministic",
                        "target_path": ".",
                        "execution_strategy": "post_extract",
                        "weight": 1.0,
                    }
                ]
            )
        ),
        encoding="utf-8",
    )
    p2.write_text(
        yaml.dump(
            _make_plugin(
                atomic_tests=[
                    {
                        "id": "shared",
                        "name": "Shared B",
                        "test_type": "deterministic",
                        "target_path": ".",
                        "execution_strategy": "post_extract",
                        "weight": 2.0,
                    }
                ]
            )
        ),
        encoding="utf-8",
    )
    registry = PluginRegistry()
    registry.load_plugins([p1, p2])
    assert registry.atomic_tests["shared"].name == "Shared B"  # last one wins

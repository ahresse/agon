"""Unit tests for REQ009 — named test-suite presets."""

from __future__ import annotations

import pytest

from agon.models import AtomicTest, TestType
from agon.presets import PRESETS, TestSuitePreset, load_preset


# ---------------------------------------------------------------------------
# Correctness review
#   - Tests verify that presets bundle AtomicTest instances with positive weights.
#   - We assert on registry contents and on the shape of the returned preset object.
# ---------------------------------------------------------------------------


def test_load_preset_returns_preset_object() -> None:
    """load_preset shall return a TestSuitePreset for a known name (REQ009)."""
    preset = load_preset("python-project")
    assert isinstance(preset, TestSuitePreset)


def test_python_project_preset_has_tests() -> None:
    """The 'python-project' preset shall contain at least one AtomicTest."""
    preset = load_preset("python-project")
    assert len(preset.tests) > 0
    assert isinstance(preset.tests[0], AtomicTest)


def test_preset_tests_have_positive_weights() -> None:
    """Every test inside a preset shall carry a strictly positive weight."""
    preset = load_preset("python-project")
    for test in preset.tests:
        assert test.weight > 0.0


def test_preset_registry_contains_python_project() -> None:
    """PRESETS shall expose a 'python-project' entry."""
    assert "python-project" in PRESETS


def test_preset_registry_contains_c_project() -> None:
    """PRESETS shall expose a 'c-project' entry."""
    assert "c-project" in PRESETS


def test_preset_registry_contains_documentation_heavy() -> None:
    """PRESETS shall expose a 'documentation-heavy' entry."""
    assert "documentation-heavy" in PRESETS


def test_load_preset_unknown_name_raises() -> None:
    """load_preset shall raise KeyError (or a domain-specific exception) when the
    preset name is not registered."""
    with pytest.raises((KeyError, LookupError)):
        load_preset("nonexistent-preset")

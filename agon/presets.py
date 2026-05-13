"""Named test-suite presets."""

from __future__ import annotations

from dataclasses import dataclass

from agon.models import AtomicTest, ExecutionStrategy, TestType


@dataclass
class TestSuitePreset:
    """A named collection of atomic tests with default weights."""

    __test__ = False

    name: str
    tests: list[AtomicTest]


PRESETS: dict[str, TestSuitePreset] = {
    "python-project": TestSuitePreset(
        name="python-project",
        tests=[
            AtomicTest(
                id="py-001",
                name="Python syntax check",
                test_type=TestType.DETERMINISTIC,
                command="python3 -m py_compile *.py",
                weight=0.3,
                required_debian_packages=("python3",),
            ),
            AtomicTest(
                id="py-002",
                name="Pylint score",
                test_type=TestType.DETERMINISTIC,
                command="pylint .",
                weight=0.4,
                required_debian_packages=("pylint",),
            ),
            AtomicTest(
                id="py-003",
                name="Flake8 check",
                test_type=TestType.DETERMINISTIC,
                command="flake8 .",
                weight=0.3,
                required_debian_packages=("flake8",),
            ),
        ],
    ),
    "c-project": TestSuitePreset(
        name="c-project",
        tests=[
            AtomicTest(
                id="c-001",
                name="Build with make",
                test_type=TestType.DETERMINISTIC,
                command="make",
                weight=0.5,
                required_debian_packages=("build-essential",),
            ),
            AtomicTest(
                id="c-002",
                name="Run tests",
                test_type=TestType.DETERMINISTIC,
                command="make test",
                weight=0.5,
            ),
        ],
    ),
    "documentation-heavy": TestSuitePreset(
        name="documentation-heavy",
        tests=[
            AtomicTest(
                id="doc-001",
                name="README presence",
                test_type=TestType.DETERMINISTIC,
                command="test -f README.md || test -f README",
                weight=0.3,
            ),
            AtomicTest(
                id="doc-002",
                name="Documentation clarity",
                test_type=TestType.AGENT_BASED,
                grading_prompt="Rate the clarity and completeness of the documentation from 0 to 20.",
                weight=0.7,
            ),
        ],
    ),
}


def load_preset(
    name: str, registry=None
) -> TestSuitePreset:
    """Retrieve a preset by name.

    If *registry* is provided (a ``PluginRegistry``), plugin-defined presets
    are checked before the built-in registry.
    """
    if registry is not None and name in registry.presets:
        return registry.presets[name]
    if name not in PRESETS:
        raise KeyError(f"Unknown preset: {name}")
    return PRESETS[name]

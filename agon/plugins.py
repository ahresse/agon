"""Plugin discovery, validation, and loading for agon.

A plugin is a single YAML file that defines atomic tests and/or test-suite
presets.  The loader validates schema version, mandatory fields, and file-size
limits, then returns structured ``AtomicTest`` and ``TestSuitePreset`` objects.

Plugin format (version 1.0)
---------------------------

.. code-block:: yaml

    version: "1.0"
    atomic_tests:
      - id: "no-todos"
        name: "No TODOs in source"
        test_type: "deterministic"
        target_path: "."
        execution_strategy: "post_extract"
        weight: 0.5
        evaluator:
          type: "regex"
          pattern: "TODO|FIXME|XXX"
          target_file: "*.py"
          score_on_match: 0.0
          score_on_no_match: 20.0

      - id: "custom-lint"
        name: "Custom linter"
        test_type: "deterministic"
        target_path: "."
        execution_strategy: "post_extract"
        weight: 0.5
        required_debian_packages: ["python3"]
        command: "python3 lint.py"
        evaluator:
          type: "script"
          grade_on_zero_exit: 20.0
          grade_on_non_zero_exit: 0.0

      - id: "doc-quality"
        name: "Documentation quality"
        test_type: "agent_based"
        target_path: "."
        execution_strategy: "post_extract"
        weight: 0.5
        grading_prompt: "Rate the documentation clarity from 0 to 20."

      - id: "custom-eval"
        name: "Custom evaluator test"
        test_type: "deterministic"
        target_path: "."
        execution_strategy: "post_extract"
        weight: 0.5
        command: "echo hello"
        evaluator:
          type: "custom"
          source: |
            def evaluate(exit_code, stdout, stderr):
                return 20.0 if exit_code == 0 else 0.0

    presets:
      - name: "my-preset"
        tests:
          - id: "no-todos"
            weight: 0.5
          - id: "custom-lint"
            weight: 0.5
"""

from __future__ import annotations

import ast
import json
import logging
import math
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import yaml

from agon.container import container_exec_result
from agon.models import AtomicTest, ExecutionStrategy, TestType
from agon.presets import TestSuitePreset

_LOGGER = logging.getLogger(__name__)

SUPPORTED_PLUGIN_VERSIONS = {"1.0"}
MAX_PLUGIN_FILE_SIZE = 1 * 1024 * 1024  # 1 MiB  (REQ026 guardrail)
REGEX_EVAL_TIMEOUT = 5  # seconds per regex execution (REQ021 guardrail)
SCRIPT_EVAL_TIMEOUT = 300  # seconds per script execution (REQ022 guardrail)
CUSTOM_EVAL_TIMEOUT = 30  # seconds per custom evaluator call (REQ032 guardrail)
MAX_AGENT_CONTEXT = 128 * 1024  # 128 KiB excerpt cap (REQ023 guardrail)


class PluginLoadError(Exception):
    """Raised when a plugin file fails validation or parsing."""

    def __init__(self, message: str, source_path: Path | None = None) -> None:
        self.message = message
        self.source_path = source_path
        super().__init__(message)


@dataclass
class PluginDefinition:
    """Structured representation of a loaded plugin."""

    version: str
    source_path: Path
    atomic_tests: list[AtomicTest] = field(default_factory=list)
    presets: list[TestSuitePreset] = field(default_factory=list)


# ----------------------------------------------------------------------
# Restricted evaluator context helpers
# ----------------------------------------------------------------------

_ALLOWED_EVAL_MODULES = {"re", "math", "json", "statistics"}


def _make_restricted_import() -> Any:
    """Return a restricted ``__import__`` that whitelists safe modules."""

    def _restricted_import(name: str, *args: Any, **kwargs: Any) -> Any:
        base = name.split(".")[0]
        if base not in _ALLOWED_EVAL_MODULES:
            raise ImportError(f"Import of {name} is not allowed in evaluator context")
        return __builtins__.__import__(name, *args, **kwargs)

    return _restricted_import


def _make_restricted_globals() -> dict[str, Any]:
    """Build a restricted globals dictionary for evaluator execution."""
    return {
        "__builtins__": {
            "True": True,
            "False": False,
            "None": None,
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "range": range,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "abs": abs,
            "min": min,
            "max": max,
            "sum": sum,
            "round": round,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "__import__": _make_restricted_import(),
        }
    }


def _validate_custom_evaluator(evaluator: dict, path: Path, test_id: str) -> None:
    """Validate a custom evaluator at plugin load time using AST (REQ032)."""
    source = evaluator.get("source")
    if not isinstance(source, str) or not source.strip():
        raise PluginLoadError(
            f"Custom evaluator for test {test_id} must contain a non-empty string 'source' field",
            path,
        )

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise PluginLoadError(
            f"Custom evaluator for test {test_id} contains invalid Python: {exc}",
            path,
        ) from exc

    evaluate_node = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "evaluate":
            evaluate_node = node
            break

    if evaluate_node is None:
        raise PluginLoadError(
            f"Custom evaluator for test {test_id} must define a function named 'evaluate'",
            path,
        )

    args = evaluate_node.args
    num_args = len(args.posonlyargs) + len(args.args)
    has_vararg = args.vararg is not None
    has_kwarg = args.kwarg is not None

    if has_vararg or has_kwarg:
        if num_args < 3:
            raise PluginLoadError(
                f"Custom evaluator 'evaluate' for test {test_id} must accept at least "
                f"3 positional arguments, got {num_args}",
                path,
            )
    else:
        if num_args != 3:
            raise PluginLoadError(
                f"Custom evaluator 'evaluate' for test {test_id} must accept exactly "
                f"3 positional arguments (exit_code, stdout, stderr), got {num_args}",
                path,
            )


class PluginLoader:
    """Load and validate agon plugin files (single-file YAML)."""

    def load_plugin(self, path: Path | str) -> PluginDefinition:
        """Load a plugin from *path* and return its definitions.

        Raises ``PluginLoadError`` when the file fails validation.
        """
        p = Path(path)
        self._validate_path(p)
        raw = self._read_file(p)
        data = self._parse_yaml(raw, p)
        self._validate_schema(data, p)
        return self._convert(data, p)

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def _validate_path(self, path: Path) -> None:
        """Ensure *path* is a single file (REQ018)."""
        if not path.exists():
            raise PluginLoadError(f"Plugin file not found: {path}", path)
        if not path.is_file():
            raise PluginLoadError(
                f"Plugin must be a single file, not a directory: {path}", path
            )

    def _read_file(self, path: Path) -> str:
        """Read plugin file contents with size guardrail (REQ026)."""
        size = path.stat().st_size
        if size > MAX_PLUGIN_FILE_SIZE:
            raise PluginLoadError(
                f"Plugin file exceeds size limit ({MAX_PLUGIN_FILE_SIZE} bytes): {size}",
                path,
            )
        return path.read_text(encoding="utf-8")

    def _parse_yaml(self, raw: str, path: Path) -> dict[str, Any]:
        """Parse raw YAML into a dictionary."""
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            raise PluginLoadError(f"Invalid YAML syntax: {exc}", path) from exc
        if not isinstance(data, dict):
            raise PluginLoadError("Plugin file must contain a top-level mapping", path)
        return data

    def _validate_schema(self, data: dict[str, Any], path: Path) -> None:
        """Validate schema version (REQ024)."""
        version = data.get("version")
        if version is None:
            raise PluginLoadError("Missing mandatory field: version", path)
        if str(version) not in SUPPORTED_PLUGIN_VERSIONS:
            raise PluginLoadError(
                f"Unsupported plugin version: {version} "
                f"(supported: {SUPPORTED_PLUGIN_VERSIONS})",
                path,
            )

    # ------------------------------------------------------------------
    # Conversion helpers
    # ------------------------------------------------------------------

    def _convert(self, data: dict[str, Any], path: Path) -> PluginDefinition:
        """Convert validated raw data to structured definitions."""
        version = str(data["version"])
        atomic_tests: list[AtomicTest] = []
        presets: list[TestSuitePreset] = []

        raw_tests = data.get("atomic_tests", [])
        if isinstance(raw_tests, list):
            for idx, raw_test in enumerate(raw_tests):
                if not isinstance(raw_test, dict):
                    _LOGGER.warning(
                        "Skipping non-dict atomic test at index %d in %s",
                        idx,
                        path,
                    )
                    continue
                test = self._convert_atomic_test(raw_test, path, idx)
                if test is not None:
                    atomic_tests.append(test)

        raw_presets = data.get("presets", [])
        if isinstance(raw_presets, list):
            for idx, raw_preset in enumerate(raw_presets):
                if not isinstance(raw_preset, dict):
                    _LOGGER.warning(
                        "Skipping non-dict preset at index %d in %s", idx, path
                    )
                    continue
                preset = self._convert_preset(raw_preset, path, idx)
                if preset is not None:
                    presets.append(preset)

        return PluginDefinition(
            version=version,
            source_path=path,
            atomic_tests=atomic_tests,
            presets=presets,
        )

    def _convert_atomic_test(
        self, raw: dict[str, Any], path: Path, index: int
    ) -> AtomicTest | None:
        """Convert a raw atomic-test dict to an ``AtomicTest`` instance (REQ027)."""
        mandatory = [
            "id",
            "name",
            "test_type",
            "target_path",
            "execution_strategy",
            "weight",
        ]
        missing = [f for f in mandatory if f not in raw or raw[f] is None]
        if missing:
            _LOGGER.error(
                "Skipping atomic test at index %d in %s: missing mandatory fields %s",
                index,
                path,
                missing,
            )
            return None

        test_id = str(raw["id"])
        name = str(raw["name"])
        test_type_str = str(raw["test_type"]).lower()
        target_path = str(raw["target_path"])
        execution_strategy_str = (
            str(raw["execution_strategy"]).lower().replace("_", "-")
        )
        weight = float(raw["weight"])

        try:
            test_type = TestType(test_type_str)
        except ValueError:
            _LOGGER.error(
                "Skipping atomic test %s in %s: unknown test_type %r",
                test_id,
                path,
                test_type_str,
            )
            return None

        try:
            execution_strategy = ExecutionStrategy(execution_strategy_str)
        except ValueError:
            _LOGGER.error(
                "Skipping atomic test %s in %s: unknown execution_strategy %r",
                test_id,
                path,
                execution_strategy_str,
            )
            return None

        command = raw.get("command")
        if command is not None:
            command = str(command)

        grading_prompt = raw.get("grading_prompt")
        if grading_prompt is not None:
            grading_prompt = str(grading_prompt)

        required_debian_packages = ()
        raw_packages = raw.get("required_debian_packages")
        if isinstance(raw_packages, list):
            required_debian_packages = tuple(str(p) for p in raw_packages)

        evaluator = raw.get("evaluator")
        if evaluator is not None and not isinstance(evaluator, dict):
            _LOGGER.warning(
                "Invalid evaluator for test %s in %s; expected dict, got %s",
                test_id,
                path,
                type(evaluator).__name__,
            )
            evaluator = None

        if isinstance(evaluator, dict) and evaluator.get("type") == "custom":
            try:
                _validate_custom_evaluator(evaluator, path, test_id)
            except PluginLoadError as exc:
                _LOGGER.error(
                    "Skipping atomic test %s in %s: %s",
                    test_id,
                    path,
                    exc.message,
                )
                return None

        return AtomicTest(
            id=test_id,
            name=name,
            test_type=test_type,
            command=command,
            grading_prompt=grading_prompt,
            target_path=target_path,
            execution_strategy=execution_strategy,
            weight=weight,
            required_debian_packages=required_debian_packages,
            evaluator=evaluator,
        )

    def _convert_preset(
        self, raw: dict[str, Any], path: Path, index: int
    ) -> TestSuitePreset | None:
        """Convert a raw preset dict to a ``TestSuitePreset`` instance.

        Test references are stored as lightweight ``AtomicTest`` placeholders
        (only ``id`` and ``weight`` are populated).  The ``PluginRegistry``
        resolves them to real tests after all plugins are loaded.
        """
        name = raw.get("name")
        if not name:
            _LOGGER.error(
                "Skipping preset at index %d in %s: missing name", index, path
            )
            return None
        name = str(name)

        tests: list[AtomicTest] = []
        raw_tests = raw.get("tests", [])
        if isinstance(raw_tests, list):
            for t in raw_tests:
                if isinstance(t, dict):
                    ref_id = str(t.get("id", ""))
                    ref_weight = float(t.get("weight", 1.0))
                    tests.append(
                        AtomicTest(
                            id=ref_id,
                            name=ref_id,
                            test_type=TestType.DETERMINISTIC,
                            weight=ref_weight,
                        )
                    )
                else:
                    _LOGGER.warning(
                        "Skipping non-dict test reference in preset %s in %s",
                        name,
                        path,
                    )

        return TestSuitePreset(name=name, tests=tests)


# ----------------------------------------------------------------------
# Plugin Registry
# ----------------------------------------------------------------------

class PluginRegistry:
    """Collects atomic tests and presets from one or more plugins.

    Supports cross-plugin preset references (REQ020).
    """

    def __init__(self) -> None:
        self.atomic_tests: dict[str, AtomicTest] = {}
        self.presets: dict[str, TestSuitePreset] = {}
        self._pending_presets: list[tuple[str, list[AtomicTest]]] = []

    def load_plugins(self, paths: list[Path | str]) -> None:
        """Load multiple plugin files and resolve cross-references."""
        loader = PluginLoader()
        definitions = []
        for path in paths:
            try:
                definitions.append(loader.load_plugin(path))
            except PluginLoadError as exc:
                _LOGGER.error("Failed to load plugin %s: %s", exc.source_path, exc.message)
                raise

        # Phase 1: register all atomic tests (deduplicate by id)
        for definition in definitions:
            for test in definition.atomic_tests:
                if test.id in self.atomic_tests:
                    _LOGGER.warning(
                        "Duplicate atomic test id %s in %s; overwriting previous definition",
                        test.id,
                        definition.source_path,
                    )
                self.atomic_tests[test.id] = test

        # Phase 2: resolve all presets
        for definition in definitions:
            for preset in definition.presets:
                resolved_tests = []
                for ref in preset.tests:
                    if ref.id in self.atomic_tests:
                        real_test = self.atomic_tests[ref.id]
                        # Override weight with the preset-specific value
                        test_copy = replace(real_test, weight=ref.weight)
                        resolved_tests.append(test_copy)
                    else:
                        _LOGGER.warning(
                            "Preset %s in %s references unknown test %s",
                            preset.name,
                            definition.source_path,
                            ref.id,
                        )
                if resolved_tests:
                    self.presets[preset.name] = TestSuitePreset(
                        name=preset.name,
                        tests=resolved_tests,
                    )
                else:
                    _LOGGER.warning(
                        "Preset %s in %s has no resolved tests; skipping",
                        preset.name,
                        definition.source_path,
                    )


# ----------------------------------------------------------------------
# Plugin evaluators (regex, script, custom)
# ----------------------------------------------------------------------

def _validate_glob_pattern(pattern: str) -> None:
    """Reject patterns that attempt path traversal."""
    if ".." in pattern:
        raise ValueError(f"Glob pattern contains path traversal: {pattern}")


def _clamp_grade(value: float, grade_scale_maximum: float) -> float:
    """Clamp a raw grade to [0, grade_scale_maximum]."""
    return max(0.0, min(grade_scale_maximum, float(value)))


def run_regex_evaluator(
    container_name: str,
    extracted_path: str,
    evaluator: dict,
    grade_scale_maximum: float = 20.0,
) -> float:
    """Run a regex-based evaluator inside the container and return a grade in [0, grade_scale_maximum].

    The evaluator dict is expected to contain at minimum:

    * ``pattern`` (str) — Python regular expression.
    * ``target_file`` (str, optional) — glob pattern relative to *extracted_path*.
    * ``score_on_match`` / ``score_on_no_match`` (float, optional) — grades.
    """
    pattern = str(evaluator.get("pattern", ""))
    target_file = str(evaluator.get("target_file", "*"))
    score_on_match = float(evaluator.get("score_on_match", 0.0))
    score_on_no_match = float(evaluator.get("score_on_no_match", grade_scale_maximum))

    if not pattern:
        _LOGGER.warning("Regex evaluator has empty pattern; returning 0.0")
        return 0.0

    _validate_glob_pattern(target_file)

    # Build a Python one-liner that runs the regex against matching files.
    script = (
        f"import glob, os, re; "
        f"files = glob.glob(os.path.join({shlex.quote(extracted_path)}, {shlex.quote(target_file)}), recursive=True); "
        f"matched = False; "
        f"rx = re.compile({shlex.quote(pattern)}); "
        f"for f in files: "
        f"    with open(f, 'r', errors='ignore') as fh: "
        f"        if rx.search(fh.read()): "
        f"            matched = True; "
        f"            break; "
        f"print({score_on_match} if matched else {score_on_no_match})"
    )

    try:
        proc = container_exec_result(
            container_name,
            f"python3 -c {shlex.quote(script)}",
            timeout=REGEX_EVAL_TIMEOUT,
        )
        raw = float(proc.stdout.strip().splitlines()[-1])
        return _clamp_grade(raw, grade_scale_maximum)
    except (ValueError, IndexError, TimeoutError) as exc:
        _LOGGER.warning("Regex evaluator failed for %s: %s", container_name, exc)
        return 0.0


def run_script_evaluator(
    container_name: str,
    extracted_path: str,
    test: AtomicTest,
    grade_scale_maximum: float = 20.0,
) -> float:
    """Run a script-based deterministic evaluator and return a grade in [0, grade_scale_maximum].

    The evaluator dict may contain:

    * ``grade_on_zero_exit`` (float, default grade_scale_maximum)
    * ``grade_on_non_zero_exit`` (float, default 0.0)
    """
    evaluator = test.evaluator or {}
    command = test.command or str(evaluator.get("command", ""))
    if not command:
        _LOGGER.warning("Script evaluator has no command for test %s", test.id)
        return 0.0

    grade_on_zero = float(evaluator.get("grade_on_zero_exit", grade_scale_maximum))
    grade_on_non_zero = float(evaluator.get("grade_on_non_zero_exit", 0.0))

    full_command = f"cd {shlex.quote(extracted_path)} && {command}"
    try:
        proc = container_exec_result(
            container_name, full_command, timeout=SCRIPT_EVAL_TIMEOUT
        )
    except TimeoutError:
        _LOGGER.warning(
            "Script evaluator timed out after %ds for test %s",
            SCRIPT_EVAL_TIMEOUT,
            test.id,
        )
        return 0.0

    if proc.returncode == 0:
        return _clamp_grade(grade_on_zero, grade_scale_maximum)
    return _clamp_grade(grade_on_non_zero, grade_scale_maximum)


def run_custom_evaluator(
    evaluator: dict,
    exit_code: int,
    stdout: str,
    stderr: str,
    grade_scale_maximum: float = 20.0,
) -> float:
    """Execute a plugin-defined custom evaluator in a restricted subprocess.

    The evaluator dict must contain a validated ``source`` string that defines
    a function ``evaluate(exit_code, stdout, stderr)`` returning a float.
    """
    source = str(evaluator.get("source", ""))
    if not source.strip():
        _LOGGER.warning("Custom evaluator has empty source; returning 0.0")
        return 0.0

    payload = {
        "source": source,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "grade_scale_maximum": grade_scale_maximum,
    }

    runner_script = (
        "import json, sys, math\n"
        "payload = json.load(sys.stdin)\n"
        "source = payload['source']\n"
        "exit_code = payload['exit_code']\n"
        "stdout = payload['stdout']\n"
        "stderr = payload['stderr']\n"
        "grade_scale_maximum = payload['grade_scale_maximum']\n"
        "\n"
        "def _restricted_import(name, *args, **kwargs):\n"
        "    base = name.split('.')[0]\n"
        "    allowed = {'re', 'math', 'json', 'statistics'}\n"
        "    if base not in allowed:\n"
        "        raise ImportError(f'Import of {name} is not allowed')\n"
        "    return __builtins__.__import__(name, *args, **kwargs)\n"
        "\n"
        "namespace = {\n"
        "    '__builtins__': {\n"
        "        'True': True, 'False': False, 'None': None,\n"
        "        'len': len, 'str': str, 'int': int, 'float': float,\n"
        "        'range': range, 'list': list, 'dict': dict, 'tuple': tuple,\n"
        "        'set': set, 'abs': abs, 'min': min, 'max': max, 'sum': sum,\n"
        "        'round': round, 'enumerate': enumerate, 'zip': zip,\n"
        "        'map': map, 'filter': filter,\n"
        "        '__import__': _restricted_import,\n"
        "    }\n"
        "}\n"
        "exec(compile(source, '<evaluator>', 'exec'), namespace)\n"
        "result = float(namespace['evaluate'](exit_code, stdout, stderr))\n"
        "clamped = max(0.0, min(grade_scale_maximum, result))\n"
        "print(json.dumps(clamped))\n"
    )

    try:
        proc = subprocess.run(
            [sys.executable, "-c", runner_script],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=CUSTOM_EVAL_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        _LOGGER.warning(
            "Custom evaluator timed out after %ds", CUSTOM_EVAL_TIMEOUT
        )
        return 0.0

    if proc.returncode != 0:
        _LOGGER.warning(
            "Custom evaluator failed: %s", proc.stderr.strip() or "unknown error"
        )
        return 0.0

    try:
        return float(json.loads(proc.stdout.strip()))
    except (ValueError, json.JSONDecodeError) as exc:
        _LOGGER.warning("Custom evaluator returned invalid output: %s", exc)
        return 0.0

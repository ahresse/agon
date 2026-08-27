"""type_check_mypy plugin (T037): static typing errors & annotation coverage.

Computes annotation coverage from the AST (deterministic) and, if mypy is
available, penalizes reported type errors. Grade blends annotation coverage with
an error penalty.
"""
from __future__ import annotations

import ast

from src.tests_plugins.quality import common
from src.tests_plugins.registry import PluginInput, PluginOutput

KEY = "quality.type_check_mypy"
_PENALTY_PER_ERROR = 5.0


class TypeCheckMypyPlugin:
    key = KEY

    def run(self, payload: PluginInput) -> PluginOutput:
        root = payload.submission_path
        sources = common.read_sources(root)
        if not sources:
            return PluginOutput(grade=0.0, cons=["No Python source found to type-check."])

        annotated, total = 0, 0
        for src in sources:
            try:
                tree = ast.parse(src)
            except SyntaxError:
                return PluginOutput(grade=0.0, cons=["Submission contains a syntax error."])
            a, t = _annotation_coverage(tree)
            annotated += a
            total += t

        coverage = 1.0 if total == 0 else annotated / total
        error_count = _mypy_errors(root, payload.timeout_seconds)
        penalty = _PENALTY_PER_ERROR * error_count if error_count is not None else 0.0
        grade = common.cap(100.0 * coverage - penalty)

        pros: list[str] = []
        cons: list[str] = []
        if coverage >= 0.8:
            pros.append(f"Strong annotation coverage ({coverage:.0%}).")
        else:
            cons.append(f"Low annotation coverage ({coverage:.0%}).")
        if error_count:
            cons.append(f"mypy reported {error_count} type error(s).")
        elif error_count == 0:
            pros.append("mypy reports no type errors.")
        return PluginOutput(grade=grade, pros=pros, cons=cons)


def _annotation_coverage(tree: ast.AST) -> tuple[int, int]:
    annotated = 0
    total = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            total += 1  # return annotation
            if node.returns is not None:
                annotated += 1
            for arg in list(node.args.args) + list(node.args.kwonlyargs):
                if arg.arg in {"self", "cls"}:
                    continue
                total += 1
                if arg.annotation is not None:
                    annotated += 1
    return annotated, total


def _mypy_errors(root: str, timeout: int) -> int | None:
    """Return the count of mypy errors, or None if mypy is unavailable."""
    try:
        result = common.run_tool(["mypy", "--no-error-summary", root], cwd=".", timeout=timeout)
    except (FileNotFoundError, OSError):
        return None
    return sum(1 for line in result.stdout.splitlines() if ": error:" in line)


def factory() -> TypeCheckMypyPlugin:
    return TypeCheckMypyPlugin()

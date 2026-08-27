"""formatting_black plugin (T039): formatting conformance & documentation.

Blends `black --check` conformance (share of files already formatted) with
docstring coverage of public modules/classes/functions computed from the AST. If
black is unavailable, formatting conformance defaults to neutral and the grade is
driven by docstring coverage.
"""
from __future__ import annotations

import ast

from src.tests_plugins.quality import common
from src.tests_plugins.registry import PluginInput, PluginOutput

KEY = "quality.formatting_black"


class FormattingBlackPlugin:
    key = KEY

    def run(self, payload: PluginInput) -> PluginOutput:
        root = payload.submission_path
        files = common.collect_python_files(root)
        if not files:
            return PluginOutput(grade=0.0, cons=["No Python source found to check."])

        documented, total = 0, 0
        for path in files:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                src = fh.read()
            try:
                tree = ast.parse(src)
            except SyntaxError:
                return PluginOutput(grade=0.0, cons=["Submission contains a syntax error."])
            d, t = _docstring_coverage(tree)
            documented += d
            total += t
        doc_coverage = 1.0 if total == 0 else documented / total

        fmt_conformance = _black_conformance(root, files, payload.timeout_seconds)
        # Grade: 60% formatting conformance + 40% docstring coverage.
        grade = common.cap(100.0 * (0.6 * fmt_conformance + 0.4 * doc_coverage))

        pros: list[str] = []
        cons: list[str] = []
        if fmt_conformance >= 0.999:
            pros.append("Code conforms to black formatting.")
        elif fmt_conformance < 0.999:
            cons.append("Some files are not black-formatted.")
        if doc_coverage >= 0.8:
            pros.append(f"Good docstring coverage ({doc_coverage:.0%}).")
        else:
            cons.append(f"Low docstring coverage ({doc_coverage:.0%}).")
        return PluginOutput(grade=grade, pros=pros, cons=cons)


def _docstring_coverage(tree: ast.AST) -> tuple[int, int]:
    documented = 0
    total = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name.startswith("_"):
                continue
            total += 1
            if ast.get_docstring(node):
                documented += 1
    return documented, total


def _black_conformance(root: str, files: list[str], timeout: int) -> float:
    """Return share of files already black-formatted; 1.0 if black unavailable."""
    try:
        result = common.run_tool(["black", "--check", "--quiet", root], cwd=".", timeout=timeout)
    except (FileNotFoundError, OSError):
        return 1.0
    if result.returncode == 0:
        return 1.0
    # black reports "would reformat" lines to stderr; count them.
    would = sum(1 for line in result.stderr.splitlines() if "would reformat" in line)
    if not files:
        return 1.0
    return max(0.0, (len(files) - would) / len(files))


def factory() -> FormattingBlackPlugin:
    return FormattingBlackPlugin()

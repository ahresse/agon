"""Built-in metric test plugin: a simple, measurable Python code quality check.

Runs inside a container against the candidate source. This example grades on two
measurable signals: presence of docstrings and average function length. It is
intentionally simple; it demonstrates the weight-in / grade-out contract.
"""
from __future__ import annotations

import ast
import os

from src.tests_plugins.registry import PluginInput, PluginOutput

KEY = "metric.readability"


class ReadabilityMetricPlugin:
    key = KEY

    def run(self, payload: PluginInput) -> PluginOutput:
        sources = _collect_python_sources(payload.submission_path)
        if not sources:
            return PluginOutput(grade=0.0, cons=["No Python source found to assess."])

        total_funcs = 0
        documented_funcs = 0
        long_funcs = 0
        for src in sources:
            try:
                tree = ast.parse(src)
            except SyntaxError:
                return PluginOutput(
                    grade=0.0, cons=["Submission contains a Python syntax error."]
                )
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    total_funcs += 1
                    if ast.get_docstring(node):
                        documented_funcs += 1
                    length = (node.end_lineno or node.lineno) - node.lineno
                    if length > 50:
                        long_funcs += 1

        pros: list[str] = []
        cons: list[str] = []
        if total_funcs == 0:
            return PluginOutput(grade=50.0, cons=["No functions defined to assess."])

        doc_ratio = documented_funcs / total_funcs
        long_ratio = long_funcs / total_funcs
        grade = max(0.0, min(100.0, 100.0 * (0.6 * doc_ratio + 0.4 * (1 - long_ratio))))

        if doc_ratio >= 0.8:
            pros.append("Most functions are documented with docstrings.")
        else:
            cons.append("Many functions lack docstrings.")
        if long_ratio <= 0.2:
            pros.append("Functions are generally concise.")
        else:
            cons.append("Several functions are overly long (>50 lines).")

        return PluginOutput(grade=round(grade, 2), pros=pros, cons=cons)


def _collect_python_sources(root: str) -> list[str]:
    sources: list[str] = []
    if os.path.isfile(root) and root.endswith(".py"):
        sources.append(_read(root))
        return sources
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            if f.endswith(".py"):
                sources.append(_read(os.path.join(dirpath, f)))
    return sources


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def factory() -> ReadabilityMetricPlugin:
    return ReadabilityMetricPlugin()

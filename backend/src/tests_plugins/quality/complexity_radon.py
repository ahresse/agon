"""complexity_radon plugin (T035): cyclomatic complexity & maintainability.

Computes cyclomatic complexity per function from the AST (deterministic, no
external dependency). Functions above a configurable threshold are penalized; the
grade blends the share of simple functions with an average-complexity penalty.
"""
from __future__ import annotations

import ast

from src.tests_plugins.quality import common
from src.tests_plugins.registry import PluginInput, PluginOutput

KEY = "quality.complexity_radon"
_DEFAULT_CC_THRESHOLD = 10

_BRANCHING = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.And,
    ast.Or,
    ast.ExceptHandler,
    ast.With,
    ast.AsyncWith,
    ast.IfExp,
    ast.comprehension,
    ast.BoolOp,
)


class ComplexityRadonPlugin:
    key = KEY

    def run(self, payload: PluginInput) -> PluginOutput:
        threshold = int(payload.config.get("cc_threshold", _DEFAULT_CC_THRESHOLD))
        sources = common.read_sources(payload.submission_path)
        if not sources:
            return PluginOutput(grade=0.0, cons=["No Python source found to analyze."])

        complexities: list[tuple[str, int]] = []
        for src in sources:
            try:
                tree = ast.parse(src)
            except SyntaxError:
                return PluginOutput(grade=0.0, cons=["Submission contains a syntax error."])
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexities.append((node.name, _cyclomatic_complexity(node)))

        if not complexities:
            return PluginOutput(grade=75.0, pros=["No functions; nothing complex to flag."])

        over = [(n, c) for n, c in complexities if c > threshold]
        simple_share = (len(complexities) - len(over)) / len(complexities)
        avg_cc = sum(c for _, c in complexities) / len(complexities)
        avg_penalty = max(0.0, (avg_cc - 1) * 3.0)
        grade = common.cap(100.0 * simple_share - avg_penalty)

        pros: list[str] = []
        cons: list[str] = []
        if not over:
            pros.append(f"All functions have cyclomatic complexity <= {threshold}.")
        else:
            worst = ", ".join(f"{n} (CC={c})" for n, c in sorted(over, key=lambda x: -x[1])[:3])
            cons.append(f"{len(over)} functions exceed CC {threshold}: {worst}.")
        if avg_cc <= 3:
            pros.append(f"Low average complexity (avg CC={avg_cc:.1f}).")
        return PluginOutput(grade=grade, pros=pros, cons=cons)


def _cyclomatic_complexity(func: ast.AST) -> int:
    complexity = 1
    for node in ast.walk(func):
        if isinstance(node, (ast.BoolOp,)):
            # each additional boolean operand adds a decision point
            complexity += max(0, len(node.values) - 1)
        elif isinstance(
            node,
            (
                ast.If,
                ast.For,
                ast.AsyncFor,
                ast.While,
                ast.ExceptHandler,
                ast.IfExp,
                ast.comprehension,
            ),
        ):
            complexity += 1
    return complexity


def factory() -> ComplexityRadonPlugin:
    return ComplexityRadonPlugin()

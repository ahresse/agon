"""stdlib_idioms plugin (T036): Pythonic use of builtins/standard library.

AST analysis rewarding idiomatic constructs (enumerate, zip, comprehensions,
context managers, pathlib, dataclasses) and penalizing anti-patterns (bare
except, mutable default args, manual index loops via range(len(...)), and
os.path usage where pathlib fits). The grade blends the idiom count against
detected anti-patterns.
"""
from __future__ import annotations

import ast

from src.tests_plugins.quality import common
from src.tests_plugins.registry import PluginInput, PluginOutput

KEY = "quality.stdlib_idioms"
_ANTIPATTERN_PENALTY = 8.0


class StdlibIdiomsPlugin:
    key = KEY

    def run(self, payload: PluginInput) -> PluginOutput:
        sources = common.read_sources(payload.submission_path)
        if not sources:
            return PluginOutput(grade=0.0, cons=["No Python source found to analyze."])

        idioms = 0
        antipatterns: list[str] = []
        for src in sources:
            try:
                tree = ast.parse(src)
            except SyntaxError:
                return PluginOutput(grade=0.0, cons=["Submission contains a syntax error."])
            i, a = _analyze(tree)
            idioms += i
            antipatterns.extend(a)

        penalty = _ANTIPATTERN_PENALTY * len(antipatterns)
        # Reward idioms modestly so idiomatic-but-imperfect code still scores well.
        base = 70.0 + min(30.0, idioms * 3.0)
        grade = common.cap(base - penalty)

        pros: list[str] = []
        cons: list[str] = []
        if idioms:
            pros.append(f"Uses {idioms} idiomatic standard-library constructs.")
        if antipatterns:
            unique = list(dict.fromkeys(antipatterns))
            cons.extend(unique[:5])
        else:
            pros.append("No common anti-patterns detected.")
        return PluginOutput(grade=grade, pros=pros, cons=cons)


def _analyze(tree: ast.AST) -> tuple[int, list[str]]:
    idioms = 0
    antipatterns: list[str] = []
    for node in ast.walk(tree):
        # Idioms
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            idioms += 1
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            idioms += 1
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"enumerate", "zip", "any", "all", "sorted"}:
                idioms += 1
        elif isinstance(node, ast.Attribute) and _is_name(node.value, "pathlib"):
            idioms += 1
        elif isinstance(node, ast.Name) and node.id in {"dataclass"}:
            idioms += 1

        # Anti-patterns
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            antipatterns.append("Bare 'except:' clause (catch specific exceptions).")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for default in node.args.defaults + node.args.kw_defaults:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    antipatterns.append(
                        f"Mutable default argument in '{node.name}' (use None sentinel)."
                    )
        if isinstance(node, (ast.For,)) and _is_range_len(node.iter):
            antipatterns.append("Manual index loop 'for i in range(len(...))' (use enumerate).")
        if isinstance(node, ast.Attribute) and _is_name(node.value, "os") and node.attr == "path":
            antipatterns.append("os.path usage where pathlib.Path is more idiomatic.")
    return idioms, antipatterns


def _is_name(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def _is_range_len(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "range"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Call)
        and isinstance(node.args[0].func, ast.Name)
        and node.args[0].func.id == "len"
    )


def factory() -> StdlibIdiomsPlugin:
    return StdlibIdiomsPlugin()

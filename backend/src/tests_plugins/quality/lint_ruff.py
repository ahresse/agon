"""lint_ruff plugin (T034): style & correctness via `ruff check` (JSON).

Grade = 100 minus a per-violation penalty normalized by lines of code. If ruff is
unavailable in the environment, the plugin degrades to a lightweight AST-free
heuristic so it still returns a deterministic 0-100 grade.
"""
from __future__ import annotations

from collections import Counter

from src.tests_plugins.quality import common
from src.tests_plugins.registry import PluginInput, PluginOutput

KEY = "quality.lint_ruff"
_PENALTY_PER_VIOLATION = 2.0


class LintRuffPlugin:
    key = KEY

    def run(self, payload: PluginInput) -> PluginOutput:
        root = payload.submission_path
        files = common.collect_python_files(root)
        if not files:
            return PluginOutput(grade=0.0, cons=["No Python source found to lint."])

        timeout = payload.timeout_seconds
        try:
            result = common.run_tool(
                ["ruff", "check", "--output-format", "json", root],
                cwd=root if _is_dir(root) else ".",
                timeout=timeout,
            )
            violations = common.parse_json(result.stdout, default=[])
            if not isinstance(violations, list):
                violations = []
        except (FileNotFoundError, OSError):
            return _heuristic(root)

        loc = max(1, common.count_lines(root))
        penalty = _PENALTY_PER_VIOLATION * len(violations) * (100.0 / loc)
        grade = common.grade_from_penalty(penalty)

        pros: list[str] = []
        cons: list[str] = []
        if not violations:
            pros.append("ruff reports no lint violations.")
        else:
            codes = Counter(v.get("code", "?") for v in violations if isinstance(v, dict))
            top = ", ".join(f"{code} x{n}" for code, n in codes.most_common(3))
            cons.append(f"{len(violations)} lint violations (top: {top}).")
        return PluginOutput(grade=grade, pros=pros, cons=cons)


def _is_dir(path: str) -> bool:
    import os

    return os.path.isdir(path)


def _heuristic(root: str) -> PluginOutput:
    """Fallback when ruff is unavailable: penalize obvious style issues."""
    issues = 0
    sources = common.read_sources(root)
    loc = max(1, sum(s.count("\n") + 1 for s in sources))
    for src in sources:
        for line in src.splitlines():
            if len(line) > 100:
                issues += 1
            if line.rstrip() != line:
                issues += 1
    penalty = 2.0 * issues * (100.0 / loc)
    grade = common.grade_from_penalty(penalty)
    cons = [] if issues == 0 else [f"{issues} style issues (long/trailing-whitespace lines)."]
    pros = ["No obvious style issues detected."] if issues == 0 else []
    return PluginOutput(grade=grade, pros=pros, cons=cons)


def factory() -> LintRuffPlugin:
    return LintRuffPlugin()

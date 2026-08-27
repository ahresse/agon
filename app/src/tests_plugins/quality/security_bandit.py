"""security_bandit plugin (T038): common security issues (severity-weighted).

Uses `bandit` JSON output when available; otherwise falls back to an AST scan for
a small set of high-signal insecure patterns (eval/exec, subprocess shell=True,
pickle.loads, yaml.load without SafeLoader). Grade = 100 minus severity-weighted
penalties.
"""
from __future__ import annotations

import ast

from src.tests_plugins.quality import common
from src.tests_plugins.registry import PluginInput, PluginOutput

KEY = "quality.security_bandit"
_SEVERITY_PENALTY = {"HIGH": 25.0, "MEDIUM": 10.0, "LOW": 3.0}


class SecurityBanditPlugin:
    key = KEY

    def run(self, payload: PluginInput) -> PluginOutput:
        root = payload.submission_path
        files = common.collect_python_files(root)
        if not files:
            return PluginOutput(grade=0.0, cons=["No Python source found to scan."])

        issues = _bandit_issues(root, payload.timeout_seconds)
        if issues is None:
            issues = _heuristic_issues(root)

        penalty = sum(_SEVERITY_PENALTY.get(sev, 3.0) for sev, _ in issues)
        grade = common.grade_from_penalty(penalty)

        pros: list[str] = []
        cons: list[str] = []
        if not issues:
            pros.append("No security issues detected.")
        else:
            for sev, msg in issues[:5]:
                cons.append(f"[{sev}] {msg}")
        return PluginOutput(grade=grade, pros=pros, cons=cons)


def _bandit_issues(root: str, timeout: int) -> list[tuple[str, str]] | None:
    try:
        result = common.run_tool(["bandit", "-r", "-f", "json", root], cwd=".", timeout=timeout)
    except (FileNotFoundError, OSError):
        return None
    data = common.parse_json(result.stdout, default={})
    out: list[tuple[str, str]] = []
    for r in data.get("results", []) if isinstance(data, dict) else []:
        sev = str(r.get("issue_severity", "LOW")).upper()
        out.append((sev, f"{r.get('test_id', '?')}: {r.get('issue_text', 'issue')}"))
    return out


def _heuristic_issues(root: str) -> list[tuple[str, str]]:
    issues: list[tuple[str, str]] = []
    for src in common.read_sources(root):
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = _call_name(node)
                if name in {"eval", "exec"}:
                    issues.append(("HIGH", f"Use of {name}() is dangerous."))
                elif name in {"pickle.loads", "pickle.load"}:
                    issues.append(("MEDIUM", "Unsafe deserialization via pickle."))
                elif name == "yaml.load" and not _has_safe_loader(node):
                    issues.append(("MEDIUM", "yaml.load without SafeLoader."))
                elif _is_subprocess_shell_true(node):
                    issues.append(("HIGH", "subprocess call with shell=True."))
    return issues


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
        return f"{node.func.value.id}.{node.func.attr}"
    return ""


def _has_safe_loader(node: ast.Call) -> bool:
    return any(kw.arg == "Loader" for kw in node.keywords)


def _is_subprocess_shell_true(node: ast.Call) -> bool:
    name = _call_name(node)
    if not name.startswith("subprocess."):
        return False
    return any(
        kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True
        for kw in node.keywords
    )


def factory() -> SecurityBanditPlugin:
    return SecurityBanditPlugin()

"""Shared helpers for Python quality metric plugins (T033).

Provides:
- source collection over a submission path,
- a subprocess+JSON tool runner,
- a normalization helper mapping a raw penalty to a 0-100 grade,
- pros/cons builders.

All metric plugins normalize their raw tool output to a comparable 0-100 grade so
grades are weighted consistently (Constitution Principle I & IV).
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class ToolResult:
    returncode: int
    stdout: str
    stderr: str


def collect_python_files(root: str) -> list[str]:
    """Return absolute paths of all .py files under root (or root itself)."""
    if os.path.isfile(root):
        return [root] if root.endswith(".py") else []
    files: list[str] = []
    for dirpath, _dirs, names in os.walk(root):
        for n in names:
            if n.endswith(".py"):
                files.append(os.path.join(dirpath, n))
    return sorted(files)


def read_sources(root: str) -> list[str]:
    out: list[str] = []
    for path in collect_python_files(root):
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            out.append(fh.read())
    return out


def count_lines(root: str) -> int:
    total = 0
    for src in read_sources(root):
        total += src.count("\n") + 1
    return total


def run_tool(args: list[str], cwd: str, timeout: int) -> ToolResult:
    """Run an external tool, capturing stdout/stderr. Never raises on non-zero."""
    proc = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return ToolResult(returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)


def parse_json(stdout: str, default):
    try:
        return json.loads(stdout) if stdout.strip() else default
    except json.JSONDecodeError:
        return default


def grade_from_penalty(penalty: float) -> float:
    """Map a non-negative penalty to a 0-100 grade (100 = no penalty)."""
    return round(max(0.0, min(100.0, 100.0 - penalty)), 2)


def grade_from_ratio(good: float, total: float) -> float:
    """Map a good/total ratio to a 0-100 grade. Empty total -> 100 (nothing wrong)."""
    if total <= 0:
        return 100.0
    return round(max(0.0, min(100.0, 100.0 * good / total)), 2)


def cap(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return round(max(low, min(high, value)), 2)

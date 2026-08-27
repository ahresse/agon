"""Guardrail: the project must contain no project-authored JavaScript/TypeScript
and no JS package/build toolchain (feature 005, FR-002/FR-008/SC-001/SC-006).

The single vendored, non-authored helper under static/vendor/ is excluded.
"""
from __future__ import annotations

import os
import subprocess

_AUTHORED_JS_EXT = (".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs")
_JS_MANIFESTS = {"package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "vite.config.ts"}
# Excluded: the vendored, non-authored helper asset (served as a static file).
_ALLOWED_PREFIXES = (os.path.join("app", "src", "static", "vendor"),)


def _repo_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    proc = subprocess.run(
        ["git", "-C", here, "rev-parse", "--show-toplevel"], capture_output=True, text=True
    )
    return proc.stdout.strip() if proc.returncode == 0 else os.path.abspath(
        os.path.join(here, "..", "..", "..")
    )


def _tracked_files(root: str) -> list[str]:
    proc = subprocess.run(
        ["git", "-C", root, "ls-files"], capture_output=True, text=True
    )
    if proc.returncode == 0 and proc.stdout.strip():
        return [line for line in proc.stdout.splitlines() if line]
    # Fallback: walk the tree (skip vcs/venv/node_modules).
    out: list[str] = []
    for dirpath, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", ".venv", "venv"}]
        for n in names:
            out.append(os.path.relpath(os.path.join(dirpath, n), root))
    return out


def _is_allowed(rel: str) -> bool:
    return any(rel.startswith(p) for p in _ALLOWED_PREFIXES)


def test_no_project_authored_javascript():
    root = _repo_root()
    offenders = []
    for rel in _tracked_files(root):
        if _is_allowed(rel):
            continue
        base = os.path.basename(rel)
        if base in _JS_MANIFESTS or rel.endswith(_AUTHORED_JS_EXT):
            offenders.append(rel)
    assert not offenders, f"project-authored JavaScript/TypeScript or JS toolchain found: {offenders}"


def test_no_frontend_directory():
    root = _repo_root()
    assert not os.path.isdir(os.path.join(root, "frontend")), "frontend/ must be removed"


def test_vendored_helper_present_and_excluded():
    root = _repo_root()
    vendored = os.path.join(root, "app", "src", "static", "vendor", "htmx.min.js")
    assert os.path.isfile(vendored), "vendored non-authored helper must be present"
    # It is a .js file but under the allowed vendor prefix, so excluded from the guardrail.
    assert _is_allowed(os.path.join("app", "src", "static", "vendor", "htmx.min.js"))

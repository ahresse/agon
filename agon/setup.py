"""Setup step detection and execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agon.container import container_exec_result


@dataclass
class SetupStep:
    """A single setup instruction to run inside the container."""

    command: str
    description: str = ""


_WELL_KNOWN_FILES = [
    "README",
    "README.md",
    "SETUP.md",
    "Makefile",
    "requirements.txt",
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "setup.sh",
    "install.sh",
    "CMakeLists.txt",
]


def scan_source_tree(path: str) -> list[dict]:
    """Scan *path* for well-known setup instruction files."""
    results = []
    p = Path(path)
    for filename in _WELL_KNOWN_FILES:
        if (p / filename).exists():
            results.append({"filename": filename, "type": "file"})
    return results


def infer_steps(path: str) -> list[SetupStep]:
    """Infer ordered setup steps from files found in *path*."""
    files = scan_source_tree(path)
    filenames = {f["filename"] for f in files}
    steps: list[SetupStep] = []

    # Dependency installation first
    if "requirements.txt" in filenames:
        steps.append(
            SetupStep(
                command="pip install -r requirements.txt",
                description="Install Python dependencies",
            )
        )
    if "package.json" in filenames:
        steps.append(
            SetupStep(
                command="npm install",
                description="Install Node.js dependencies",
            )
        )

    # Build / configuration next
    if "pyproject.toml" in filenames:
        steps.append(
            SetupStep(
                command="pip install -e .",
                description="Install Python project",
            )
        )
    if "setup.sh" in filenames:
        steps.append(
            SetupStep(
                command="bash setup.sh",
                description="Run setup script",
            )
        )
    if "install.sh" in filenames:
        steps.append(
            SetupStep(
                command="bash install.sh",
                description="Run install script",
            )
        )
    if "Makefile" in filenames:
        steps.append(
            SetupStep(
                command="make",
                description="Build with Make",
            )
        )
    if "CMakeLists.txt" in filenames:
        steps.append(
            SetupStep(
                command="cmake . && make",
                description="Build with CMake",
            )
        )
    if "Cargo.toml" in filenames:
        steps.append(
            SetupStep(
                command="cargo build",
                description="Build Rust project",
            )
        )

    return steps


def execute_setup_steps(
    container_name: str,
    steps: list[SetupStep],
    skip_setup: bool = False,
) -> list:
    """Run *steps* inside the container, stopping on the first failure.

    Returns a list of ``CompletedProcess`` objects (or empty list when
    *skip_setup* is ``True``).
    """
    if skip_setup:
        return []

    outputs = []
    for step in steps:
        result = container_exec_result(container_name, step.command)
        outputs.append(result)
        if result.returncode != 0:
            break
    return outputs

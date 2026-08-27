"""LXD execution backend (Constitution Principle II — NON-NEGOTIABLE).

Runs a single test plugin inside a fresh, disposable LXD container and reads back
only the structured ``{grade, pros, cons}`` result. Implemented against the ``lxc``
CLI so it needs no in-process LXD client and works on the Ubuntu/arm64 target.

Lifecycle per run:
  1. launch an ephemeral container from the configured profile/image
  2. push the backend source tree and the candidate submission into it
  3. exec the in-container entrypoint under a hard timeout
  4. parse the JSON result from stdout
  5. delete the container (ephemeral containers auto-delete on stop; we also
     force-delete defensively)

Any failure (launch error, timeout, non-zero exit, unreadable result) raises, and
the caller (test_runner) records the test as FAILED with grade 0 (FR-007).
"""
from __future__ import annotations

import json
import os
import subprocess
import uuid

from src.tests_plugins.registry import PluginInput, PluginOutput, TestPlugin

# Where the backend source and submission are placed inside the container.
_CONTAINER_APP_DIR = "/opt/agon/backend"
_CONTAINER_SUB_DIR = "/opt/agon/submission"


class LXDExecutionError(RuntimeError):
    """Raised when a containerized run cannot complete successfully."""


def _lxc(args: list[str], timeout: int, check: bool = True) -> subprocess.CompletedProcess:
    try:
        proc = subprocess.run(
            ["lxc", *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise LXDExecutionError(
            "The 'lxc' command was not found. Install and initialize LXD on the host "
            "(see backend/src/runners/metric_image.md), or set AGON_USE_LOCAL_RUNNER=1 "
            "for a non-isolating dev fallback."
        ) from exc
    if check and proc.returncode != 0:
        stderr = proc.stderr.strip()
        # Give the operator an actionable hint when the base image is missing.
        if "Failed to find image" in stderr or "not found" in stderr.lower():
            raise LXDExecutionError(
                f"LXD image/profile not available for '{args[1] if len(args) > 1 else '?'}'. "
                "Provision the metric container image first: "
                "run backend/src/runners/provision_image.sh "
                "(see backend/src/runners/metric_image.md). Original error: " + stderr
            )
        raise LXDExecutionError(
            f"lxc {' '.join(args)} failed ({proc.returncode}): {stderr}"
        )
    return proc


def _backend_src_root() -> str:
    # .../backend/src/runners/lxd_backend.py -> .../backend
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def image_available(image_profile: str, timeout: int = 15) -> bool:
    """Return True if the given LXD image alias exists locally."""
    try:
        proc = subprocess.run(
            ["lxc", "image", "info", image_profile],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


def execute_in_lxd(
    image_profile: str,
    plugin: TestPlugin,
    payload: PluginInput,
) -> PluginOutput:
    """Execute ``plugin`` inside a disposable LXD container and return its result."""
    name = f"agon-run-{uuid.uuid4().hex[:12]}"
    timeout = payload.timeout_seconds
    # Overall wall-clock budget for the whole lifecycle; the exec step gets the
    # plugin's timeout, launch/push/delete get a fixed allowance on top.
    setup_timeout = 120

    try:
        # 1. Launch an ephemeral container from the configured profile.
        _lxc(
            ["launch", image_profile, name, "--ephemeral"],
            timeout=setup_timeout,
        )

        # 2. Inject backend source and candidate submission.
        #    `lxc file push -r <localdir> <name>/<parent>/` places <localdir> under
        #    <parent> inside the container; the parent must exist.
        _lxc(["exec", name, "--", "mkdir", "-p", _CONTAINER_APP_DIR], timeout=setup_timeout)
        _lxc(["exec", name, "--", "mkdir", "-p", _CONTAINER_SUB_DIR], timeout=setup_timeout)
        _lxc(
            ["file", "push", "-r", _backend_src_root() + "/src", f"{name}{_CONTAINER_APP_DIR}/"],
            timeout=setup_timeout,
        )
        _lxc(
            ["file", "push", "-r", payload.submission_path, f"{name}{_CONTAINER_SUB_DIR}/"],
            timeout=setup_timeout,
        )

        # 3. Execute the in-container entrypoint under the plugin timeout.
        sub_name = os.path.basename(payload.submission_path.rstrip("/"))
        in_container_sub = os.path.join(_CONTAINER_SUB_DIR, sub_name)
        proc = _lxc(
            [
                "exec",
                name,
                "--env",
                f"PYTHONPATH={_CONTAINER_APP_DIR}",
                "--",
                "python3",
                "-m",
                "src.runners.in_container",
                plugin.key,
                in_container_sub,
                json.dumps(payload.config or {}),
            ],
            timeout=timeout,
            check=False,
        )
        if proc.returncode != 0:
            raise LXDExecutionError(
                f"in-container run failed ({proc.returncode}): {proc.stderr.strip()}"
            )

        data = _parse_result(proc.stdout)
        return PluginOutput(
            grade=float(data["grade"]),
            pros=list(data.get("pros", [])),
            cons=list(data.get("cons", [])),
        )
    finally:
        # 5. Destroy the container (defensive; ephemeral auto-deletes on stop).
        _lxc(["delete", name, "--force"], timeout=setup_timeout, check=False)


def _parse_result(stdout: str) -> dict:
    line = ""
    for candidate in reversed(stdout.strip().splitlines()):
        candidate = candidate.strip()
        if candidate.startswith("{"):
            line = candidate
            break
    if not line:
        raise LXDExecutionError("No structured result returned from container.")
    data = json.loads(line)
    if "error" in data:
        raise LXDExecutionError(str(data["error"]))
    if "grade" not in data:
        raise LXDExecutionError("Container result missing 'grade'.")
    return data

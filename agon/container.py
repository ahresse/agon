"""Container lifecycle and command execution helpers."""

from __future__ import annotations

import subprocess
import uuid
from typing import Any


def container_exec_result(
    container_name: str, shell_command: str, timeout: int | None = None
) -> subprocess.CompletedProcess[str]:
    """Run a shell command in the container and return the CompletedProcess."""
    return subprocess.run(
        ["lxc", "exec", container_name, "--", "bash", "-lc", shell_command],
        check=False,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def container_exec(container_name: str, shell_command: str, timeout: int | None = None) -> None:
    """Run a shell command in the container and raise on non-zero exit."""
    result = container_exec_result(container_name, shell_command, timeout=timeout)
    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            returncode=result.returncode,
            cmd=["lxc", "exec", container_name, "--", "bash", "-lc", shell_command],
            output=result.stdout,
            stderr=result.stderr,
        )


class ContainerManager:
    """High-level manager for ephemeral LXC containers."""

    def launch(self, image: str) -> str:
        """Launch a new container from *image* and return its name."""
        name = f"agon-{uuid.uuid4().hex[:8]}"
        subprocess.run(
            ["lxc", "launch", image, name],
            check=True,
            text=True,
            capture_output=True,
        )
        return name

    def delete(self, name: str) -> None:
        """Force-delete a container, ignoring errors."""
        subprocess.run(
            ["lxc", "delete", "--force", name],
            check=False,
            text=True,
            capture_output=True,
        )

    def exec(self, name: str, command: str, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
        """Run a command inside the container and return captured output."""
        return subprocess.run(
            ["lxc", "exec", name, "--", "bash", "-lc", command],
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout,
        )

    def upload_file(self, name: str, local_path: str, remote_path: str) -> None:
        """Push a local file into the container via ``lxc file push``."""
        container_path = f"{name}{remote_path}"
        subprocess.run(
            ["lxc", "file", "push", "--create-dirs", local_path, container_path],
            check=True,
            text=True,
            capture_output=True,
        )

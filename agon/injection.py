"""Test file injection helpers."""

from __future__ import annotations

import base64
import shlex

from agon.container import container_exec


def inject_files(
    container_name: str,
    files: dict[str, bytes],
    base_path: str,
    timing: str = "post-extract",
) -> None:
    """Inject auxiliary files into the container without modifying the archive."""
    for filename, content in files.items():
        remote_path = f"{base_path.rstrip('/')}/{filename}"
        b64 = base64.b64encode(content).decode()
        cmd = f"echo {shlex.quote(b64)} | base64 -d > {shlex.quote(remote_path)}"
        container_exec(container_name, cmd)

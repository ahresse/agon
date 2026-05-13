"""Archive upload and extraction helpers."""

from __future__ import annotations

from pathlib import Path

from agon.container import container_exec, container_exec_result


def upload_archive(
    container_name: str, archive_path: Path, container_upload_path: str
) -> str:
    """Return the full path inside the container and ensure the upload directory exists."""
    upload_dir = container_upload_path.rstrip("/") or "/"
    container_archive_path = f"{upload_dir}/{archive_path.name}"
    container_exec(container_name, f"mkdir -p '{upload_dir}'")
    return container_archive_path


def extract_archive(
    container_name: str,
    container_archive_path: str,
    container_extract_path: str,
) -> str:
    """Extract the archive into *container_extract_path* and return the project directory."""
    extract_dir = container_extract_path.rstrip("/") or "/"
    archive_name = container_archive_path.lower()
    container_exec(container_name, f"mkdir -p '{extract_dir}'")

    if archive_name.endswith(".zip"):
        container_exec(container_name, f"unzip -q '{container_archive_path}' -d '{extract_dir}'")
    elif archive_name.endswith(".tar.gz"):
        container_exec(container_name, f"tar xf '{container_archive_path}' -C '{extract_dir}'")
    else:
        raise ValueError("Archive must be a .zip or .tar.gz archive.")

    result = container_exec_result(container_name, f"ls -1 '{extract_dir}'")
    if result.returncode != 0:
        raise RuntimeError(
            "Failed to list extracted directory contents.\n"
            f"exit code: {result.returncode}\n"
            f"stdout:\n{result.stdout.strip()}\n"
            f"stderr:\n{result.stderr.strip()}"
        )

    items = [item for item in result.stdout.splitlines() if item]
    if len(items) == 1:
        return f"{extract_dir}/{items[0]}"
    return extract_dir

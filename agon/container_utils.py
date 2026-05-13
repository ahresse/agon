"""Container utility helpers for agon."""

from __future__ import annotations

import inspect
import shlex
import time
import subprocess
import textwrap
import uuid
from pathlib import Path
from typing import Any, Callable

from agon.assessments import AssessmentResult
from agon.assessments import AssessmentSpec
from agon.assessments import run_assessment


def container_exec(container_name: str, shell_command: str) -> None:
    """Run a shell command in the container and raise on non-zero exit."""
    result = container_exec_result(container_name, shell_command)
    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            returncode=result.returncode,
            cmd=["lxc", "exec", container_name, "--", "bash", "-lc", shell_command],
            output=result.stdout,
            stderr=result.stderr,
        )


def container_exec_result(
    container_name: str, shell_command: str
) -> subprocess.CompletedProcess[str]:
    """Run a shell command in the container and return the CompletedProcess."""
    return subprocess.run(
        ["lxc", "exec", container_name, "--", "bash", "-lc", shell_command],
        check=False,
        text=True,
        capture_output=True,
    )


def wait_for_container(container_name: str, timeout_seconds: int = 90) -> None:
    """Block until the container is ready to accept commands or timeout."""
    deadline = time.time() + timeout_seconds

    print("Waiting for container to be ready...")

    while time.time() < deadline:
        try:
            subprocess.run(
                ["lxc", "exec", container_name, "--", "true"],
                check=True,
                text=True,
                capture_output=True,
            )
            container_exec(container_name, "DEBIAN_FRONTEND=noninteractive apt update -qq")
            return
        except subprocess.CalledProcessError:
            time.sleep(1)
    raise TimeoutError(f"Container {container_name} did not become ready in time.")


def ensure_debian_package(container_name: str, package_name: str) -> None:
    """Install a Debian package in the container only if it is not already installed."""
    package = package_name.strip()
    if not package:
        raise ValueError("package_name must not be empty")

    quoted_package = shlex.quote(package)

    check_result = container_exec_result(
        container_name,
        f"dpkg -s {quoted_package} >/dev/null 2>&1",
    )
    if check_result.returncode == 0:
        return

    update_result = container_exec_result(
        container_name,
        "DEBIAN_FRONTEND=noninteractive apt update -qq",
    )
    if update_result.returncode != 0:
        raise RuntimeError(
            "Failed to refresh apt index in container.\n"
            f"exit code: {update_result.returncode}\n"
            f"stdout:\n{update_result.stdout.strip()}\n"
            f"stderr:\n{update_result.stderr.strip()}"
        )

    install_result = container_exec_result(
        container_name,
        (
            "DEBIAN_FRONTEND=noninteractive apt install -y -qq "
            f"--no-install-recommends {quoted_package}"
        ),
    )
    if install_result.returncode != 0:
        raise RuntimeError(
            "Failed to install required Debian package in container.\n"
            f"package: {package}\n"
            f"exit code: {install_result.returncode}\n"
            f"stdout:\n{install_result.stdout.strip()}\n"
            f"stderr:\n{install_result.stderr.strip()}"
        )

    verify_result = container_exec_result(
        container_name,
        f"dpkg -s {quoted_package} >/dev/null 2>&1",
    )
    if verify_result.returncode != 0:
        raise RuntimeError(
            "Package installation command completed but package is still not installed.\n"
            f"package: {package}"
        )


def upload_archive_to_container(
    container_name: str,
    archive_path: Path,
    container_upload_path: str,
) -> str:
    """Upload the archive to the container and return its full path."""
    upload_dir = container_upload_path.rstrip("/") or "/"
    container_archive_path = f"{upload_dir}/{archive_path.name}"
    print(f"Pushing archive to container at {container_archive_path}...")

    # Ensure destination directory exists to avoid push failures on custom paths.
    container_exec(container_name, f"mkdir -p '{upload_dir}'")

    cmd = [
        "lxc",
        "file",
        "push",
        "--create-dirs",
        str(archive_path),
        f"{container_name}{container_archive_path}",
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            text=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Failed to upload archive to container.\n"
            f"command: {' '.join(str(part) for part in cmd)}\n"
            f"exit code: {exc.returncode}\n"
            f"stdout:\n{(exc.stdout or '').strip()}\n"
            f"stderr:\n{(exc.stderr or '').strip()}"
        ) from exc

    return container_archive_path


def extract_archive_in_container(
    container_name: str,
    container_archive_path: str,
    container_extract_path: str,
) -> str:
    """Extract the archive into a container path and return the extracted project path."""
    extract_dir = container_extract_path.rstrip("/") or "/"
    archive_name = container_archive_path.lower()
    print(f"Extracting archive in container at {container_extract_path}...")
    container_exec(container_name, f"mkdir -p '{extract_dir}'")
    if archive_name.endswith(".zip"):
        ensure_debian_package(container_name, "unzip")
        container_exec(container_name, f"unzip -q '{container_archive_path}' -d '{extract_dir}'")
    elif archive_name.endswith(".tar.gz"):
        ensure_debian_package(container_name, "tar")
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


def setup_apt_cache_sharing(container_name: str) -> None:
    """Mount the host's apt cache into the container to reuse cached packages."""
    try:
        subprocess.run(
            [
                "lxc",
                "config",
                "device",
                "add",
                container_name,
                "apt-cache",
                "disk",
                "source=/var/cache/apt",
                "path=/var/cache/apt",
            ],
            check=True,
            text=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        pass


def show_directory_tree(container_name: str, target_path: str) -> None:
    """Display the directory tree for a path in the container."""
    ensure_debian_package(container_name, "tree")
    print(f"\nContents of {target_path}:")
    result = container_exec_result(container_name, f"tree -hClsa '{target_path}'")
    if result.returncode != 0:
        raise RuntimeError(
            "Failed to display extracted contents with tree.\n"
            f"exit code: {result.returncode}\n"
            f"stdout:\n{result.stdout.strip()}\n"
            f"stderr:\n{result.stderr.strip()}"
        )
    print(result.stdout)


def delete_container(container_name: str) -> None:
    """Force-delete a container, ignoring errors."""
    subprocess.run(
        ["lxc", "delete", "--force", container_name],
        check=False,
        text=True,
        capture_output=True,
    )


def open_shell(container_name: str, container_user: str) -> None:
    """Open an interactive shell session in the container."""
    banner = "=" * 72
    print(f"\n{banner}")
    print(f"Opening shell session in container as {container_user} user.")
    print("Type 'exit' to return to the host.")
    print(f"{banner}\n")
    subprocess.run(
        ["lxc", "exec", container_name, "--", "su", "-", container_user],
        check=False,
        stdin=None,
        stdout=None,
        stderr=None,
    )


def container_run(
    python_func: Callable[[], Any],
    image: str = "ubuntu:24.04",
    timeout_seconds: int = 90,
) -> str:
    """Run a zero-argument Python function inside a temporary container.

    The function source code is executed in the container with ``python3``.
    Returns captured stdout from that execution.
    """
    if not callable(python_func):
        raise TypeError("python_func must be callable")

    signature = inspect.signature(python_func)
    required_parameters = [
        p
        for p in signature.parameters.values()
        if p.default is inspect.Signature.empty
        and p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    ]
    if required_parameters:
        raise ValueError("python_func must not require arguments")

    try:
        function_source = textwrap.dedent(inspect.getsource(python_func)).strip()
    except (OSError, TypeError) as exc:
        raise ValueError("Unable to retrieve source for python_func") from exc

    function_name = python_func.__name__
    container_name = f"agon-run-{uuid.uuid4().hex[:8]}"

    script = (
        f"{function_source}\n\n"
        "if __name__ == '__main__':\n"
        f"    _result = {function_name}()\n"
        "    if _result is not None:\n"
        "        print(_result)\n"
    )
    shell_command = f"python3 - <<'PY'\n{script}\nPY"

    subprocess.run(
        ["lxc", "launch", image, container_name],
        check=True,
        text=True,
        capture_output=True,
    )

    try:
        wait_for_container(container_name, timeout_seconds=timeout_seconds)
        result = container_exec_result(container_name, shell_command)
        if result.returncode != 0:
            raise RuntimeError(
                "Failed to execute Python function in container.\n"
                f"exit code: {result.returncode}\n"
                f"stdout:\n{result.stdout.strip()}\n"
                f"stderr:\n{result.stderr.strip()}"
            )
        return result.stdout
    finally:
        delete_container(container_name)


def run_assessment_in_container(
    container_name: str,
    assessment: AssessmentSpec,
    target_path: str,
) -> AssessmentResult:
    """Run a generic assessment inside a container."""
    banner = "=" * 72
    print(f"\n{banner}")
    print(f"ASSESSMENT START :: {assessment.name} :: target={target_path}")
    print(banner)

    result = run_assessment(
        assessment,
        target_path,
        command_runner=lambda command: container_exec_result(container_name, command),
        dependency_installer=lambda package: ensure_debian_package(container_name, package),
    )

    print(f"ASSESSMENT END   :: {assessment.name} :: exit_code={result.returncode}")
    print("-" * 72)

    if result.stdout:
        print("STDOUT")
        print("-" * 72)
        print(result.stdout)
    if result.stderr:
        print("STDERR")
        print("-" * 72)
        print(result.stderr)

    if not result.stdout and not result.stderr:
        print("No stdout/stderr captured for this assessment.")

    print(banner)
    return result

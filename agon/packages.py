"""Debian package installation helpers."""

from __future__ import annotations

import shlex

from agon.container import container_exec_result


def ensure_packages(container_name: str, package_names: tuple[str, ...]) -> bool:
    """Install missing Debian packages inside the container.

    Returns ``True`` if all packages are present after the call,
    ``False`` if installation fails.
    """
    for package in package_names:
        check = container_exec_result(
            container_name,
            f"dpkg -s {shlex.quote(package)} >/dev/null 2>&1",
        )
        if check.returncode == 0:
            continue

        install = container_exec_result(
            container_name,
            (
                "DEBIAN_FRONTEND=noninteractive apt install -y -qq "
                f"--no-install-recommends {shlex.quote(package)}"
            ),
        )
        if install.returncode != 0:
            return False

        verify = container_exec_result(
            container_name,
            f"dpkg -s {shlex.quote(package)} >/dev/null 2>&1",
        )
        if verify.returncode != 0:
            return False

    return True

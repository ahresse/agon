"""Runner selection (Constitution Principle II).

Returns the production LXD runner by default; the non-isolating local runner is
only selected when explicitly enabled for CI/dev.
"""
from __future__ import annotations

from src.config import settings
from src.runners.container_runner import ContainerRunner, LocalSubprocessRunner, LXDRunner


def get_runner() -> ContainerRunner:
    if settings.use_local_runner:
        return LocalSubprocessRunner()
    return LXDRunner(image_profile=settings.lxd_image_profile)

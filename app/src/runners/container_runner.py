"""Container execution runners (Constitution Principle II - NON-NEGOTIABLE).

Every test plugin runs inside an isolated, disposable container. `LXDRunner` is
the production runner. `LocalSubprocessRunner` exists ONLY for environments where
LXD is unavailable (CI/dev) and MUST NOT be used in production; it is explicitly
marked non-isolating so it can never be mistaken for the real thing.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.tests_plugins.registry import PluginInput, PluginOutput, TestPlugin


class ContainerRunner(ABC):
    """Abstract execution boundary for a single test run."""

    #: True only for runners that provide real container isolation.
    isolated: bool = False

    @abstractmethod
    def run(self, plugin: TestPlugin, payload: PluginInput) -> PluginOutput:
        """Execute the plugin against the submission inside a fresh container."""
        raise NotImplementedError


class LXDRunner(ContainerRunner):
    """Production runner: one disposable LXD container per test run.

    Creates a fresh container from a configured Python base image, injects the
    candidate source, executes the plugin under a hard timeout, reads back only
    the structured {grade, pros, cons}, then destroys the container.
    """

    isolated = True

    def __init__(self, image_profile: str) -> None:
        self.image_profile = image_profile

    def run(self, plugin: TestPlugin, payload: PluginInput) -> PluginOutput:
        # Requires pylxd + a running LXD daemon on the host (Ubuntu/arm64 target).
        # Implemented against the LXD API: launch → push source → exec → collect
        # → delete. Kept import-local so the module imports without pylxd present.
        from src.runners.lxd_backend import execute_in_lxd  # pragma: no cover

        return execute_in_lxd(self.image_profile, plugin, payload)  # pragma: no cover


class LocalSubprocessRunner(ContainerRunner):
    """NON-ISOLATING fallback for CI/dev only. Never use in production."""

    isolated = False

    def run(self, plugin: TestPlugin, payload: PluginInput) -> PluginOutput:
        return plugin.run(payload)

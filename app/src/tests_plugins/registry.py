"""Test plugin interface and registry (Constitution Principle III).

Plugins conform to a stable weight-in / grade-out contract and register under a
stable key so new tests can be added without changing framework core.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol


@dataclass(frozen=True)
class PluginInput:
    submission_path: str  # path *inside the container* to the candidate source
    config: dict = field(default_factory=dict)
    timeout_seconds: int = 60


@dataclass(frozen=True)
class PluginOutput:
    grade: float  # 0-100 (Principle I, FR-005)
    pros: list[str] = field(default_factory=list)
    cons: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not (0 <= self.grade <= 100):
            raise ValueError(f"Plugin grade must be within 0-100, got {self.grade}.")


class TestPlugin(Protocol):
    key: str

    def run(self, payload: PluginInput) -> PluginOutput:  # pragma: no cover - protocol
        ...


class PluginRegistry:
    """Registry mapping stable keys to plugin factories.

    Adding a plugin here requires no change to scheduling/grading core.
    """

    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], TestPlugin]] = {}

    def register(self, key: str, factory: Callable[[], TestPlugin]) -> None:
        if key in self._factories:
            raise ValueError(f"Plugin key already registered: {key}")
        self._factories[key] = factory

    def create(self, key: str) -> TestPlugin:
        if key not in self._factories:
            raise KeyError(f"No plugin registered under key: {key}")
        return self._factories[key]()

    def keys(self) -> list[str]:
        return sorted(self._factories)


registry = PluginRegistry()

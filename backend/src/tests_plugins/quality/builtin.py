"""Central registration of the built-in Python quality metric plugins.

Importing and calling `register_quality_plugins(registry)` wires all six metric
plugins. Idempotent so it can be called on every app startup / in tests.
"""
from __future__ import annotations

from src.tests_plugins.quality import (
    complexity_radon,
    formatting_black,
    git_history,
    lint_ruff,
    security_bandit,
    stdlib_idioms,
    type_check_mypy,
)
from src.tests_plugins.registry import PluginRegistry

# (key, human name, factory) for each built-in metric plugin.
QUALITY_PLUGINS = [
    (lint_ruff.KEY, "Lint (ruff)", lint_ruff.factory),
    (complexity_radon.KEY, "Complexity (radon)", complexity_radon.factory),
    (stdlib_idioms.KEY, "Standard-library idioms", stdlib_idioms.factory),
    (type_check_mypy.KEY, "Type checking (mypy)", type_check_mypy.factory),
    (security_bandit.KEY, "Security (bandit)", security_bandit.factory),
    (formatting_black.KEY, "Formatting & docs (black)", formatting_black.factory),
    (git_history.KEY, "Git commit quality", git_history.factory),
]


def register_quality_plugins(registry: PluginRegistry) -> None:
    existing = set(registry.keys())
    for key, _name, factory in QUALITY_PLUGINS:
        if key not in existing:
            registry.register(key, factory)

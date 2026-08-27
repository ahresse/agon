"""AI-agent test plugin (T069, US5, FR-013).

A theme-scoped AI-agent test that runs in isolation like any other plugin and
folds into the same weighted grading model. It calls a pluggable AI provider from
inside its container and returns the standard {grade, pros, cons} shape.
"""
from __future__ import annotations

import os

from src.config import settings
from src.tests_plugins.ai_provider import get_provider
from src.tests_plugins.registry import PluginInput, PluginOutput

KEY = "ai.readability"


class AIAgentPlugin:
    key = KEY

    def run(self, payload: PluginInput) -> PluginOutput:
        theme = str(payload.config.get("theme") or "readability")
        source = _concat_sources(payload.submission_path)
        if not source.strip():
            return PluginOutput(grade=0.0, cons=["No Python source found to assess."])
        provider = get_provider(settings.ai_provider_url)
        grade, pros, cons = provider.assess(theme, source)
        return PluginOutput(grade=grade, pros=pros, cons=cons)


def _concat_sources(root: str) -> str:
    parts: list[str] = []
    if os.path.isfile(root):
        paths = [root] if root.endswith(".py") else []
    else:
        paths = []
        for dirpath, _dirs, files in os.walk(root):
            for f in files:
                if f.endswith(".py"):
                    paths.append(os.path.join(dirpath, f))
    for p in sorted(paths):
        with open(p, "r", encoding="utf-8", errors="replace") as fh:
            parts.append(fh.read())
    return "\n".join(parts)


def factory() -> AIAgentPlugin:
    return AIAgentPlugin()

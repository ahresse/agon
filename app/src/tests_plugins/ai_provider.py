"""Pluggable AI provider interface (T068, US5, Constitution II/III).

Abstracts the concrete model/endpoint behind a small interface so the AI-agent
test can obtain intelligence from *inside* its container without hard-coding a
specific provider. A deterministic `StubAIProvider` is used when no provider is
configured, keeping tests reproducible and self-hosting viable offline.
"""
from __future__ import annotations

from typing import Protocol


class AIProvider(Protocol):
    def assess(self, theme: str, source: str) -> tuple[float, list[str], list[str]]:
        """Return (grade 0-100, pros, cons) for the given theme over the source."""
        ...


class StubAIProvider:
    """Offline, deterministic provider. Grades on a simple readability proxy so
    the AI-agent test yields reproducible output without an external model.
    """

    def assess(self, theme: str, source: str) -> tuple[float, list[str], list[str]]:
        lines = [ln for ln in source.splitlines() if ln.strip()]
        if not lines:
            return 0.0, [], ["No source to assess."]
        commented = sum(1 for ln in lines if ln.lstrip().startswith("#"))
        comment_ratio = commented / len(lines)
        avg_len = sum(len(ln) for ln in lines) / len(lines)
        grade = max(0.0, min(100.0, 100.0 * comment_ratio + max(0.0, 80.0 - avg_len)))
        pros = [f"Theme '{theme}': {comment_ratio:.0%} of lines are comments."]
        cons = [] if avg_len < 80 else ["Lines are long on average; consider wrapping."]
        return round(grade, 2), pros, cons


def get_provider(provider_url: str | None) -> AIProvider:
    """Return a configured provider, or the deterministic stub when unset."""
    # A real HTTP-backed provider would be constructed here from provider_url.
    return StubAIProvider()

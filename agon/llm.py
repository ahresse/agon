"""LLM client for agent-based assessments.

Supports any OpenAI-compatible HTTP endpoint via the ``requests`` library.
Configuration is read from environment variables:

* ``AGON_LLM_ENDPOINT`` — base URL (default: ``https://api.openai.com/v1``)
* ``AGON_LLM_API_KEY`` — API key (required unless the endpoint needs none)
* ``AGON_LLM_MODEL`` — model name (default: ``gpt-4o-mini``)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import requests


DEFAULT_ENDPOINT = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"


@dataclass
class LLMConfig:
    """Runtime configuration for the LLM backend."""

    endpoint: str
    api_key: str | None
    model: str

    @classmethod
    def from_env(cls) -> LLMConfig:
        """Build a config from environment variables."""
        return cls(
            endpoint=os.getenv("AGON_LLM_ENDPOINT", DEFAULT_ENDPOINT).rstrip("/"),
            api_key=os.getenv("AGON_LLM_API_KEY") or None,
            model=os.getenv("AGON_LLM_MODEL", DEFAULT_MODEL),
        )


def _build_messages(prompt: str, source_tree: str) -> list[dict[str, str]]:
    """Assemble the chat-completion messages for an assessment call."""
    system_text = (
        "You are an automated code-assessment agent. "
        "You evaluate source code / documentation against a rubric and return a JSON object "
        "with exactly two keys: \"score\" (a number between 0 and 20, inclusive) "
        "and \"reasoning\" (a short explanation of the awarded score). "
        "Return ONLY the JSON object, with no markdown code fences."
    )
    user_text = (
        f"Assessment criteria:\n{prompt}\n\n"
        f"Source tree:\n{source_tree}\n\n"
        "Respond with JSON only."
    )
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]


def _parse_response(raw: str) -> tuple[float, str]:
    """Extract ``(score, reasoning)`` from the LLM's raw text output.

    Tries JSON parsing first, then falls back to crude regex extraction.
    """
    # Strip markdown fences if the model ignored the instruction
    cleaned = raw.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    # Attempt strict JSON parsing
    try:
        data: Any = json.loads(cleaned)
        if isinstance(data, dict):
            score = float(data.get("score", 0))
            reasoning = str(data.get("reasoning", ""))
            return score, reasoning
    except (json.JSONDecodeError, ValueError, TypeError):
        pass

    # Fallback: look for a number near the start or end of the text
    import re

    numbers = [float(m) for m in re.findall(r"\b(\d+(?:\.\d+)?)\b", cleaned)]
    score = numbers[0] if numbers else 0.0
    reasoning = cleaned
    return score, reasoning


def call_ai_agent(prompt: str, source_tree: str) -> tuple[float, str]:
    """Send an agent-based grading request to the configured LLM endpoint.

    Returns ``(score, reasoning)`` where *score* is in the range [0, 20].
    Raises ``RuntimeError`` on network or configuration failures.
    """
    config = LLMConfig.from_env()

    url = f"{config.endpoint}/chat/completions"
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"

    payload = {
        "model": config.model,
        "messages": _build_messages(prompt, source_tree),
        "temperature": 0.3,
        "max_tokens": 4096,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"LLM request failed: {exc}") from exc

    try:
        data = response.json()
        raw_content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as exc:
        raise RuntimeError(f"Unexpected LLM response shape: {exc}") from exc

    score, reasoning = _parse_response(raw_content)
    return score, reasoning

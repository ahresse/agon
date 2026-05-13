"""Unit tests for the agon LLM client."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from agon.llm import (
    DEFAULT_ENDPOINT,
    DEFAULT_MODEL,
    LLMConfig,
    _build_messages,
    _parse_response,
    call_ai_agent,
)


def test_llm_config_from_env_defaults() -> None:
    """LLMConfig.from_env shall use sensible defaults when no env vars are set."""
    config = LLMConfig.from_env()
    assert config.endpoint == DEFAULT_ENDPOINT
    assert config.api_key is None
    assert config.model == DEFAULT_MODEL


def test_llm_config_from_env_override() -> None:
    """LLMConfig.from_env shall honour environment overrides."""
    with patch.dict(
        os.environ,
        {
            "AGON_LLM_ENDPOINT": "https://custom.example.com/v1",
            "AGON_LLM_API_KEY": "sk-test",
            "AGON_LLM_MODEL": "custom-model",
        },
        clear=False,
    ):
        config = LLMConfig.from_env()
    assert config.endpoint == "https://custom.example.com/v1"
    assert config.api_key == "sk-test"
    assert config.model == "custom-model"


def test_llm_config_strips_trailing_slash() -> None:
    """The endpoint shall be normalised to have no trailing slash."""
    with patch.dict(os.environ, {"AGON_LLM_ENDPOINT": "http://localhost:1234/"}, clear=False):
        config = LLMConfig.from_env()
    assert config.endpoint == "http://localhost:1234"


def test_build_messages_contains_system_and_user() -> None:
    """_build_messages shall return a list with system and user roles."""
    msgs = _build_messages("Rate docs.", "# README")
    assert len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert "JSON" in msgs[0]["content"]
    assert msgs[1]["role"] == "user"
    assert "Rate docs." in msgs[1]["content"]
    assert "# README" in msgs[1]["content"]


def test_parse_response_valid_json() -> None:
    """_parse_response shall extract score and reasoning from clean JSON."""
    raw = '{"score": 15.5, "reasoning": "Good but terse."}'
    score, reasoning = _parse_response(raw)
    assert score == 15.5
    assert reasoning == "Good but terse."


def test_parse_response_json_with_markdown_fences() -> None:
    """_parse_response shall strip markdown code fences before parsing."""
    raw = '```json\n{"score": 12.0, "reasoning": "OK."}\n```'
    score, reasoning = _parse_response(raw)
    assert score == 12.0
    assert reasoning == "OK."


def test_parse_response_plain_text_fallback() -> None:
    """When the response is not JSON, _parse_response shall fall back to the
    first number found and use the full text as reasoning."""
    raw = "The project deserves a 14.5 out of 20. Nice structure."
    score, reasoning = _parse_response(raw)
    assert score == 14.5
    assert reasoning == raw


def test_call_ai_agent_happy_path() -> None:
    """call_ai_agent shall POST to the configured endpoint and return parsed
    (score, reasoning)."""
    fake_response = MagicMock()
    fake_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '{"score": 18.0, "reasoning": "Excellent."}'
                }
            }
        ]
    }
    fake_response.raise_for_status.return_value = None

    with patch("agon.llm.requests.post", return_value=fake_response) as mock_post:
        with patch.dict(
            os.environ,
            {"AGON_LLM_API_KEY": "sk-test", "AGON_LLM_MODEL": "gpt-4"},
            clear=False,
        ):
            score, reasoning = call_ai_agent("Rate.", "src/main.py")

    assert score == 18.0
    assert reasoning == "Excellent."
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args[1]
    assert call_kwargs["headers"]["Authorization"] == "Bearer sk-test"
    assert call_kwargs["json"]["model"] == "gpt-4"


def test_call_ai_agent_no_api_key_omits_auth() -> None:
    """When no API key is configured, call_ai_agent shall omit the Authorization
    header (useful for local endpoints)."""
    fake_response = MagicMock()
    fake_response.json.return_value = {
        "choices": [{"message": {"content": '{"score": 10, "reasoning": "Meh."}'}}]
    }
    fake_response.raise_for_status.return_value = None

    with patch("agon.llm.requests.post", return_value=fake_response) as mock_post:
        with patch.dict(os.environ, {}, clear=True):
            score, _ = call_ai_agent("Rate.", "src/main.py")

    call_kwargs = mock_post.call_args[1]
    assert "Authorization" not in call_kwargs["headers"]


def test_call_ai_agent_raises_on_http_error() -> None:
    """call_ai_agent shall raise RuntimeError on HTTP failures."""
    from requests import HTTPError

    fake_response = MagicMock()
    fake_response.raise_for_status.side_effect = HTTPError("401 Unauthorized")

    with patch("agon.llm.requests.post", return_value=fake_response):
        with pytest.raises(RuntimeError):
            call_ai_agent("Rate.", "src/main.py")


def test_call_ai_agent_raises_on_bad_response_shape() -> None:
    """call_ai_agent shall raise RuntimeError when the response JSON lacks the
    expected shape."""
    fake_response = MagicMock()
    fake_response.json.return_value = {"error": "invalid"}
    fake_response.raise_for_status.return_value = None

    with patch("agon.llm.requests.post", return_value=fake_response):
        with pytest.raises(RuntimeError):
            call_ai_agent("Rate.", "src/main.py")

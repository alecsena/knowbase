"""Tests for LLM client dispatch and provider-level helpers."""

from unittest.mock import patch

import pytest

from altcoin_analyzer.llm.client import LLMError, _resolve_model


def test_resolve_model_uses_override() -> None:
    assert _resolve_model("anthropic", "custom-model") == "custom-model"


def test_resolve_model_anthropic_default() -> None:
    from altcoin_analyzer.config import settings
    result = _resolve_model("anthropic", "")
    assert result == settings.anthropic_model


def test_resolve_model_openrouter_default() -> None:
    from altcoin_analyzer.config import settings
    result = _resolve_model("openrouter", "")
    assert result == settings.openrouter_model


def test_resolve_model_openai_default() -> None:
    from altcoin_analyzer.config import settings
    result = _resolve_model("openai", "")
    assert result == settings.openai_model


@pytest.mark.asyncio
async def test_dispatch_unknown_provider_raises() -> None:
    from altcoin_analyzer.llm.client import _dispatch
    with pytest.raises(LLMError, match="Unknown provider"):
        await _dispatch("unknown_provider", "model", "prompt")


@pytest.mark.asyncio
async def test_call_anthropic_raises_when_no_key() -> None:
    from altcoin_analyzer.llm.client import _call_anthropic
    with patch("altcoin_analyzer.llm.client.settings") as mock_settings:
        mock_settings.anthropic_api_key = ""
        with pytest.raises(LLMError, match="ANTHROPIC_API_KEY"):
            await _call_anthropic("prompt", "model")


@pytest.mark.asyncio
async def test_call_openai_compatible_raises_when_no_key() -> None:
    from altcoin_analyzer.llm.client import _call_openai_compatible
    with pytest.raises(LLMError, match="OPENAI_API_KEY"):
        await _call_openai_compatible("prompt", "gpt-4o", "https://api.openai.com/v1", "", "openai")


@pytest.mark.asyncio
async def test_llm_client_no_fallback_configured() -> None:
    from altcoin_analyzer.llm.client import LLMClient

    with (
        patch("altcoin_analyzer.llm.client.settings") as mock_settings,
        patch("altcoin_analyzer.llm.client._dispatch") as mock_dispatch,
    ):
        mock_settings.llm_provider = "anthropic"
        mock_settings.llm_fallback_provider = ""
        mock_settings.anthropic_model = "claude-sonnet-4-6"

        mock_dispatch.side_effect = LLMError("primary down")

        client = LLMClient()
        with pytest.raises(LLMError):
            await client.decide("test prompt")

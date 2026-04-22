import json
from unittest.mock import patch

import pytest

from altcoin_analyzer.llm.client import LLMClient, LLMError, _extract_json
from altcoin_analyzer.llm.prompts import build_decision_prompt
from tests.conftest import LLM_DECISION_JSON


def test_extract_json_strips_markdown() -> None:
    raw = "```json\n{\"decision\": \"BUY\"}\n```"
    assert _extract_json(raw) == '{"decision": "BUY"}'


def test_extract_json_passthrough() -> None:
    raw = '{"decision": "HOLD"}'
    assert _extract_json(raw) == raw


def test_build_decision_prompt_contains_symbol() -> None:
    prompt = build_decision_prompt(
        symbol="SOL",
        risk_profile="moderate",
        time_horizon="medium",
        scores={"overall": 7.5},
        market_data={"price_usd": 150.0},
        onchain_data={"tvl_usd": 5e9},
        red_flags=["high FDV ratio"],
        green_flags=["audited"],
    )
    assert "SOL" in prompt
    assert "moderate" in prompt
    assert "medium" in prompt
    assert "high FDV ratio" in prompt
    assert "audited" in prompt


@pytest.mark.asyncio
async def test_llm_client_parse_valid_json() -> None:
    client = LLMClient()
    decision = client._parse(LLM_DECISION_JSON)
    assert decision.decision == "BUY"
    assert 0 < decision.confidence <= 1.0
    assert isinstance(decision.key_risks, list)


@pytest.mark.asyncio
async def test_llm_client_raises_on_invalid_json() -> None:
    client = LLMClient()
    with pytest.raises(LLMError, match="invalid JSON"):
        client._parse("this is not json")


@pytest.mark.asyncio
async def test_llm_client_raises_on_invalid_schema() -> None:
    client = LLMClient()
    bad = json.dumps({"decision": "MAYBE", "confidence": 0.5})  # invalid decision value
    with pytest.raises(LLMError):
        client._parse(bad)


@pytest.mark.asyncio
async def test_llm_client_clamps_out_of_range_fields() -> None:
    client = LLMClient()
    raw = json.dumps({
        "decision": "BUY",
        "confidence": 1.5,  # should clamp to 1.0
        "reasoning": "test",
        "key_risks": [],
        "key_opportunities": [],
        "suggested_allocation_pct": 50,  # should clamp to 10
        "stop_loss_suggestion_pct": 100,  # should clamp to 30
        "reevaluation_trigger": "none",
    })
    decision = client._parse(raw)
    assert decision.confidence == 1.0
    assert decision.suggested_allocation_pct == 10.0
    assert decision.stop_loss_suggestion_pct == 30.0


@pytest.mark.asyncio
async def test_llm_client_uses_fallback_on_primary_failure() -> None:
    with (
        patch("altcoin_analyzer.llm.client.settings") as mock_settings,
        patch("altcoin_analyzer.llm.client._dispatch") as mock_dispatch,
    ):
        mock_settings.llm_provider = "anthropic"
        mock_settings.llm_fallback_provider = "openrouter"
        mock_settings.llm_fallback_model = "meta-llama/llama-3.1-70b-instruct"
        mock_settings.anthropic_model = "claude-sonnet-4-6"
        mock_settings.openrouter_model = "openai/gpt-4o"
        mock_settings.openai_model = "gpt-4o"

        mock_dispatch.side_effect = [
            LLMError("primary failed"),
            (LLM_DECISION_JSON, "openrouter/meta-llama/llama-3.1-70b-instruct"),
        ]

        client = LLMClient()
        decision, provider = await client.decide("test prompt")
        assert decision.decision == "BUY"
        assert "openrouter" in provider


@pytest.mark.asyncio
async def test_llm_client_raises_when_both_providers_fail() -> None:
    with (
        patch("altcoin_analyzer.llm.client.settings") as mock_settings,
        patch("altcoin_analyzer.llm.client._dispatch") as mock_dispatch,
    ):
        mock_settings.llm_provider = "anthropic"
        mock_settings.llm_fallback_provider = "openrouter"
        mock_settings.llm_fallback_model = "llama"
        mock_settings.anthropic_model = "claude-sonnet-4-6"

        mock_dispatch.side_effect = [
            LLMError("primary down"),
            LLMError("fallback down"),
        ]

        client = LLMClient()
        with pytest.raises(LLMError):
            await client.decide("test")

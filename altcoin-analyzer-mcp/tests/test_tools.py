from unittest.mock import AsyncMock, patch

import pytest

from altcoin_analyzer.models.altcoin import AltcoinData
from altcoin_analyzer.models.decision import LLMDecision


def _make_mock_altcoin(sample_altcoin: AltcoinData) -> AsyncMock:
    mock = AsyncMock(return_value=sample_altcoin)
    return mock


@pytest.mark.asyncio
async def test_score_altcoin_returns_scoring_result(sample_altcoin: AltcoinData) -> None:
    with patch("altcoin_analyzer.tools.score.assemble_altcoin_data", AsyncMock(return_value=sample_altcoin)):
        from altcoin_analyzer.tools.score import score_altcoin
        result = await score_altcoin("SOL")
        assert "overall" in result
        assert "fundamentals" in result
        assert 0 <= result["overall"] <= 10


@pytest.mark.asyncio
async def test_analyze_altcoin_no_llm(sample_altcoin: AltcoinData) -> None:
    with patch("altcoin_analyzer.tools.analyze.assemble_altcoin_data", AsyncMock(return_value=sample_altcoin)):
        from altcoin_analyzer.tools.analyze import analyze_altcoin
        result = await analyze_altcoin("SOL", include_llm_reasoning=False)
        assert result["symbol"] == "SOL"
        assert result["decision"] in ("BUY", "HOLD", "AVOID")
        assert "scores" in result
        assert "DISCLAIMER" in result


@pytest.mark.asyncio
async def test_analyze_altcoin_with_llm(sample_altcoin: AltcoinData) -> None:
    from altcoin_analyzer.llm.client import LLMClient

    mock_decision = LLMDecision.model_validate(
        {
            "decision": "BUY",
            "confidence": 0.78,
            "reasoning": "Solana has strong fundamentals.",
            "key_risks": ["volatility"],
            "key_opportunities": ["ecosystem growth"],
            "suggested_allocation_pct": 5,
            "stop_loss_suggestion_pct": 15,
            "reevaluation_trigger": "TVL drops 20%",
        }
    )

    with (
        patch("altcoin_analyzer.tools.analyze.assemble_altcoin_data", AsyncMock(return_value=sample_altcoin)),
        patch.object(LLMClient, "decide", AsyncMock(return_value=(mock_decision, "anthropic/claude-sonnet-4-6"))),
    ):
        from altcoin_analyzer.tools.analyze import analyze_altcoin
        result = await analyze_altcoin("SOL", include_llm_reasoning=True)
        assert result["decision"] == "BUY"
        assert result["confidence"] == 0.78
        assert result["llm_provider_used"] == "anthropic/claude-sonnet-4-6"


@pytest.mark.asyncio
async def test_analyze_altcoin_llm_failure_fallback(sample_altcoin: AltcoinData) -> None:
    from altcoin_analyzer.llm.client import LLMClient, LLMError

    with (
        patch("altcoin_analyzer.tools.analyze.assemble_altcoin_data", AsyncMock(return_value=sample_altcoin)),
        patch.object(LLMClient, "decide", AsyncMock(side_effect=LLMError("all providers failed"))),
    ):
        from altcoin_analyzer.tools.analyze import analyze_altcoin
        result = await analyze_altcoin("SOL", include_llm_reasoning=True)
        assert result["decision"] == "HOLD"
        assert result["llm_provider_used"] == "fallback_rule_based"


@pytest.mark.asyncio
async def test_compare_altcoins_ranks_correctly(sample_altcoin: AltcoinData) -> None:
    with patch("altcoin_analyzer.tools.compare.assemble_altcoin_data", AsyncMock(return_value=sample_altcoin)):
        from altcoin_analyzer.tools.compare import compare_altcoins
        result = await compare_altcoins(["SOL", "AVAX"])
        assert "ranking" in result
        assert len(result["ranking"]) == 2
        assert result["ranking"][0]["rank"] == 1
        assert result["ranking"][1]["rank"] == 2


@pytest.mark.asyncio
async def test_compare_altcoins_rejects_too_few_symbols(sample_altcoin: AltcoinData) -> None:
    from altcoin_analyzer.tools.compare import compare_altcoins
    result = await compare_altcoins(["SOL"])
    assert "error" in result


@pytest.mark.asyncio
async def test_compare_altcoins_partial_failure(sample_altcoin: AltcoinData) -> None:
    from altcoin_analyzer.providers.base import ProviderError

    async def mock_assemble(symbol: str) -> AltcoinData:
        if symbol == "FAIL":
            raise ProviderError("provider down")
        return sample_altcoin

    with patch("altcoin_analyzer.tools.compare.assemble_altcoin_data", side_effect=mock_assemble):
        from altcoin_analyzer.tools.compare import compare_altcoins
        result = await compare_altcoins(["SOL", "FAIL"])
        assert len(result["ranking"]) == 1
        assert len(result["errors"]) == 1

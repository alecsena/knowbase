from unittest.mock import AsyncMock, patch

import pytest

from altcoin_analyzer.providers.base import ProviderError


@pytest.mark.asyncio
async def test_assemble_raises_on_coingecko_failure() -> None:
    with (
        patch("altcoin_analyzer.tools._assembler.CoinGeckoProvider") as MockCG,
        patch("altcoin_analyzer.tools._assembler.DeFiLlamaProvider") as MockDL,
        patch("altcoin_analyzer.tools._assembler.GitHubMetricsProvider") as MockGH,
    ):
        cg_inst = MockCG.return_value
        cg_inst.fetch = AsyncMock(return_value={"error": "rate limited"})
        cg_inst.close = AsyncMock()

        for MockP in [MockDL, MockGH]:
            inst = MockP.return_value
            inst.fetch = AsyncMock(return_value={})
            inst.close = AsyncMock()

        from altcoin_analyzer.tools._assembler import assemble_altcoin_data
        with pytest.raises(ProviderError):
            await assemble_altcoin_data("SOL")


@pytest.mark.asyncio
async def test_assemble_succeeds_with_partial_providers(coingecko_response: dict) -> None:
    from altcoin_analyzer.providers.coingecko import CoinGeckoProvider

    cg = CoinGeckoProvider()
    cg_data = cg._parse(coingecko_response, "SOL")

    with (
        patch("altcoin_analyzer.tools._assembler.CoinGeckoProvider") as MockCG,
        patch("altcoin_analyzer.tools._assembler.DeFiLlamaProvider") as MockDL,
        patch("altcoin_analyzer.tools._assembler.GitHubMetricsProvider") as MockGH,
    ):
        cg_inst = MockCG.return_value
        cg_inst.fetch = AsyncMock(return_value=cg_data)
        cg_inst.close = AsyncMock()

        dl_inst = MockDL.return_value
        dl_inst.fetch = AsyncMock(side_effect=Exception("DeFiLlama down"))
        dl_inst.close = AsyncMock()

        gh_inst = MockGH.return_value
        gh_inst.fetch = AsyncMock(side_effect=Exception("GitHub down"))
        gh_inst.close = AsyncMock()

        from altcoin_analyzer.tools._assembler import assemble_altcoin_data
        result = await assemble_altcoin_data("SOL")
        assert result.symbol == "SOL"
        assert "defillama_tvl" in result.data_gaps
        assert "github_metrics" in result.data_gaps


@pytest.mark.asyncio
async def test_assemble_includes_known_fundamentals(coingecko_response: dict) -> None:
    from altcoin_analyzer.providers.coingecko import CoinGeckoProvider

    cg = CoinGeckoProvider()
    cg_data = cg._parse(coingecko_response, "SOL")

    with (
        patch("altcoin_analyzer.tools._assembler.CoinGeckoProvider") as MockCG,
        patch("altcoin_analyzer.tools._assembler.DeFiLlamaProvider") as MockDL,
        patch("altcoin_analyzer.tools._assembler.GitHubMetricsProvider") as MockGH,
    ):
        for MockP, data in [(MockCG, cg_data), (MockDL, {}), (MockGH, {})]:
            inst = MockP.return_value
            inst.fetch = AsyncMock(return_value=data)
            inst.close = AsyncMock()

        from altcoin_analyzer.tools._assembler import assemble_altcoin_data
        result = await assemble_altcoin_data("SOL")
        assert result.fundamentals.is_audited is True
        assert "Kudelski" in result.fundamentals.audit_firms

import httpx
import pytest
import respx

from altcoin_analyzer.providers.coingecko import CoinGeckoProvider
from altcoin_analyzer.providers.coingecko import _cache as cg_cache
from altcoin_analyzer.providers.defillama import DeFiLlamaProvider
from altcoin_analyzer.providers.defillama import _cache as dl_cache


@pytest.fixture(autouse=True)
async def clear_provider_caches() -> None:
    await cg_cache.clear()
    await dl_cache.clear()


@pytest.mark.asyncio
@respx.mock
async def test_coingecko_fetch_success(coingecko_response: dict) -> None:
    respx.get("https://api.coingecko.com/api/v3/coins/solana").mock(
        return_value=httpx.Response(200, json=coingecko_response)
    )
    provider = CoinGeckoProvider()
    result = await provider.fetch("SOL")
    assert result["symbol"] == "SOL"
    assert result["price_usd"] == 150.0
    assert result["market_cap_usd"] == 70_000_000_000
    assert result["liquidity_ratio"] == pytest.approx(0.05, rel=0.01)


@pytest.mark.asyncio
@respx.mock
async def test_coingecko_fetch_failure_returns_error() -> None:
    respx.get("https://api.coingecko.com/api/v3/coins/solana").mock(
        return_value=httpx.Response(429, json={"error": "rate limit"})
    )
    provider = CoinGeckoProvider()
    result = await provider.fetch("SOL")
    assert "error" in result


@pytest.mark.asyncio
@respx.mock
async def test_coingecko_calculates_fdv_ratio(coingecko_response: dict) -> None:
    respx.get("https://api.coingecko.com/api/v3/coins/solana").mock(
        return_value=httpx.Response(200, json=coingecko_response)
    )
    provider = CoinGeckoProvider()
    result = await provider.fetch("SOL")
    # fdv / mcap = 80B / 70B ≈ 1.14
    assert result["fdv_vs_mcap_ratio"] == pytest.approx(80 / 70, rel=0.01)


@pytest.mark.asyncio
@respx.mock
async def test_defillama_fetch_success(defillama_response: list) -> None:
    respx.get("https://api.llama.fi/v2/historicalChainTvl/solana").mock(
        return_value=httpx.Response(200, json=defillama_response)
    )
    provider = DeFiLlamaProvider()
    result = await provider.fetch("SOL")
    assert result["tvl_usd"] is not None
    assert result["tvl_change_30d_pct"] is not None


@pytest.mark.asyncio
@respx.mock
async def test_defillama_returns_none_for_unknown_symbol() -> None:
    provider = DeFiLlamaProvider()
    result = await provider.fetch("UNKNOWNCOIN")
    assert result["tvl_usd"] is None


@pytest.mark.asyncio
@respx.mock
async def test_defillama_fetch_failure_returns_graceful() -> None:
    respx.get("https://api.llama.fi/v2/historicalChainTvl/solana").mock(
        return_value=httpx.Response(500, json={})
    )
    provider = DeFiLlamaProvider()
    result = await provider.fetch("SOL")
    assert result["tvl_usd"] is None

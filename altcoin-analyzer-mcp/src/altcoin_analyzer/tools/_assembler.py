"""
Shared logic: fetch data from all providers and assemble AltcoinData.
"""

import asyncio
from typing import Any

from altcoin_analyzer.models.altcoin import AltcoinData, FundamentalData, MarketData, OnChainData
from altcoin_analyzer.providers import CoinGeckoProvider, DeFiLlamaProvider, GitHubMetricsProvider
from altcoin_analyzer.providers.base import ProviderError
from altcoin_analyzer.utils.logging import get_logger

logger = get_logger(__name__)

# Minimal known fundamentals DB (extend as needed)
_FUNDAMENTALS_DB: dict[str, dict[str, Any]] = {
    "SOL": {
        "is_audited": True, "audit_firms": ["Kudelski", "Neodyme"], "team_known": True,
        "has_whitepaper": True, "whitepaper_quality_score": 8.5,
        "regulatory_jurisdiction": "USA",
        "project_inception_year": 2020,
        "exchange_listings": ["binance", "coinbase", "kraken", "bybit", "okx"],
    },
    "AVAX": {
        "is_audited": True, "audit_firms": ["Halborn", "Trail of Bits"], "team_known": True,
        "has_whitepaper": True, "whitepaper_quality_score": 8.0,
        "regulatory_jurisdiction": "Switzerland",
        "project_inception_year": 2020,
        "exchange_listings": ["binance", "coinbase", "kraken", "bybit"],
    },
    "MATIC": {
        "is_audited": True, "audit_firms": ["Consensys Diligence"], "team_known": True,
        "has_whitepaper": True, "whitepaper_quality_score": 7.5,
        "regulatory_jurisdiction": "Singapore",
        "project_inception_year": 2019,
        "exchange_listings": ["binance", "coinbase", "kraken", "bybit", "okx"],
    },
    "ARB": {
        "is_audited": True, "audit_firms": ["Trail of Bits", "OpenZeppelin"], "team_known": True,
        "has_whitepaper": True, "whitepaper_quality_score": 8.0,
        "regulatory_jurisdiction": "Cayman Islands",
        "project_inception_year": 2021,
        "exchange_listings": ["binance", "coinbase", "bybit", "okx"],
    },
    "OP": {
        "is_audited": True, "audit_firms": ["OpenZeppelin"], "team_known": True,
        "has_whitepaper": True, "whitepaper_quality_score": 8.0,
        "regulatory_jurisdiction": "Cayman Islands",
        "project_inception_year": 2021,
        "exchange_listings": ["binance", "coinbase", "bybit"],
    },
}

_DEFAULT_FUNDAMENTALS: dict[str, Any] = {
    "is_audited": False, "audit_firms": [], "team_known": False,
    "has_whitepaper": True, "whitepaper_quality_score": 5.0,
    "regulatory_jurisdiction": None, "project_inception_year": None,
    "exchange_listings": [],
}


async def assemble_altcoin_data(symbol: str) -> AltcoinData:
    sym = symbol.upper()

    cg_provider = CoinGeckoProvider()
    dl_provider = DeFiLlamaProvider()
    gh_provider = GitHubMetricsProvider()

    try:
        cg_data, dl_data, gh_data = await asyncio.gather(
            cg_provider.fetch(sym),
            dl_provider.fetch(sym),
            gh_provider.fetch(sym),
            return_exceptions=True,
        )
    finally:
        await asyncio.gather(cg_provider.close(), dl_provider.close(), gh_provider.close())

    data_gaps: list[str] = []

    if isinstance(cg_data, (Exception, ProviderError)) or (isinstance(cg_data, dict) and "error" in cg_data):
        logger.error("coingecko_failed", symbol=sym, error=str(cg_data))
        raise ProviderError(f"CoinGecko unavailable for {sym}: {cg_data}")

    cg: dict[str, Any] = cg_data  # type: ignore[assignment]

    if isinstance(dl_data, (Exception,)):
        logger.warning("defillama_partial", symbol=sym, error=str(dl_data))
        dl_data = {}
        data_gaps.append("defillama_tvl")

    if isinstance(gh_data, (Exception,)):
        logger.warning("github_partial", symbol=sym, error=str(gh_data))
        gh_data = {}
        data_gaps.append("github_metrics")

    dl: dict[str, Any] = dl_data or {}  # type: ignore[assignment]
    gh: dict[str, Any] = gh_data or {}  # type: ignore[assignment]

    fund_db = _FUNDAMENTALS_DB.get(sym, _DEFAULT_FUNDAMENTALS)

    market = MarketData(
        price_usd=cg.get("price_usd", 0.0),
        market_cap_usd=cg.get("market_cap_usd", 0.0),
        fully_diluted_valuation_usd=cg.get("fully_diluted_valuation_usd", 0.0),
        volume_24h_usd=cg.get("volume_24h_usd", 0.0),
        price_change_24h_pct=cg.get("price_change_24h_pct", 0.0),
        price_change_7d_pct=cg.get("price_change_7d_pct", 0.0),
        price_change_30d_pct=cg.get("price_change_30d_pct", 0.0),
        all_time_high_usd=cg.get("all_time_high_usd", 0.0),
        ath_change_pct=cg.get("ath_change_pct", 0.0),
        circulating_supply=cg.get("circulating_supply", 0.0),
        total_supply=cg.get("total_supply"),
        max_supply=cg.get("max_supply"),
        liquidity_ratio=cg.get("liquidity_ratio", 0.0),
        fdv_vs_mcap_ratio=cg.get("fdv_vs_mcap_ratio", 1.0),
    )

    on_chain = OnChainData(
        tvl_usd=dl.get("tvl_usd"),
        tvl_change_7d_pct=dl.get("tvl_change_7d_pct"),
        tvl_change_30d_pct=dl.get("tvl_change_30d_pct"),
        active_addresses_7d=None,
        transaction_count_24h=None,
        github_commits_90d=gh.get("github_commits_90d") or cg.get("github_commits_90d"),
        github_stars=gh.get("github_stars") or cg.get("github_stars"),
        github_contributors=gh.get("github_contributors") or cg.get("github_contributors"),
        github_repo=gh.get("github_repo"),
    )

    fundamentals = FundamentalData(**fund_db)

    return AltcoinData(
        symbol=cg.get("symbol", sym),
        name=cg.get("name", sym),
        coingecko_id=cg.get("coingecko_id", sym.lower()),
        market_data=market,
        on_chain=on_chain,
        fundamentals=fundamentals,
        data_gaps=data_gaps,
    )

from typing import Any

from altcoin_analyzer.config import settings
from altcoin_analyzer.utils.cache import TTLCache
from altcoin_analyzer.utils.logging import get_logger

from .base import BaseProvider, ProviderError

logger = get_logger(__name__)

_cache: TTLCache = TTLCache(default_ttl=settings.cache_ttl_seconds)

# Mapping of common ticker symbols to CoinGecko IDs
SYMBOL_TO_ID: dict[str, str] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "AVAX": "avalanche-2",
    "MATIC": "matic-network",
    "POL": "matic-network",
    "DOT": "polkadot",
    "ADA": "cardano",
    "LINK": "chainlink",
    "UNI": "uniswap",
    "AAVE": "aave",
    "CRV": "curve-dao-token",
    "ARB": "arbitrum",
    "OP": "optimism",
    "INJ": "injective-protocol",
    "SUI": "sui",
    "APT": "aptos",
    "TIA": "celestia",
    "SEI": "sei-network",
    "JTO": "jito-governance-token",
}


class CoinGeckoProvider(BaseProvider):
    name = "coingecko"

    def __init__(self) -> None:
        super().__init__()
        self._base = settings.coingecko_base_url

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {"Accept": "application/json"}
        if settings.coingecko_api_key:
            h["x-cg-pro-api-key"] = settings.coingecko_api_key
        return h

    def _resolve_id(self, symbol: str) -> str:
        return SYMBOL_TO_ID.get(symbol.upper(), symbol.lower())

    async def fetch(self, symbol: str) -> dict[str, Any]:
        cache_key = f"coingecko:{symbol.upper()}:coin"
        cached = await _cache.get(cache_key)
        if cached is not None:
            logger.info("cache_hit", provider=self.name, symbol=symbol)
            return cached  # type: ignore[return-value]

        coin_id = self._resolve_id(symbol)
        url = f"{self._base}/coins/{coin_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "true",
            "sparkline": "false",
        }

        try:
            data = await self._get(url, params=params, headers=self._headers())
        except ProviderError as e:
            logger.error("coingecko_fetch_failed", symbol=symbol, error=str(e))
            return {"error": str(e), "symbol": symbol}

        result = self._parse(data, symbol)
        await _cache.set(cache_key, result)
        logger.info("cache_miss_fetched", provider=self.name, symbol=symbol)
        return result

    def _parse(self, data: dict[str, Any], symbol: str) -> dict[str, Any]:
        md = data.get("market_data", {})
        dev = data.get("developer_data", {})

        def safe(d: dict[str, Any], *keys: str, default: Any = None) -> Any:
            for k in keys:
                if not isinstance(d, dict):
                    return default
                d = d.get(k, {})  # type: ignore[assignment]
            return d if d is not None else default

        price = safe(md, "current_price", "usd", default=0.0)
        mcap = safe(md, "market_cap", "usd", default=0.0)
        fdv = safe(md, "fully_diluted_valuation", "usd", default=mcap)
        volume = safe(md, "total_volume", "usd", default=0.0)
        ath = safe(md, "ath", "usd", default=0.0)

        liquidity_ratio = volume / mcap if mcap > 0 else 0.0
        fdv_ratio = fdv / mcap if mcap > 0 else 1.0

        return {
            "symbol": data.get("symbol", symbol).upper(),
            "name": data.get("name", symbol),
            "coingecko_id": data.get("id", symbol.lower()),
            "price_usd": price,
            "market_cap_usd": mcap,
            "fully_diluted_valuation_usd": fdv,
            "volume_24h_usd": volume,
            "price_change_24h_pct": safe(md, "price_change_percentage_24h", default=0.0),
            "price_change_7d_pct": safe(md, "price_change_percentage_7d", default=0.0),
            "price_change_30d_pct": safe(md, "price_change_percentage_30d", default=0.0),
            "all_time_high_usd": ath,
            "ath_change_pct": safe(md, "ath_change_percentage", "usd", default=0.0),
            "circulating_supply": safe(md, "circulating_supply", default=0.0),
            "total_supply": safe(md, "total_supply"),
            "max_supply": safe(md, "max_supply"),
            "liquidity_ratio": liquidity_ratio,
            "fdv_vs_mcap_ratio": fdv_ratio,
            # developer data
            "github_commits_90d": dev.get("commit_count_4_weeks", 0) * 3,
            "github_stars": dev.get("stars", 0),
            "github_contributors": dev.get("pull_request_contributors", 0),
        }

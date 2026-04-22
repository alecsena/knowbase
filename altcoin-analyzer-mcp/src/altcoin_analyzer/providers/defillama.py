from typing import Any

from altcoin_analyzer.config import settings
from altcoin_analyzer.utils.cache import TTLCache
from altcoin_analyzer.utils.logging import get_logger

from .base import BaseProvider, ProviderError

logger = get_logger(__name__)

_cache: TTLCache = TTLCache(default_ttl=settings.cache_ttl_seconds)

SYMBOL_TO_SLUG: dict[str, str] = {
    "ETH": "ethereum",
    "SOL": "solana",
    "AVAX": "avalanche",
    "MATIC": "polygon",
    "POL": "polygon",
    "ARB": "arbitrum",
    "OP": "optimism",
    "DOT": "polkadot",
    "ADA": "cardano",
    "SUI": "sui",
    "APT": "aptos",
    "INJ": "injective",
    "TIA": "celestia",
}


class DeFiLlamaProvider(BaseProvider):
    name = "defillama"

    def __init__(self) -> None:
        super().__init__()
        self._base = settings.defillama_base_url

    async def fetch(self, symbol: str) -> dict[str, Any]:
        cache_key = f"defillama:{symbol.upper()}:tvl"
        cached = await _cache.get(cache_key)
        if cached is not None:
            logger.info("cache_hit", provider=self.name, symbol=symbol)
            return cached  # type: ignore[return-value]

        slug = SYMBOL_TO_SLUG.get(symbol.upper())
        if not slug:
            return {"tvl_usd": None, "tvl_change_7d_pct": None, "tvl_change_30d_pct": None}

        url = f"{self._base}/v2/historicalChainTvl/{slug}"
        try:
            data = await self._get(url)
        except ProviderError as e:
            logger.warning("defillama_fetch_failed", symbol=symbol, error=str(e))
            return {"tvl_usd": None, "tvl_change_7d_pct": None, "tvl_change_30d_pct": None}

        result = self._parse(data)
        await _cache.set(cache_key, result)
        return result

    def _parse(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        if not data or not isinstance(data, list):
            return {"tvl_usd": None, "tvl_change_7d_pct": None, "tvl_change_30d_pct": None}

        tvl_now = float(data[-1].get("tvl", 0)) if data else None
        tvl_7d_ago = float(data[-7].get("tvl", 0)) if len(data) >= 7 else None
        tvl_30d_ago = float(data[-30].get("tvl", 0)) if len(data) >= 30 else None

        def pct_change(old: float | None, new: float | None) -> float | None:
            if old is None or new is None or old == 0:
                return None
            return round((new - old) / old * 100, 2)

        return {
            "tvl_usd": tvl_now,
            "tvl_change_7d_pct": pct_change(tvl_7d_ago, tvl_now),
            "tvl_change_30d_pct": pct_change(tvl_30d_ago, tvl_now),
        }

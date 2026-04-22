from datetime import datetime, timedelta
from typing import Any

from altcoin_analyzer.config import settings
from altcoin_analyzer.utils.cache import TTLCache
from altcoin_analyzer.utils.logging import get_logger

from .base import BaseProvider, ProviderError

logger = get_logger(__name__)

_cache: TTLCache = TTLCache(default_ttl=settings.cache_ttl_seconds * 6)  # longer TTL for GH

SYMBOL_TO_REPO: dict[str, str] = {
    "SOL": "solana-labs/solana",
    "AVAX": "ava-labs/avalanchego",
    "MATIC": "maticnetwork/heimdall",
    "POL": "maticnetwork/heimdall",
    "DOT": "paritytech/polkadot-sdk",
    "ADA": "input-output-hk/cardano-node",
    "LINK": "smartcontractkit/chainlink",
    "UNI": "Uniswap/v3-core",
    "ARB": "OffchainLabs/arbitrum",
    "OP": "ethereum-optimism/optimism",
    "INJ": "InjectiveLabs/injective-core",
    "SUI": "MystenLabs/sui",
    "APT": "aptos-labs/aptos-core",
    "TIA": "celestiaorg/celestia-node",
    "SEI": "sei-protocol/sei-chain",
    "AAVE": "aave/aave-v3-core",
    "CRV": "curvefi/curve-contract",
}


class GitHubMetricsProvider(BaseProvider):
    name = "github"

    def __init__(self) -> None:
        super().__init__()
        self._api_base = "https://api.github.com"

    def _headers(self) -> dict[str, str]:
        h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if settings.github_token:
            h["Authorization"] = f"Bearer {settings.github_token}"
        return h

    async def fetch(self, symbol: str) -> dict[str, Any]:
        cache_key = f"github:{symbol.upper()}:metrics"
        cached = await _cache.get(cache_key)
        if cached is not None:
            logger.info("cache_hit", provider=self.name, symbol=symbol)
            return cached  # type: ignore[return-value]

        repo = SYMBOL_TO_REPO.get(symbol.upper())
        if not repo:
            return {"github_repo": None, "github_commits_90d": None, "github_stars": None, "github_contributors": None}

        try:
            repo_data, commits_count, contributors_count = await self._fetch_all(repo)
        except ProviderError as e:
            logger.warning("github_fetch_failed", symbol=symbol, repo=repo, error=str(e))
            return {"github_repo": repo, "github_commits_90d": None, "github_stars": None, "github_contributors": None}

        result = {
            "github_repo": repo,
            "github_commits_90d": commits_count,
            "github_stars": repo_data.get("stargazers_count", 0),
            "github_contributors": contributors_count,
        }
        await _cache.set(cache_key, result)
        return result

    async def _fetch_all(self, repo: str) -> tuple[dict[str, Any], int, int]:
        import asyncio

        repo_url = f"{self._api_base}/repos/{repo}"
        since = (datetime.utcnow() - timedelta(days=90)).isoformat() + "Z"
        commits_url = f"{self._api_base}/repos/{repo}/commits"
        contributors_url = f"{self._api_base}/repos/{repo}/contributors"

        repo_data, commits_data, contributors_data = await asyncio.gather(
            self._get(repo_url, headers=self._headers()),
            self._get(commits_url, params={"since": since, "per_page": 100}, headers=self._headers()),
            self._get(contributors_url, params={"per_page": 100, "anon": "false"}, headers=self._headers()),
            return_exceptions=True,
        )

        rd: dict[str, Any] = repo_data if isinstance(repo_data, dict) else {}
        commits_count = len(commits_data) if isinstance(commits_data, list) else 0
        contributors_count = len(contributors_data) if isinstance(contributors_data, list) else 0

        return rd, commits_count, contributors_count

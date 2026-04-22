from abc import ABC, abstractmethod
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from altcoin_analyzer.config import settings
from altcoin_analyzer.utils.logging import get_logger

logger = get_logger(__name__)


class ProviderError(Exception):
    """Raised when a data provider call fails."""


class InsufficientDataError(Exception):
    """Raised when required data is missing after all providers are exhausted."""


class BaseProvider(ABC):
    name: str = "base"

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=settings.http_timeout_seconds)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _get(self, url: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> Any:
        client = await self._get_client()
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.warning("provider_http_error", provider=self.name, url=url, status=e.response.status_code)
            raise ProviderError(f"{self.name}: HTTP {e.response.status_code} for {url}") from e
        except httpx.RequestError as e:
            logger.warning("provider_request_error", provider=self.name, url=url, error=str(e))
            raise ProviderError(f"{self.name}: request error for {url}: {e}") from e

    @abstractmethod
    async def fetch(self, symbol: str) -> dict[str, Any]:
        """Fetch raw data for the given symbol. Returns partial dict on error."""

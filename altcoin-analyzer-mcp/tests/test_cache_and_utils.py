import asyncio

import pytest

from altcoin_analyzer.utils.cache import TTLCache
from altcoin_analyzer.utils.logging import get_logger, setup_logging


@pytest.mark.asyncio
async def test_cache_set_and_get() -> None:
    cache = TTLCache(default_ttl=60)
    await cache.set("key1", {"value": 42})
    result = await cache.get("key1")
    assert result == {"value": 42}


@pytest.mark.asyncio
async def test_cache_miss_returns_none() -> None:
    cache = TTLCache(default_ttl=60)
    result = await cache.get("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_cache_ttl_expiry() -> None:
    cache = TTLCache(default_ttl=1)
    await cache.set("expiring", "soon", ttl=0)
    await asyncio.sleep(0.01)
    result = await cache.get("expiring")
    assert result is None


@pytest.mark.asyncio
async def test_cache_delete() -> None:
    cache = TTLCache(default_ttl=60)
    await cache.set("to_delete", "data")
    await cache.delete("to_delete")
    assert await cache.get("to_delete") is None


@pytest.mark.asyncio
async def test_cache_clear() -> None:
    cache = TTLCache(default_ttl=60)
    await cache.set("a", 1)
    await cache.set("b", 2)
    await cache.clear()
    assert cache.size() == 0


@pytest.mark.asyncio
async def test_cache_custom_ttl_per_entry() -> None:
    cache = TTLCache(default_ttl=60)
    await cache.set("short", "data", ttl=1)
    await cache.set("long", "data", ttl=3600)
    assert cache.size() == 2


def test_setup_logging_does_not_raise() -> None:
    setup_logging("DEBUG")


def test_get_logger_returns_logger() -> None:
    logger = get_logger("test")
    assert logger is not None

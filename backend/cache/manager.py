from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from collections import OrderedDict
from typing import Any

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# TTL constants (seconds)
TTL_ASSETS = 30 * 24 * 3600       # 30 days — driver photos, cars, logos
TTL_CALENDAR = 7 * 24 * 3600      # 7 days — season schedule
TTL_STANDINGS = 6 * 3600          # 6 hours — championship standings
TTL_RECENT_RESULT = 3600          # 1 hour — recent race result
TTL_FINAL_RESULT = 365 * 24 * 3600  # ~forever — past results
TTL_MEMORY = 300                  # 5 min — in-memory LRU


class MemoryCache:
    """Simple in-memory LRU cache with TTL."""

    def __init__(self, max_size: int = 256):
        self._data: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._max_size = max_size

    def get(self, key: str) -> Any | None:
        if key in self._data:
            value, expires = self._data[key]
            if time.time() < expires:
                self._data.move_to_end(key)
                return value
            del self._data[key]
        return None

    def set(self, key: str, value: Any, ttl: int = TTL_MEMORY) -> None:
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = (value, time.time() + ttl)
        while len(self._data) > self._max_size:
            self._data.popitem(last=False)


class CacheManager:
    """Multi-level cache: Memory → Redis → source."""

    def __init__(self, redis_url: str | None = None):
        self._memory = MemoryCache()
        self._redis: aioredis.Redis | None = None
        self._redis_url = redis_url
        self._redis_available = False

    async def connect(self) -> None:
        if self._redis_url:
            try:
                self._redis = aioredis.from_url(
                    self._redis_url, decode_responses=False
                )
                await self._redis.ping()
                self._redis_available = True
                logger.info("Redis connected: %s", self._redis_url)
            except Exception:
                logger.warning("Redis unavailable, using memory-only cache")
                self._redis_available = False

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()

    async def get(self, key: str) -> Any | None:
        # Level 1: Memory
        value = self._memory.get(key)
        if value is not None:
            return value

        # Level 2: Redis
        if self._redis_available and self._redis:
            try:
                raw = await self._redis.get(key)
                if raw is not None:
                    value = json.loads(raw)
                    self._memory.set(key, value)
                    return value
            except Exception:
                logger.debug("Redis get failed for key: %s", key)

        return None

    async def set(self, key: str, value: Any, ttl: int = TTL_STANDINGS) -> None:
        # Always set in memory
        self._memory.set(key, value, min(ttl, TTL_MEMORY))

        # Set in Redis if available
        if self._redis_available and self._redis:
            try:
                raw = json.dumps(value, default=str)
                await self._redis.setex(key, ttl, raw)
            except Exception:
                logger.debug("Redis set failed for key: %s", key)

    async def get_bytes(self, key: str) -> bytes | None:
        """Get binary data (images) from Redis."""
        if self._redis_available and self._redis:
            try:
                return await self._redis.get(key)
            except Exception:
                return None
        return None

    async def set_bytes(self, key: str, data: bytes, ttl: int = TTL_ASSETS) -> None:
        """Store binary data (images) in Redis."""
        if self._redis_available and self._redis:
            try:
                await self._redis.setex(key, ttl, data)
            except Exception:
                logger.debug("Redis set_bytes failed for key: %s", key)

    @staticmethod
    def make_key(*parts: str | int) -> str:
        raw = ":".join(str(p) for p in parts)
        return f"f1:{raw}"


# Global instance
cache = CacheManager()

"""
services/caching_strategy.py
============================

Flexible caching strategy — supports Redis (prod) + local fallback (dev).

Usage:
    from services.caching_strategy import CacheStrategy, get_cache

    # Automatic: uses Redis if available, falls back to local
    cache = get_cache()

    # Try to get from cache
    df = cache.get("dataset_key")

    # If not cached, load and store
    if df is None:
        df = pd.read_excel("data.xlsx")
        cache.set("dataset_key", df, ttl_seconds=300)
"""

from __future__ import annotations

import os
import pickle
import logging
from typing import Optional, Any
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ============================================================================
# ABSTRACT CACHE INTERFACE
# ============================================================================


class BaseCacheStrategy(ABC):
    """Abstract base class for cache implementations."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """Store value in cache with TTL."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Remove value from cache."""
        pass

    @abstractmethod
    def clear(self) -> bool:
        """Clear all cached values."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if cache is accessible."""
        pass


# ============================================================================
# REDIS IMPLEMENTATION
# ============================================================================


class RedisCache(BaseCacheStrategy):
    """Redis-backed cache (recommended for production)."""

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL (e.g., redis://user:pass@host:port).
                      If None, reads from REDIS_URL environment variable.
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL")
        self.client = None
        self._connect()

    def _connect(self) -> None:
        """Establish Redis connection."""
        if not self.redis_url:
            logger.warning("REDIS_URL not set, Redis cache disabled")
            return

        try:
            import redis

            self.client = redis.from_url(self.redis_url, decode_responses=False)
            self.client.ping()
            logger.info("✅ Redis cache connected")
        except ImportError:
            logger.warning("redis module not installed, install with: pip install redis")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.client = None

    def get(self, key: str) -> Optional[Any]:
        """Retrieve from Redis."""
        if not self.client:
            return None

        try:
            data = self.client.get(key)
            if data:
                return pickle.loads(data)
        except Exception as e:
            logger.warning(f"Redis get error for key '{key}': {e}")

        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """Store in Redis with TTL."""
        if not self.client:
            return False

        try:
            data = pickle.dumps(value)
            self.client.setex(key, ttl_seconds, data)
            logger.debug(f"✅ Cached '{key}' (TTL: {ttl_seconds}s)")
            return True
        except Exception as e:
            logger.error(f"Redis set error for key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete from Redis."""
        if not self.client:
            return False

        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    def clear(self) -> bool:
        """Clear all Redis keys (use with caution!)."""
        if not self.client:
            return False

        try:
            self.client.flushdb()
            logger.info("⚠️  Redis cache cleared")
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False

    def health_check(self) -> bool:
        """Check if Redis is accessible."""
        if not self.client:
            return False

        try:
            self.client.ping()
            return True
        except Exception:
            return False


# ============================================================================
# LOCAL CACHE IMPLEMENTATION
# ============================================================================


class LocalCache(BaseCacheStrategy):
    """In-memory local cache (fallback for development)."""

    def __init__(self):
        """Initialize local cache."""
        self.store: dict[str, tuple[Any, float]] = {}
        logger.info("💾 Local in-memory cache initialized")

    def get(self, key: str) -> Optional[Any]:
        """Retrieve from local cache (with TTL expiration check)."""
        if key not in self.store:
            return None

        value, expiry_time = self.store[key]

        # Check if expired
        if datetime.now() >= expiry_time:
            del self.store[key]
            logger.debug(f"Local cache entry '{key}' expired")
            return None

        logger.debug(f"✅ Local cache HIT '{key}'")
        return value

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """Store in local cache with TTL."""
        expiry_time = datetime.now() + timedelta(seconds=ttl_seconds)
        self.store[key] = (value, expiry_time)
        logger.debug(f"✅ Local cached '{key}' (TTL: {ttl_seconds}s)")
        return True

    def delete(self, key: str) -> bool:
        """Delete from local cache."""
        if key in self.store:
            del self.store[key]
            return True
        return False

    def clear(self) -> bool:
        """Clear all local cache."""
        self.store.clear()
        logger.info("⚠️  Local cache cleared")
        return True

    def health_check(self) -> bool:
        """Local cache is always available."""
        return True


# ============================================================================
# HYBRID CACHE STRATEGY
# ============================================================================


class HybridCache(BaseCacheStrategy):
    """
    Hybrid caching — tries Redis first, falls back to local.

    Ideal for graceful degradation:
    - Production: uses Redis for shared cache
    - Redis unavailable: falls back to local
    - Development: uses local only
    """

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize hybrid cache."""
        self.redis = RedisCache(redis_url=redis_url)
        self.local = LocalCache()

    def get(self, key: str) -> Optional[Any]:
        """Get from Redis, fallback to local."""
        # Try Redis first
        if self.redis.client:
            value = self.redis.get(key)
            if value is not None:
                logger.debug(f"✅ Cache HIT (Redis) '{key}'")
                return value

        # Fallback to local
        value = self.local.get(key)
        if value is not None:
            logger.debug(f"✅ Cache HIT (Local) '{key}'")
            return value

        logger.debug(f"❌ Cache MISS '{key}'")
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """Set in both Redis and local."""
        redis_ok = self.redis.set(key, value, ttl_seconds) if self.redis.client else True
        local_ok = self.local.set(key, value, ttl_seconds)
        return redis_ok and local_ok

    def delete(self, key: str) -> bool:
        """Delete from both."""
        redis_ok = self.redis.delete(key) if self.redis.client else True
        local_ok = self.local.delete(key)
        return redis_ok and local_ok

    def clear(self) -> bool:
        """Clear both."""
        redis_ok = self.redis.clear() if self.redis.client else True
        local_ok = self.local.clear()
        return redis_ok and local_ok

    def health_check(self) -> bool:
        """Both local and Redis should be healthy."""
        return self.local.health_check() and (
            self.redis.health_check() if self.redis.client else True
        )


# ============================================================================
# FACTORY & GLOBAL INSTANCE
# ============================================================================

_CACHE_INSTANCE: Optional[BaseCacheStrategy] = None


def get_cache(
    strategy: str = "hybrid",
    redis_url: Optional[str] = None,
) -> BaseCacheStrategy:
    """
    Get or create global cache instance.

    Args:
        strategy: "hybrid" (default), "redis", or "local"
        redis_url: Redis connection URL (if using redis/hybrid)

    Returns:
        Cache strategy instance
    """
    global _CACHE_INSTANCE

    if _CACHE_INSTANCE is not None:
        return _CACHE_INSTANCE

    if strategy == "redis":
        _CACHE_INSTANCE = RedisCache(redis_url=redis_url)
    elif strategy == "local":
        _CACHE_INSTANCE = LocalCache()
    elif strategy == "hybrid":
        _CACHE_INSTANCE = HybridCache(redis_url=redis_url)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    return _CACHE_INSTANCE


def reset_cache() -> None:
    """Reset global cache instance (useful for testing)."""
    global _CACHE_INSTANCE
    _CACHE_INSTANCE = None


if __name__ == "__main__":
    # Example usage
    import pandas as pd

    cache = get_cache()

    # Try to get cached data
    df = cache.get("example_data")

    if df is None:
        print("📥 Cache MISS — creating example data...")
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        cache.set("example_data", df, ttl_seconds=60)
        print(f"✅ Cached: {df.shape}")
    else:
        print(f"✅ Cache HIT: {df.shape}")
        print(df)

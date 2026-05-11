"""
services/caching_strategy/ — Flexible caching strategy (Redis + local fallback)

Refactorización PHASE 2 (268L → 3 modules):
  - base.py: Abstract base cache interface (26L)
  - implementations.py: Redis, Local, Hybrid implementations (207L)
  - __init__.py: Factory functions and re-exports (20L)

Responsibility unique per module:
  - base: Define the cache strategy contract
  - implementations: Provide Redis, Local, and Hybrid implementations
  - __init__: Factory pattern for cache creation

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

from typing import Optional

from .base import BaseCacheStrategy
from .implementations import HybridCache, LocalCache, RedisCache

# Alias for convenience
CacheStrategy = BaseCacheStrategy

# Global cache instance
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


__all__ = [
    "BaseCacheStrategy",
    "CacheStrategy",
    "RedisCache",
    "LocalCache",
    "HybridCache",
    "get_cache",
    "reset_cache",
]

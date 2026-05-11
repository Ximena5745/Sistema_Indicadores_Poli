"""
services/caching_strategy/base.py
=================================

Abstract base class for cache implementations.

Responsibility: Define the cache interface contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Any


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

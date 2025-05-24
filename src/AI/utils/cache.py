"""
AI Cache Module

This module provides caching functionality for AI components to improve performance.
"""

import logging
import functools
import time
from typing import Dict, Any, Callable, Tuple, Optional, Union
from datetime import datetime, timedelta
import json

# Configure logger
logger = logging.getLogger(__name__)

class AICache:
    """
    Caching system for AI module results.
    
    Attributes:
        cache (Dict): In-memory cache storage
        ttl (int): Time-to-live in seconds
        max_size (int): Maximum number of items in cache
    """
    
    def __init__(self, ttl: int = 3600, max_size: int = 1000):
        """
        Initialize the cache.
        
        Args:
            ttl: Cache time-to-live in seconds (default: 3600 - 1 hour)
            max_size: Maximum number of items in cache (default: 1000)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl
        self.max_size = max_size
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if key in self.cache:
            # Check if the cached value has expired
            cache_entry = self.cache[key]
            if time.time() < cache_entry['expires_at']:
                logger.debug(f"Cache hit for key: {key}")
                return cache_entry['value']
                
            # Remove expired entry
            logger.debug(f"Cache expired for key: {key}")
            del self.cache[key]
            
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Custom TTL in seconds (overrides default)
        """
        # Check if we need to evict entries due to size limit
        if len(self.cache) >= self.max_size:
            self._evict_entries()
            
        # Set the cache entry with expiration time
        self.cache[key] = {
            'value': value,
            'expires_at': time.time() + (ttl if ttl is not None else self.ttl),
            'created_at': time.time()
        }
        
        logger.debug(f"Cache set for key: {key}")
    
    def _evict_entries(self) -> None:
        """Evict entries to maintain cache size limit."""
        # First, remove all expired entries
        current_time = time.time()
        expired_keys = [k for k, v in self.cache.items() if v['expires_at'] < current_time]
        
        for key in expired_keys:
            del self.cache[key]
            
        # If we still need to evict entries, remove oldest ones
        if len(self.cache) >= self.max_size:
            # Sort by creation time and remove oldest entries
            sorted_keys = sorted(
                self.cache.keys(), 
                key=lambda k: self.cache[k]['created_at']
            )
            
            # Remove oldest 10% of entries
            num_to_remove = max(1, len(self.cache) // 10)
            for key in sorted_keys[:num_to_remove]:
                logger.debug(f"Evicting cache entry: {key}")
                del self.cache[key]
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        logger.debug("Cache cleared")
    
    def remove(self, key: str) -> bool:
        """
        Remove a specific key from the cache.
        
        Args:
            key: Cache key to remove
            
        Returns:
            True if key was in cache and removed, False otherwise
        """
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"Cache entry removed: {key}")
            return True
        return False
        
    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        current_time = time.time()
        expired_count = sum(1 for v in self.cache.values() if v['expires_at'] < current_time)
        valid_count = len(self.cache) - expired_count
        
        return {
            'size': len(self.cache),
            'valid_entries': valid_count,
            'expired_entries': expired_count,
            'max_size': self.max_size,
            'ttl': self.ttl
        }

# Create global cache instances for different components
regime_cache = AICache(ttl=3600)  # 1 hour TTL for regime detection
position_sizing_cache = AICache(ttl=300)  # 5 minutes TTL for position sizing
risk_metrics_cache = AICache(ttl=600)  # 10 minutes TTL for risk metrics

def cached(cache_instance: AICache, key_prefix: str = ''):
    """
    Decorator for caching function results.
    
    Args:
        cache_instance: AICache instance to use
        key_prefix: Prefix for cache keys
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name, args, and kwargs
            cache_key = f"{key_prefix}:{func.__name__}:"
            
            # Add args to key (exclude self/cls for methods)
            if args:
                if hasattr(args[0].__class__, func.__name__):  # Method call with self/cls
                    arg_str = str([str(a) for a in args[1:]])
                else:  # Regular function call
                    arg_str = str([str(a) for a in args])
                cache_key += arg_str
            
            # Add kwargs to key
            if kwargs:
                kwarg_str = str(sorted(kwargs.items()))
                cache_key += kwarg_str
            
            # Check cache for existing result
            cached_result = cache_instance.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Call the original function
            result = func(*args, **kwargs)
            
            # Cache the result
            cache_instance.set(cache_key, result)
            
            return result
        return wrapper
    return decorator

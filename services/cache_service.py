import json
import logging
import pickle
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from flask import current_app, g

logger = logging.getLogger(__name__)

class CacheService:
    """Redis-based caching service for the application
    
    This service provides methods for caching and retrieving data using Redis.
    It supports tenant isolation by prefixing cache keys with tenant IDs.
    
    Features:
        - Tenant isolation with key prefixing
        - Serialization/deserialization of complex objects
        - Automatic key generation
        - Memoization decorator for function results
        - Batch operations for improved performance
        - Circuit breaker pattern for Redis failures
    
    Attributes:
        default_timeout (int): Default cache timeout in seconds
        circuit_open (bool): Circuit breaker status
        failure_threshold (int): Number of failures before opening circuit
        recovery_timeout (int): Time in seconds before attempting recovery
        failure_count (int): Current count of consecutive failures
        last_failure_time (float): Timestamp of last failure
    """
    
    def __init__(self, default_timeout: int = 300, failure_threshold: int = 5, recovery_timeout: int = 60):
        """Initialize the cache service
        
        Args:
            default_timeout (int): Default cache timeout in seconds
            failure_threshold (int, optional): Number of failures before opening circuit. Defaults to 5.
            recovery_timeout (int, optional): Time in seconds before attempting recovery. Defaults to 60.
        """
        self.default_timeout = default_timeout
        
        # Circuit breaker pattern attributes
        self.circuit_open = False
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        
    def _handle_redis_failure(self, error: Exception) -> None:
        """Handle Redis connection failures using circuit breaker pattern
        
        Args:
            error (Exception): The exception that occurred
        """
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.circuit_open = True
            logger.warning(f"Circuit breaker opened after {self.failure_count} consecutive Redis failures")
        
        logger.error(f"Redis operation failed: {str(error)}")
        
    def _check_circuit_breaker(self) -> bool:
        """Check if circuit breaker is open and attempt recovery if needed
        
        Returns:
            bool: True if Redis operations should be attempted, False otherwise
        """
        # If circuit is open, check if recovery timeout has elapsed
        if self.circuit_open:
            elapsed = time.time() - self.last_failure_time
            if elapsed > self.recovery_timeout:
                # Try to recover
                logger.info(f"Attempting circuit recovery after {elapsed:.2f} seconds")
                self.circuit_open = False
                self.failure_count = 0
                return True
            return False
        
        return True
    
    @property
    def redis(self):
        """Get the Redis connection from the current Flask app
        
        Returns:
            Redis: The Redis connection or None if unavailable
        """
        if not self._check_circuit_breaker():
            logger.warning("Circuit breaker is open, skipping Redis operation")
            return None
            
        try:
            redis_client = current_app.extensions.get('redis')
            if redis_client is None:
                logger.warning("Redis client is not available in Flask app extensions")
            else:
                # Reset failure count on successful connection
                if self.failure_count > 0:
                    self.failure_count = 0
                    logger.info("Redis connection restored, reset failure count")
            return redis_client
        except Exception as e:
            self._handle_redis_failure(e)
            return None
    
    def _get_tenant_prefix(self) -> str:
        """Get the current tenant prefix for cache keys
        
        Returns:
            str: The tenant prefix
        """
        try:
            # Try to get tenant_id from g object if available
            tenant_id = getattr(g, 'tenant_id', None)
            if tenant_id:
                return f"tenant:{tenant_id}:"
            return ""
        except RuntimeError:
            # Not in request context
            return ""
    
    def _format_key(self, key: str) -> str:
        """Format a cache key with tenant prefix
        
        Args:
            key (str): The original cache key
            
        Returns:
            str: The formatted cache key with tenant prefix
        """
        # If key already contains tenant or organization ID, don't add prefix
        if ':' in key and any(x in key for x in ['tenant:', 'organization_id:', 'organization:']):
            return key
        
        prefix = self._get_tenant_prefix()
        return f"{prefix}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache
        
        Args:
            key (str): The cache key
            
        Returns:
            Any: The cached value, or None if not found
        """
        if not self.redis:
            logger.warning("Redis not available, skipping cache get")
            return None
        
        formatted_key = self._format_key(key)
        try:
            cached_data = self.redis.get(formatted_key)
            if cached_data is None:
                return None
            
            # Try to deserialize the data
            try:
                return pickle.loads(cached_data)
            except (pickle.PickleError, TypeError):
                # Fallback to JSON if pickle fails
                try:
                    return json.loads(cached_data)
                except json.JSONDecodeError:
                    # Return as-is if not serialized
                    return cached_data
        except Exception as e:
            logger.error(f"Error getting cache key {formatted_key}: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """Set a value in the cache
        
        Args:
            key (str): The cache key
            value (Any): The value to cache
            timeout (int, optional): Cache timeout in seconds. Defaults to None.
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.redis:
            logger.warning("Redis not available, skipping cache set")
            return False
        
        formatted_key = self._format_key(key)
        timeout = timeout or self.default_timeout
        
        try:
            # Try to serialize the data with pickle for complex objects
            try:
                serialized_data = pickle.dumps(value)
            except (pickle.PickleError, TypeError):
                # Fallback to JSON for simpler objects
                try:
                    serialized_data = json.dumps(value)
                except (TypeError, ValueError):
                    # Store as-is if serialization fails
                    serialized_data = value
            
            self.redis.setex(formatted_key, timeout, serialized_data)
            return True
        except Exception as e:
            logger.error(f"Error setting cache key {formatted_key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a value from the cache
        
        Args:
            key (str): The cache key
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.redis:
            logger.warning("Redis not available, skipping cache delete")
            return False
        
        formatted_key = self._format_key(key)
        try:
            self.redis.delete(formatted_key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache key {formatted_key}: {str(e)}")
            return False
    
    def clear_prefix(self, prefix: str) -> bool:
        """Clear all cache keys with a specific prefix
        
        Args:
            prefix (str): The prefix to clear
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.redis:
            logger.warning("Redis not available, skipping cache clear")
            return False
        
        formatted_prefix = self._format_key(prefix)
        try:
            # Get all keys with the prefix
            keys = self.redis.keys(f"{formatted_prefix}*")
            if keys:
                self.redis.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Error clearing cache prefix {formatted_prefix}: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache
        
        Args:
            key (str): The cache key
            
        Returns:
            bool: True if the key exists, False otherwise
        """
        if not self.redis:
            logger.warning("Redis not available, skipping cache exists check")
            return False
        
        formatted_key = self._format_key(key)
        try:
            return bool(self.redis.exists(formatted_key))
        except Exception as e:
            logger.error(f"Error checking cache key {formatted_key}: {str(e)}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a numeric value in the cache
        
        Args:
            key (str): The cache key
            amount (int): The amount to increment by
            
        Returns:
            int: The new value, or None if failed
        """
        if not self.redis:
            logger.warning("Redis not available, skipping cache increment")
            return None
        
        formatted_key = self._format_key(key)
        try:
            return self.redis.incrby(formatted_key, amount)
        except Exception as e:
            logger.error(f"Error incrementing cache key {formatted_key}: {str(e)}")
            return None
    
    def get_ttl(self, key: str) -> Optional[int]:
        """Get the remaining time-to-live for a key
        
        Args:
            key (str): The cache key
            
        Returns:
            int: The remaining TTL in seconds, or None if failed
        """
        if not self.redis:
            logger.warning("Redis not available, skipping cache TTL check")
            return None
        
        formatted_key = self._format_key(key)
        try:
            ttl = self.redis.ttl(formatted_key)
            return ttl if ttl > 0 else None
        except Exception as e:
            logger.error(f"Error getting TTL for cache key {formatted_key}: {str(e)}")
            return None
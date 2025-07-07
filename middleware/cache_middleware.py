import time
import logging
from functools import wraps
from flask import request, current_app, g
from services.cache_service import CacheService

logger = logging.getLogger(__name__)

class CacheMiddleware:
    """Middleware for intelligent caching strategies
    
    This middleware provides caching functionality for Flask routes and views.
    It supports tenant-aware caching, automatic cache key generation, and
    cache invalidation strategies.
    """
    
    def __init__(self, app=None):
        """Initialize the cache middleware
        
        Args:
            app (Flask, optional): The Flask application. Defaults to None.
        """
        self.app = app
        self.cache_service = CacheService()
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with a Flask application
        
        Args:
            app (Flask): The Flask application
        """
        self.app = app
        
        # Register before_request handler
        app.before_request(self._before_request)
        
        # Register after_request handler
        app.after_request(self._after_request)
        
        # Add cache service to app context
        app.cache_service = self.cache_service
        
        # Log initialization
        logger.info("Cache middleware initialized")
    
    def _before_request(self):
        """Handle before_request event
        
        This method is called before each request and checks if the response
        can be served from cache.
        """
        # Skip caching for non-GET requests
        if request.method != 'GET':
            return
        
        # Skip caching for specific paths
        if any(path in request.path for path in ['/admin', '/static', '/api/health']):
            return
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Try to get response from cache
        cached_response = self.cache_service.get(cache_key)
        if cached_response:
            # Store cache hit in g for metrics
            g.cache_hit = True
            g.cache_key = cache_key
            
            # Log cache hit
            logger.debug(f"Cache hit for {cache_key}")
            
            # Return cached response
            return cached_response
        
        # Store cache miss in g for after_request
        g.cache_miss = True
        g.cache_key = cache_key
    
    def _after_request(self, response):
        """Handle after_request event
        
        This method is called after each request and caches the response
        if appropriate.
        
        Args:
            response (Response): The Flask response
            
        Returns:
            Response: The Flask response
        """
        # Skip caching for non-GET requests
        if request.method != 'GET':
            return response
        
        # Skip caching for error responses
        if response.status_code != 200:
            return response
        
        # Skip caching for specific paths
        if any(path in request.path for path in ['/admin', '/static', '/api/health']):
            return response
        
        # Skip if not a cache miss
        if not getattr(g, 'cache_miss', False):
            return response
        
        # Get cache key from g
        cache_key = getattr(g, 'cache_key', None)
        if not cache_key:
            return response
        
        # Determine cache timeout based on path
        timeout = self._get_cache_timeout(request.path)
        
        # Cache the response
        self.cache_service.set(cache_key, response, timeout=timeout)
        
        # Log cache set
        logger.debug(f"Cached response for {cache_key} with timeout {timeout}s")
        
        return response
    
    def _generate_cache_key(self, request):
        """Generate a cache key for a request
        
        Args:
            request (Request): The Flask request
            
        Returns:
            str: The cache key
        """
        # Get tenant ID from g if available
        tenant_id = getattr(g, 'tenant_id', 'global')
        
        # Generate key based on path and query string
        path = request.path
        query_string = request.query_string.decode('utf-8')
        
        # Include user ID if authenticated
        user_id = 'anon'
        if hasattr(g, 'user') and g.user:
            user_id = str(g.user.id)
        
        # Generate key
        key = f"view:{tenant_id}:{user_id}:{path}"
        if query_string:
            key += f"?{query_string}"
        
        return key
    
    def _get_cache_timeout(self, path):
        """Get cache timeout based on path
        
        Args:
            path (str): The request path
            
        Returns:
            int: The cache timeout in seconds
        """
        # Default timeout
        default_timeout = current_app.config.get('CACHE_DEFAULT_TIMEOUT', 300)
        
        # Path-specific timeouts
        timeouts = {
            '/dashboard': 60,  # Dashboard updates frequently
            '/analytics': 300,  # Analytics can be cached longer
            '/results': 600,  # Results don't change often
            '/student': 600,  # Student profiles don't change often
            '/api/': 60,  # API responses cached for 1 minute
        }
        
        # Find matching path
        for prefix, timeout in timeouts.items():
            if path.startswith(prefix):
                return timeout
        
        return default_timeout


def cached_view(timeout=None):
    """Decorator for caching view functions
    
    Args:
        timeout (int, optional): Cache timeout in seconds. Defaults to None.
        
    Returns:
        callable: The decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip caching if Redis is not available
            if not hasattr(current_app, 'redis') or current_app.redis is None:
                return f(*args, **kwargs)
            
            # Generate cache key
            cache_key = f"view:{f.__name__}:{request.path}:{str(request.query_string)}"
            
            # Add tenant ID if available
            if hasattr(g, 'tenant_id'):
                cache_key = f"tenant:{g.tenant_id}:{cache_key}"
            
            # Try to get from cache
            cache_service = CacheService()
            cached_response = cache_service.get(cache_key)
            if cached_response is not None:
                return cached_response
            
            # Call the view function
            start_time = time.time()
            response = f(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Cache the response if execution time is significant
            if execution_time > 0.1:  # Only cache if execution takes more than 100ms
                cache_timeout = timeout or current_app.config.get('CACHE_DEFAULT_TIMEOUT', 300)
                cache_service.set(cache_key, response, timeout=cache_timeout)
            
            return response
        return decorated_function
    return decorator


def invalidate_cache(prefix):
    """Decorator for invalidating cache after a function call
    
    Args:
        prefix (str): The cache key prefix to invalidate
        
    Returns:
        callable: The decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Call the function
            result = f(*args, **kwargs)
            
            # Invalidate cache
            cache_service = CacheService()
            cache_service.clear_prefix(prefix)
            
            # Log cache invalidation
            logger.debug(f"Invalidated cache with prefix {prefix}")
            
            return result
        return decorated_function
    return decorator
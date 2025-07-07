import pytest
from unittest.mock import MagicMock, patch
from flask import Flask, request, g
from middleware.cache_middleware import CacheMiddleware, cached_view, invalidate_cache
from services.cache_service import CacheService

@pytest.fixture
def app():
    """Create a Flask app for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    
    # Mock Redis
    mock_redis = MagicMock()
    app.redis = mock_redis
    
    return app

@pytest.fixture
def cache_middleware(app):
    """Create a CacheMiddleware instance"""
    middleware = CacheMiddleware(app)
    return middleware

@pytest.fixture
def mock_cache_service():
    """Mock CacheService"""
    service = MagicMock(spec=CacheService)
    return service

class TestCacheMiddleware:
    """Test the CacheMiddleware class"""
    
    def test_init_app(self, app):
        """Test initialization with app"""
        middleware = CacheMiddleware()
        middleware.init_app(app)
        
        assert middleware.app == app
        assert hasattr(app, 'cache_service')
    
    def test_before_request_skip_non_get(self, app, cache_middleware):
        """Test _before_request skips non-GET requests"""
        with app.test_request_context('/', method='POST'):
            result = cache_middleware._before_request()
            assert result is None
            assert not hasattr(g, 'cache_hit')
            assert not hasattr(g, 'cache_miss')
    
    def test_before_request_skip_excluded_paths(self, app, cache_middleware):
        """Test _before_request skips excluded paths"""
        excluded_paths = [
            '/admin/dashboard',
            '/static/css/style.css',
            '/api/health'
        ]
        
        for path in excluded_paths:
            with app.test_request_context(path, method='GET'):
                result = cache_middleware._before_request()
                assert result is None
                assert not hasattr(g, 'cache_hit')
                assert not hasattr(g, 'cache_miss')
    
    def test_before_request_cache_hit(self, app, cache_middleware):
        """Test _before_request with cache hit"""
        # Mock cache hit
        cache_middleware.cache_service.get = MagicMock(return_value="cached response")
        
        with app.test_request_context('/dashboard', method='GET'):
            g.tenant_id = "test-tenant"
            result = cache_middleware._before_request()
            
            assert result == "cached response"
            assert g.cache_hit is True
            assert hasattr(g, 'cache_key')
    
    def test_before_request_cache_miss(self, app, cache_middleware):
        """Test _before_request with cache miss"""
        # Mock cache miss
        cache_middleware.cache_service.get = MagicMock(return_value=None)
        
        with app.test_request_context('/dashboard', method='GET'):
            g.tenant_id = "test-tenant"
            result = cache_middleware._before_request()
            
            assert result is None
            assert g.cache_miss is True
            assert hasattr(g, 'cache_key')
    
    def test_after_request_skip_non_get(self, app, cache_middleware):
        """Test _after_request skips non-GET requests"""
        response = MagicMock()
        response.status_code = 200
        
        with app.test_request_context('/', method='POST'):
            result = cache_middleware._after_request(response)
            assert result == response
            cache_middleware.cache_service.set.assert_not_called()
    
    def test_after_request_skip_error_responses(self, app, cache_middleware):
        """Test _after_request skips error responses"""
        response = MagicMock()
        response.status_code = 404
        
        with app.test_request_context('/', method='GET'):
            result = cache_middleware._after_request(response)
            assert result == response
            cache_middleware.cache_service.set.assert_not_called()
    
    def test_after_request_skip_excluded_paths(self, app, cache_middleware):
        """Test _after_request skips excluded paths"""
        response = MagicMock()
        response.status_code = 200
        
        excluded_paths = [
            '/admin/dashboard',
            '/static/css/style.css',
            '/api/health'
        ]
        
        for path in excluded_paths:
            with app.test_request_context(path, method='GET'):
                result = cache_middleware._after_request(response)
                assert result == response
                cache_middleware.cache_service.set.assert_not_called()
    
    def test_after_request_skip_if_not_cache_miss(self, app, cache_middleware):
        """Test _after_request skips if not a cache miss"""
        response = MagicMock()
        response.status_code = 200
        
        with app.test_request_context('/dashboard', method='GET'):
            # No cache_miss attribute set
            result = cache_middleware._after_request(response)
            assert result == response
            cache_middleware.cache_service.set.assert_not_called()
    
    def test_after_request_cache_response(self, app, cache_middleware):
        """Test _after_request caches response"""
        response = MagicMock()
        response.status_code = 200
        
        with app.test_request_context('/dashboard', method='GET'):
            g.cache_miss = True
            g.cache_key = "test:key"
            
            # Mock _get_cache_timeout
            cache_middleware._get_cache_timeout = MagicMock(return_value=60)
            
            result = cache_middleware._after_request(response)
            assert result == response
            
            # Verify cache was set
            cache_middleware.cache_service.set.assert_called_once_with(
                "test:key", response, timeout=60
            )
    
    def test_generate_cache_key(self, app, cache_middleware):
        """Test _generate_cache_key"""
        with app.test_request_context('/dashboard?param=value', method='GET'):
            # Test with tenant_id and user
            g.tenant_id = "test-tenant"
            g.user = MagicMock()
            g.user.id = 123
            
            key = cache_middleware._generate_cache_key(request)
            assert key == "view:test-tenant:123:/dashboard?param=value"
            
            # Test without user
            delattr(g, 'user')
            key = cache_middleware._generate_cache_key(request)
            assert key == "view:test-tenant:anon:/dashboard?param=value"
            
            # Test without tenant_id
            delattr(g, 'tenant_id')
            key = cache_middleware._generate_cache_key(request)
            assert key == "view:global:anon:/dashboard?param=value"
            
            # Test without query string
            with app.test_request_context('/dashboard', method='GET'):
                key = cache_middleware._generate_cache_key(request)
                assert key == "view:global:anon:/dashboard"
    
    def test_get_cache_timeout(self, app, cache_middleware):
        """Test _get_cache_timeout"""
        with app.app_context():
            # Test specific paths
            assert cache_middleware._get_cache_timeout('/dashboard') == 60
            assert cache_middleware._get_cache_timeout('/analytics/student/1') == 300
            assert cache_middleware._get_cache_timeout('/results/class/10A') == 600
            assert cache_middleware._get_cache_timeout('/student/1') == 600
            assert cache_middleware._get_cache_timeout('/api/v1/students') == 60
            
            # Test default timeout
            assert cache_middleware._get_cache_timeout('/unknown/path') == 300


class TestCachedViewDecorator:
    """Test the cached_view decorator"""
    
    def test_cached_view_skip_if_no_redis(self, app):
        """Test cached_view skips if Redis is not available"""
        app.redis = None
        
        @cached_view()
        def test_view():
            return "test response"
        
        with app.test_request_context('/'):
            result = test_view()
            assert result == "test response"
    
    def test_cached_view_cache_hit(self, app):
        """Test cached_view with cache hit"""
        # Mock CacheService.get to return a cached response
        with patch('services.cache_service.CacheService.get', return_value="cached response"):
            @cached_view()
            def test_view():
                return "original response"
            
            with app.test_request_context('/'):
                result = test_view()
                assert result == "cached response"
    
    def test_cached_view_cache_miss_fast_execution(self, app):
        """Test cached_view with cache miss and fast execution"""
        # Mock CacheService.get to return None (cache miss)
        with patch('services.cache_service.CacheService.get', return_value=None):
            # Mock time.time to simulate fast execution (< 100ms)
            with patch('time.time', side_effect=[0, 0.05]):
                @cached_view()
                def test_view():
                    return "original response"
                
                with app.test_request_context('/'):
                    with patch('services.cache_service.CacheService.set') as mock_set:
                        result = test_view()
                        assert result == "original response"
                        # Should not cache fast responses
                        mock_set.assert_not_called()
    
    def test_cached_view_cache_miss_slow_execution(self, app):
        """Test cached_view with cache miss and slow execution"""
        # Mock CacheService.get to return None (cache miss)
        with patch('services.cache_service.CacheService.get', return_value=None):
            # Mock time.time to simulate slow execution (> 100ms)
            with patch('time.time', side_effect=[0, 0.2]):
                @cached_view()
                def test_view():
                    return "original response"
                
                with app.test_request_context('/'):
                    with patch('services.cache_service.CacheService.set') as mock_set:
                        result = test_view()
                        assert result == "original response"
                        # Should cache slow responses
                        mock_set.assert_called_once()
    
    def test_cached_view_with_custom_timeout(self, app):
        """Test cached_view with custom timeout"""
        # Mock CacheService.get to return None (cache miss)
        with patch('services.cache_service.CacheService.get', return_value=None):
            # Mock time.time to simulate slow execution (> 100ms)
            with patch('time.time', side_effect=[0, 0.2]):
                @cached_view(timeout=600)
                def test_view():
                    return "original response"
                
                with app.test_request_context('/'):
                    with patch('services.cache_service.CacheService.set') as mock_set:
                        result = test_view()
                        assert result == "original response"
                        # Should cache with custom timeout
                        mock_set.assert_called_once()
                        # Check timeout was passed correctly
                        assert mock_set.call_args[1]['timeout'] == 600


class TestInvalidateCacheDecorator:
    """Test the invalidate_cache decorator"""
    
    def test_invalidate_cache(self, app):
        """Test invalidate_cache decorator"""
        with patch('services.cache_service.CacheService.clear_prefix') as mock_clear:
            @invalidate_cache("test:prefix")
            def test_function():
                return "test result"
            
            with app.app_context():
                result = test_function()
                assert result == "test result"
                mock_clear.assert_called_once_with("test:prefix")
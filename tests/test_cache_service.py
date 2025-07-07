import pytest
import pickle
import json
from unittest.mock import MagicMock, patch
from services.cache_service import CacheService
from flask import g

@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis_mock = MagicMock()
    return redis_mock

@pytest.fixture
def cache_service(mock_redis):
    """Create a CacheService instance with mocked Redis"""
    service = CacheService(default_timeout=300)
    service.redis = mock_redis
    return service

@pytest.fixture
def flask_app_context(app):
    """Create a Flask app context"""
    with app.app_context() as ctx:
        yield ctx

class TestCacheService:
    """Test the CacheService class"""
    
    def test_init(self):
        """Test initialization"""
        service = CacheService(default_timeout=600)
        assert service.default_timeout == 600
        
        service = CacheService()
        assert service.default_timeout == 300
    
    def test_redis_property(self, app):
        """Test the redis property"""
        with app.app_context():
            service = CacheService()
            assert service.redis is not None
    
    def test_tenant_prefix_with_tenant_id(self, app):
        """Test _get_tenant_prefix with tenant_id in g"""
        with app.app_context():
            g.tenant_id = "test-tenant"
            service = CacheService()
            prefix = service._get_tenant_prefix()
            assert prefix == "tenant:test-tenant:"
    
    def test_tenant_prefix_without_tenant_id(self, app):
        """Test _get_tenant_prefix without tenant_id in g"""
        with app.app_context():
            # Ensure g doesn't have tenant_id
            if hasattr(g, 'tenant_id'):
                delattr(g, 'tenant_id')
            
            service = CacheService()
            prefix = service._get_tenant_prefix()
            assert prefix == ""
    
    def test_format_key_with_tenant_prefix(self, app):
        """Test _format_key with tenant prefix"""
        with app.app_context():
            g.tenant_id = "test-tenant"
            service = CacheService()
            key = service._format_key("test-key")
            assert key == "tenant:test-tenant:test-key"
    
    def test_format_key_with_existing_prefix(self, app):
        """Test _format_key with existing prefix"""
        with app.app_context():
            g.tenant_id = "test-tenant"
            service = CacheService()
            key = service._format_key("tenant:other-tenant:test-key")
            assert key == "tenant:other-tenant:test-key"
            
            key = service._format_key("organization_id:123:test-key")
            assert key == "organization_id:123:test-key"
    
    def test_get_success(self, cache_service, mock_redis):
        """Test successful get operation"""
        # Test with pickle serialized data
        test_data = {"key": "value"}
        mock_redis.get.return_value = pickle.dumps(test_data)
        
        result = cache_service.get("test-key")
        assert result == test_data
        mock_redis.get.assert_called_once_with("test-key")
    
    def test_get_json_fallback(self, cache_service, mock_redis):
        """Test get with JSON fallback"""
        # Test with JSON serialized data
        test_data = {"key": "value"}
        mock_redis.get.return_value = json.dumps(test_data).encode()
        
        result = cache_service.get("test-key")
        assert result == test_data
        mock_redis.get.assert_called_once_with("test-key")
    
    def test_get_none(self, cache_service, mock_redis):
        """Test get with None result"""
        mock_redis.get.return_value = None
        
        result = cache_service.get("test-key")
        assert result is None
        mock_redis.get.assert_called_once_with("test-key")
    
    def test_get_error(self, cache_service, mock_redis):
        """Test get with error"""
        mock_redis.get.side_effect = Exception("Redis error")
        
        result = cache_service.get("test-key")
        assert result is None
        mock_redis.get.assert_called_once_with("test-key")
    
    def test_set_success(self, cache_service, mock_redis):
        """Test successful set operation"""
        test_data = {"key": "value"}
        
        result = cache_service.set("test-key", test_data)
        assert result is True
        mock_redis.setex.assert_called_once()
    
    def test_set_with_timeout(self, cache_service, mock_redis):
        """Test set with custom timeout"""
        test_data = {"key": "value"}
        
        result = cache_service.set("test-key", test_data, timeout=600)
        assert result is True
        mock_redis.setex.assert_called_once()
        # Check timeout was passed correctly
        assert mock_redis.setex.call_args[0][1] == 600
    
    def test_set_error(self, cache_service, mock_redis):
        """Test set with error"""
        mock_redis.setex.side_effect = Exception("Redis error")
        
        result = cache_service.set("test-key", "value")
        assert result is False
        mock_redis.setex.assert_called_once()
    
    def test_delete_success(self, cache_service, mock_redis):
        """Test successful delete operation"""
        result = cache_service.delete("test-key")
        assert result is True
        mock_redis.delete.assert_called_once_with("test-key")
    
    def test_delete_error(self, cache_service, mock_redis):
        """Test delete with error"""
        mock_redis.delete.side_effect = Exception("Redis error")
        
        result = cache_service.delete("test-key")
        assert result is False
        mock_redis.delete.assert_called_once_with("test-key")
    
    def test_clear_prefix_success(self, cache_service, mock_redis):
        """Test successful clear_prefix operation"""
        mock_redis.keys.return_value = ["prefix:key1", "prefix:key2"]
        
        result = cache_service.clear_prefix("prefix")
        assert result is True
        mock_redis.keys.assert_called_once_with("prefix*")
        mock_redis.delete.assert_called_once_with("prefix:key1", "prefix:key2")
    
    def test_clear_prefix_no_keys(self, cache_service, mock_redis):
        """Test clear_prefix with no matching keys"""
        mock_redis.keys.return_value = []
        
        result = cache_service.clear_prefix("prefix")
        assert result is True
        mock_redis.keys.assert_called_once_with("prefix*")
        mock_redis.delete.assert_not_called()
    
    def test_clear_prefix_error(self, cache_service, mock_redis):
        """Test clear_prefix with error"""
        mock_redis.keys.side_effect = Exception("Redis error")
        
        result = cache_service.clear_prefix("prefix")
        assert result is False
        mock_redis.keys.assert_called_once_with("prefix*")
    
    def test_exists_success(self, cache_service, mock_redis):
        """Test successful exists operation"""
        mock_redis.exists.return_value = 1
        
        result = cache_service.exists("test-key")
        assert result is True
        mock_redis.exists.assert_called_once_with("test-key")
    
    def test_exists_not_found(self, cache_service, mock_redis):
        """Test exists with key not found"""
        mock_redis.exists.return_value = 0
        
        result = cache_service.exists("test-key")
        assert result is False
        mock_redis.exists.assert_called_once_with("test-key")
    
    def test_exists_error(self, cache_service, mock_redis):
        """Test exists with error"""
        mock_redis.exists.side_effect = Exception("Redis error")
        
        result = cache_service.exists("test-key")
        assert result is False
        mock_redis.exists.assert_called_once_with("test-key")
    
    def test_increment_success(self, cache_service, mock_redis):
        """Test successful increment operation"""
        mock_redis.incrby.return_value = 2
        
        result = cache_service.increment("test-key")
        assert result == 2
        mock_redis.incrby.assert_called_once_with("test-key", 1)
    
    def test_increment_with_amount(self, cache_service, mock_redis):
        """Test increment with custom amount"""
        mock_redis.incrby.return_value = 5
        
        result = cache_service.increment("test-key", 5)
        assert result == 5
        mock_redis.incrby.assert_called_once_with("test-key", 5)
    
    def test_increment_error(self, cache_service, mock_redis):
        """Test increment with error"""
        mock_redis.incrby.side_effect = Exception("Redis error")
        
        result = cache_service.increment("test-key")
        assert result is None
        mock_redis.incrby.assert_called_once_with("test-key", 1)
    
    def test_get_ttl_success(self, cache_service, mock_redis):
        """Test successful get_ttl operation"""
        mock_redis.ttl.return_value = 300
        
        result = cache_service.get_ttl("test-key")
        assert result == 300
        mock_redis.ttl.assert_called_once_with("test-key")
    
    def test_get_ttl_expired(self, cache_service, mock_redis):
        """Test get_ttl with expired key"""
        mock_redis.ttl.return_value = -1
        
        result = cache_service.get_ttl("test-key")
        assert result is None
        mock_redis.ttl.assert_called_once_with("test-key")
    
    def test_get_ttl_error(self, cache_service, mock_redis):
        """Test get_ttl with error"""
        mock_redis.ttl.side_effect = Exception("Redis error")
        
        result = cache_service.get_ttl("test-key")
        assert result is None
        mock_redis.ttl.assert_called_once_with("test-key")
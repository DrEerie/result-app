# utils/error_handlers.py
import logging
import traceback
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify, current_app
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from utils.validations import ValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class AppError(Exception):
    """Custom application error with status code and error details"""
    
    def __init__(self, message: str, status_code: int = 500, error_code: str = None, details: Dict = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or 'app_error'
        self.details = details or {}
        super().__init__(self.message)

class BusinessLogicError(AppError):
    """Error for business logic violations"""
    
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, 400, 'business_logic_error', details)

class AuthorizationError(AppError):
    """Error for authorization failures"""
    
    def __init__(self, message: str = "You don't have permission to access this resource"):
        super().__init__(message, 403, 'authorization_error')

class ResourceNotFoundError(AppError):
    """Error for resource not found"""
    
    def __init__(self, resource: str = "Resource", resource_id: Any = None):
        message = f"{resource} not found"
        if resource_id:
            message += f" with ID: {resource_id}"
        super().__init__(message, 404, 'resource_not_found')

class DuplicateResourceError(AppError):
    """Error for duplicate resource creation"""
    
    def __init__(self, resource: str, field: str = None):
        message = f"{resource} already exists"
        if field:
            message += f" with this {field}"
        super().__init__(message, 409, 'duplicate_resource')

class ErrorHandler:
    """Centralized error handling and logging"""
    
    def __init__(self, app: Flask = None):
        self.logger = logging.getLogger('ErrorHandler')
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize error handlers for Flask app"""
        
        @app.errorhandler(ValidationError)
        def handle_validation_error(error):
            return self._create_error_response(
                message=error.message,
                status_code=400,
                error_code='validation_error',
                details={'field': error.field, 'code': error.code}
            )
        
        @app.errorhandler(AppError)
        def handle_app_error(error):
            return self._create_error_response(
                message=error.message,
                status_code=error.status_code,
                error_code=error.error_code,
                details=error.details
            )
        
        @app.errorhandler(SQLAlchemyError)
        def handle_database_error(error):
            self._log_error(error, 'Database Error')
            
            if isinstance(error, IntegrityError):
                return self._create_error_response(
                    message="A database constraint was violated. This might be due to duplicate data.",
                    status_code=409,
                    error_code='integrity_error'
                )
            
            return self._create_error_response(
                message="A database error occurred. Please try again.",
                status_code=500,
                error_code='database_error'
            )
        
        @app.errorhandler(HTTPException)
        def handle_http_error(error):
            return self._create_error_response(
                message=error.description,
                status_code=error.code,
                error_code=f'http_{error.code}'
            )
        
        @app.errorhandler(Exception)
        def handle_generic_error(error):
            self._log_error(error, 'Unhandled Exception')
            
            return self._create_error_response(
                message="An unexpected error occurred. Please try again.",
                status_code=500,
                error_code='internal_server_error',
                details={'error': str(error)} if current_app.debug else None
            )
        
        # Add request logging middleware
        @app.before_request
        def log_request_info():
            if current_app.debug:
                self.logger.debug(f"Request: {request.method} {request.url}")
                if request.json:
                    self.logger.debug(f"Request body: {request.json}")
    
    def _create_error_response(self, message: str, status_code: int, error_code: str, details: Dict = None):
        """Create standardized error response"""
        response_data = {
            'success': False,
            'error': {
                'code': error_code,
                'message': message,
                'timestamp': self._get_timestamp()
            }
        }
        
        if details:
            response_data['error']['details'] = details
        
        if current_app.debug:
            response_data['error']['request_id'] = request.headers.get('X-Request-ID', 'unknown')
        
        return jsonify(response_data), status_code
    
    def _log_error(self, error: Exception, error_type: str):
        """Log error with context information"""
        error_info = {
            'type': error_type,
            'message': str(error),
            'url': request.url if request else 'Unknown',
            'method': request.method if request else 'Unknown',
            'user_agent': request.headers.get('User-Agent') if request else 'Unknown',
            'ip_address': request.remote_addr if request else 'Unknown'
        }
        
        if current_app.debug:
            error_info['traceback'] = traceback.format_exc()
        
        self.logger.error(f"Error occurred: {error_info}")
    
    def _get_timestamp(self):
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'

# Success response helper
def create_success_response(data: Any = None, message: str = "Operation successful", status_code: int = 200):
    """Create standardized success response"""
    response_data = {
        'success': True,
        'message': message,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    if data is not None:
        response_data['data'] = data
    
    return jsonify(response_data), status_code

# Audit logging decorator
def audit_log(operation: str, resource_type: str = None):
    """Decorator to log operations for audit trail"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            from flask_login import current_user
            
            audit_data = {
                'operation': operation,
                'resource_type': resource_type,
                'user_id': getattr(current_user, 'id', None) if current_user.is_authenticated else None,
                'timestamp': datetime.utcnow().isoformat(),
                'ip_address': request.remote_addr if request else None,
                'user_agent': request.headers.get('User-Agent') if request else None
            }
            
            logger = logging.getLogger('AuditLogger')
            
            try:
                result = func(*args, **kwargs)
                audit_data['status'] = 'success'
                logger.info(f"Audit Log: {audit_data}")
                return result
            except Exception as e:
                audit_data['status'] = 'failed'
                audit_data['error'] = str(e)
                logger.warning(f"Audit Log: {audit_data}")
                raise
        
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

# Rate limiting helper
class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is within rate limit"""
        import time
        
        current_time = time.time()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Clean old requests outside the window
        self.requests[key] = [
            req_time for req_time in self.requests[key] 
            if current_time - req_time < window
        ]
        
        # Check if within limit
        if len(self.requests[key]) >= limit:
            return False
        
        # Add current request
        self.requests[key].append(current_time)
        return True

# Context manager for database transactions
class DatabaseTransaction:
    """Context manager for database transactions with error handling"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.logger = logging.getLogger('DatabaseTransaction')
    
    def __enter__(self):
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            try:
                self.db.commit()
                self.logger.debug("Database transaction committed successfully")
            except Exception as e:
                self.db.rollback()
                self.logger.error(f"Error committing transaction: {e}")
                raise
        else:
            self.db.rollback()
            self.logger.warning(f"Database transaction rolled back due to: {exc_val}")
        return False

# Import datetime for timestamp
from datetime import datetime

def register_error_handlers(app):
    """Register all error handlers with the Flask app."""
    handler = ErrorHandler()
    handler.init_app(app)

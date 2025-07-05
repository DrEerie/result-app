from functools import wraps
from flask import request, abort, current_app
import json
from werkzeug.exceptions import BadRequest

def validate_json():
    """Decorator to validate JSON request data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                current_app.logger.warning('Request content-type is not application/json')
                abort(400, description='Content-Type must be application/json')
            
            try:
                request.get_json()
            except BadRequest:
                current_app.logger.warning('Invalid JSON data in request')
                abort(400, description='Invalid JSON data')
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_schema(schema):
    """Decorator to validate request data against a schema"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = request.get_json()
                errors = schema.validate(data)
                if errors:
                    current_app.logger.warning(f'Schema validation failed: {errors}')
                    return {'errors': errors}, 400
            except Exception as e:
                current_app.logger.error(f'Schema validation error: {str(e)}')
                abort(400, description='Invalid request data')
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def sanitize_input(data):
    """Sanitize input data to prevent XSS and injection attacks"""
    if isinstance(data, str):
        # Basic XSS prevention
        return data.replace('<', '&lt;').replace('>', '&gt;')
    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(x) for x in data]
    return data

def validate_and_sanitize_input():
    """Decorator to sanitize request input"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.is_json:
                data = request.get_json()
                sanitized = sanitize_input(data)
                # Override request._cached_json to use sanitized data
                setattr(request, '_cached_json', (sanitized, request._cached_json[1]))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator 
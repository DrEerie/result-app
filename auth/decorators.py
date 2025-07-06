
# auth/decorators.py
from functools import wraps
from flask import g, abort, redirect, url_for, request
from flask_login import current_user, login_required as flask_login_required

def login_required(f):
    """Require user to be logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    """Require user to have specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            if current_user.role not in roles:
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        
        if not current_user.is_admin:
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def premium_only(f):
    """Require premium subscription"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'current_organization') or not g.current_organization:
            abort(401)
        
        subscription = g.current_organization.subscription
        if not subscription or subscription.tier == 'free':
            abort(402)  # Payment Required
        
        return f(*args, **kwargs)
    return decorated_function
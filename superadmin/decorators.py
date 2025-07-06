"""
SuperAdmin Decorators for EveClus
Handles SuperAdmin authentication and permission checks.
"""

from functools import wraps
from flask import session, request, jsonify, redirect, url_for, flash, current_app
from .models import SuperAdmin, GlobalAudit
from services.supabase_client import get_superadmin_client
import logging

logger = logging.getLogger(__name__)

def superadmin_required(f):
    """
    Decorator to ensure user is authenticated as SuperAdmin
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if superadmin is in session
        if 'superadmin_id' not in session:
            if request.is_json:
                return jsonify({'error': 'SuperAdmin authentication required'}), 401
            flash('Please log in as SuperAdmin to access this page.', 'error')
            return redirect(url_for('superadmin.login'))
        
        try:
            # Get superadmin client
            supabase = get_superadmin_client()
            
            # Verify superadmin exists and is active
            response = supabase.table('superadmins').select('*').eq('id', session['superadmin_id']).execute()
            
            if not response.data:
                session.pop('superadmin_id', None)
                if request.is_json:
                    return jsonify({'error': 'SuperAdmin not found'}), 401
                flash('SuperAdmin account not found. Please log in again.', 'error')
                return redirect(url_for('superadmin.login'))
            
            superadmin = response.data[0]
            
            if not superadmin.get('is_active', False):
                session.pop('superadmin_id', None)
                if request.is_json:
                    return jsonify({'error': 'SuperAdmin account is inactive'}), 401
                flash('SuperAdmin account is inactive.', 'error')
                return redirect(url_for('superadmin.login'))
            
            # Store superadmin info in request context
            request.superadmin = superadmin
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"SuperAdmin authentication error: {str(e)}")
            if request.is_json:
                return jsonify({'error': 'Authentication verification failed'}), 500
            flash('Authentication verification failed. Please try again.', 'error')
            return redirect(url_for('superadmin.login'))
    
    return decorated_function

def permission_required(permission):
    """
    Decorator to check if superadmin has specific permission
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # First check if superadmin is authenticated
            if 'superadmin_id' not in session:
                if request.is_json:
                    return jsonify({'error': 'SuperAdmin authentication required'}), 401
                flash('Please log in as SuperAdmin to access this page.', 'error')
                return redirect(url_for('superadmin.login'))
            
            try:
                # Get superadmin from request context or database
                superadmin = getattr(request, 'superadmin', None)
                if not superadmin:
                    supabase = get_superadmin_client()
                    response = supabase.table('superadmins').select('*').eq('id', session['superadmin_id']).execute()
                    if response.data:
                        superadmin = response.data[0]
                    else:
                        raise Exception("SuperAdmin not found")
                
                # Check if superadmin is master (has all permissions)
                if superadmin.get('is_master', False):
                    return f(*args, **kwargs)
                
                # Check specific permission
                permissions = superadmin.get('permissions', [])
                if permission not in permissions:
                    if request.is_json:
                        return jsonify({'error': f'Permission denied: {permission}'}), 403
                    flash(f'You do not have permission to access this resource: {permission}', 'error')
                    return redirect(url_for('superadmin.dashboard'))
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Permission check error: {str(e)}")
                if request.is_json:
                    return jsonify({'error': 'Permission verification failed'}), 500
                flash('Permission verification failed. Please try again.', 'error')
                return redirect(url_for('superadmin.dashboard'))
        
        return decorated_function
    return decorator

def master_admin_required(f):
    """
    Decorator to ensure user is a master SuperAdmin
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check if superadmin is authenticated
        if 'superadmin_id' not in session:
            if request.is_json:
                return jsonify({'error': 'SuperAdmin authentication required'}), 401
            flash('Please log in as SuperAdmin to access this page.', 'error')
            return redirect(url_for('superadmin.login'))
        
        try:
            # Get superadmin from request context or database
            superadmin = getattr(request, 'superadmin', None)
            if not superadmin:
                supabase = get_superadmin_client()
                response = supabase.table('superadmins').select('*').eq('id', session['superadmin_id']).execute()
                if response.data:
                    superadmin = response.data[0]
                else:
                    raise Exception("SuperAdmin not found")
            
            # Check if superadmin is master
            if not superadmin.get('is_master', False):
                if request.is_json:
                    return jsonify({'error': 'Master SuperAdmin access required'}), 403
                flash('Master SuperAdmin access required for this operation.', 'error')
                return redirect(url_for('superadmin.dashboard'))
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Master admin check error: {str(e)}")
            if request.is_json:
                return jsonify({'error': 'Master admin verification failed'}), 500
            flash('Master admin verification failed. Please try again.', 'error')
            return redirect(url_for('superadmin.dashboard'))
    
    return decorated_function

def log_superadmin_action(action, resource_type, description=None):
    """
    Decorator to log SuperAdmin actions
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Execute the function first
            result = f(*args, **kwargs)
            
            try:
                # Log the action
                if 'superadmin_id' in session:
                    supabase = get_superadmin_client()
                    
                    # Get resource ID from kwargs if available
                    resource_id = kwargs.get('id') or kwargs.get('tenant_id') or None
                    
                    audit_data = {
                        'superadmin_id': session['superadmin_id'],
                        'action': action,
                        'resource_type': resource_type,
                        'resource_id': str(resource_id) if resource_id else None,
                        'description': description or f"{action} {resource_type}",
                        'ip_address': request.remote_addr,
                        'user_agent': request.headers.get('User-Agent', ''),
                        'endpoint': request.endpoint,
                        'method': request.method,
                        'severity': 'info'
                    }
                    
                    # Add tenant_id if available
                    if hasattr(request, 'tenant_id'):
                        audit_data['tenant_id'] = request.tenant_id
                    
                    supabase.table('global_audit_logs').insert(audit_data).execute()
                    
            except Exception as e:
                logger.error(f"Failed to log SuperAdmin action: {str(e)}")
                # Don't fail the original request if logging fails
            
            return result
        
        return decorated_function
    return decorator

def rate_limit_superadmin(max_requests=100, window_minutes=60):
    """
    Rate limiting decorator for SuperAdmin endpoints
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'superadmin_id' not in session:
                return f(*args, **kwargs)
            
            try:
                # Simple rate limiting using session
                rate_limit_key = f"superadmin_rate_limit_{session['superadmin_id']}"
                
                # In production, you would use Redis for this
                # For now, we'll use a simple session-based approach
                current_time = datetime.utcnow()
                
                # This is a simplified implementation
                # In production, implement proper rate limiting with Redis
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Rate limiting error: {str(e)}")
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# Permission constants
class Permissions:
    """SuperAdmin permission constants"""
    TENANT_CREATE = 'tenant:create'
    TENANT_UPDATE = 'tenant:update'
    TENANT_DELETE = 'tenant:delete'
    TENANT_VIEW = 'tenant:view'
    TENANT_SUSPEND = 'tenant:suspend'
    
    SUPERADMIN_CREATE = 'superadmin:create'
    SUPERADMIN_UPDATE = 'superadmin:update'
    SUPERADMIN_DELETE = 'superadmin:delete'
    SUPERADMIN_VIEW = 'superadmin:view'
    
    SYSTEM_SETTINGS = 'system:settings'
    SYSTEM_ANALYTICS = 'system:analytics'
    SYSTEM_AUDIT = 'system:audit'
    SYSTEM_MAINTENANCE = 'system:maintenance'
    
    BILLING_VIEW = 'billing:view'
    BILLING_UPDATE = 'billing:update'
    
    SUPPORT_ACCESS = 'support:access'

# Helper functions
def get_current_superadmin():
    """Get current superadmin from session"""
    if 'superadmin_id' not in session:
        return None
    
    try:
        supabase = get_superadmin_client()
        response = supabase.table('superadmins').select('*').eq('id', session['superadmin_id']).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error getting current superadmin: {str(e)}")
        return None

def has_permission(permission):
    """Check if current superadmin has specific permission"""
    superadmin = get_current_superadmin()
    if not superadmin:
        return False
    
    if superadmin.get('is_master', False):
        return True
    
    permissions = superadmin.get('permissions', [])
    return permission in permissions

def is_master_admin():
    """Check if current superadmin is master"""
    superadmin = get_current_superadmin()
    return superadmin.get('is_master', False) if superadmin else False
# middleware/tenant.py
from flask import request, session, g, abort
from auth.models import User
import logging

logger = logging.getLogger(__name__)

class TenantMiddleware:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        app.before_request(self.load_tenant_context)
    
    def load_tenant_context(self):
        """Load tenant context for each request"""
        # Skip for auth routes
        if request.endpoint and request.endpoint.startswith('auth.'):
            return
        
        # Get organization from session
        organization_id = session.get('organization_id')
        user_id = session.get('user_id')
        
        if organization_id and user_id:
            user = User.query.filter_by(id=user_id).first()
            if user and str(user.organization_id) == organization_id:
                g.current_user = user
                g.current_organization = user.organization
                g.organization_id = user.organization_id
                
                # Set RLS context for Supabase
                self.set_rls_context(user.organization_id)
            else:
                session.clear()
                abort(401)
        elif request.endpoint and not request.endpoint.startswith(('main_bp.', 'template/public')):
            # Require authentication for non-public routes
            abort(401)
    
    def set_rls_context(self, organization_id):
        """Set Row Level Security context"""
        try:
            from services.supabase_client import supabase_client
            # This would be handled by Supabase RLS policies automatically
            # based on the authenticated user's JWT token
            pass
        except Exception as e:
            logger.error(f"Failed to set RLS context: {str(e)}")

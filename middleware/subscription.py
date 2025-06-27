# middleware/subscription.py
from flask import g, abort, jsonify, request
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class SubscriptionMiddleware:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        app.before_request(self.check_subscription_limits)
    
    def check_subscription_limits(self):
        """Check subscription limits before processing request"""
        if not hasattr(g, 'current_organization') or not g.current_organization:
            return
        
        subscription = g.current_organization.subscription
        if not subscription or not subscription.is_active:
            if request.endpoint and not request.endpoint.startswith(('auth.', 'main.', 'subscription.')):
                abort(402)  # Payment Required

def feature_required(feature_name):
    """Decorator to check if user has access to a feature"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_organization') or not g.current_organization:
                abort(401)
            
            subscription = g.current_organization.subscription
            if not subscription or not subscription.has_feature(feature_name):
                return jsonify({
                    'error': f'Feature "{feature_name}" requires {subscription.tier if subscription else "premium"} subscription',
                    'upgrade_required': True
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def usage_tracked(feature_name):
    """Decorator to track feature usage"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if hasattr(g, 'current_organization') and g.current_organization:
                try:
                    from models.base import UsageTracking, db
                    from datetime import datetime
                    
                    # Update or create usage tracking
                    usage = UsageTracking.query.filter_by(
                        organization_id=g.current_organization.id,
                        feature=feature_name,
                        date=datetime.utcnow().date()
                    ).first()
                    
                    if usage:
                        usage.usage_count += 1
                    else:
                        usage = UsageTracking(
                            organization_id=g.current_organization.id,
                            feature=feature_name,
                            usage_count=1
                        )
                        db.session.add(usage)
                    
                    db.session.commit()
                    
                except Exception as e:
                    logger.error(f"Usage tracking failed: {str(e)}")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# auth/models.py
from sqlalchemy.dialects.postgresql import UUID
from flask_login import UserMixin
from datetime import datetime
import uuid

# Import shared db instance
try:
    from models.base import db
except ImportError:
    # Fallback for testing or standalone usage
    from flask_sqlalchemy import SQLAlchemy
    db = SQLAlchemy()

class User(UserMixin, db.Model):  # Add UserMixin here
    __tablename__ = 'users'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True)  # Links to Supabase auth.users
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('super_admin', 'admin', 'teacher', 'student', name='user_role'), default='teacher')
    is_active = db.Column(db.Boolean, default=True)
    phone = db.Column(db.String(20))
    avatar_url = db.Column(db.Text)
    employee_id = db.Column(db.String(50))
    department = db.Column(db.String(100))
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    preferences = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)
    api_token = db.Column(db.String(255), unique=True, nullable=True)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    # Flask-Login required methods
    def get_id(self):
        """Return the user ID as a string"""
        return str(self.id)
    
    def is_authenticated(self):
        """Return True if user is authenticated"""
        return True
    
    def is_anonymous(self):
        """Return True if user is anonymous"""
        return False
    
    def is_active_user(self):
        """Return True if user account is active"""
        return self.is_active
    
    @property
    def is_admin(self):
        return self.role in ['admin', 'super_admin']
    
    @property
    def is_teacher(self):
        return self.role in ['teacher', 'admin', 'super_admin']
    
    def can_access_feature(self, feature_name):
        """Check if user can access a feature based on subscription"""
        if not self.organization.subscription:
            return False
        return self.organization.subscription.has_feature(feature_name)

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    tier = db.Column(db.Enum('free', 'premium', 'enterprise', name='subscription_tier'), default='free')
    status = db.Column(db.String(20), default='active')
    features = db.Column(db.JSON, default=dict)
    limits = db.Column(db.JSON, default=dict)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    trial_ends_at = db.Column(db.DateTime)
    billing_cycle = db.Column(db.String(20), default='monthly')
    amount = db.Column(db.Numeric(10, 2), default=0)
    currency = db.Column(db.String(3), default='USD')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Subscription {self.tier} for {self.organization.name}>'
    
    @property
    def is_active(self):
        return self.status == 'active' and (not self.expires_at or self.expires_at > datetime.utcnow())
    
    @property
    def is_trial(self):
        return self.trial_ends_at and self.trial_ends_at > datetime.utcnow()
    
    def has_feature(self, feature_name):
        """Check if subscription has access to a feature"""
        tier_features = {
            'free': ['basic_reports', 'student_management'],
            'premium': ['basic_reports', 'student_management', 'attendance_tracking', 'advanced_analytics', 'bulk_import', 'custom_branding'],
            'enterprise': ['basic_reports', 'student_management', 'attendance_tracking', 'advanced_analytics', 'bulk_import', 'custom_branding', 'api_access', 'multiple_organizations']
        }
        return feature_name in tier_features.get(self.tier, [])
    
    def get_limits(self):
        """Get subscription limits"""
        tier_limits = {
            'free': {'students': 50, 'subjects': 5, 'storage_mb': 100},
            'premium': {'students': -1, 'subjects': -1, 'storage_mb': 1000},
            'enterprise': {'students': -1, 'subjects': -1, 'storage_mb': 10000}
        }
        return tier_limits.get(self.tier, tier_limits['free'])
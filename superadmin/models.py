"""
SuperAdmin Models for EveClus
Handles system-wide administration data models.
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

Base = declarative_base()

class TenantStatus(Enum):
    """Tenant status enumeration"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    DELETED = "deleted"

class SubscriptionTier(Enum):
    """Subscription tier enumeration"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class SuperAdmin(Base):
    """SuperAdmin model for system administration"""
    __tablename__ = 'superadmins'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    full_name = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    is_master = Column(Boolean, default=False)  # Master admin with full privileges
    permissions = Column(JSON, default=lambda: [])  # List of permissions
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    audit_logs = relationship("GlobalAudit", back_populates="superadmin")
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission):
        """Check if superadmin has specific permission"""
        return permission in self.permissions or self.is_master
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_master': self.is_master,
            'permissions': self.permissions,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Tenant(Base):
    """Tenant model for multi-tenancy management"""
    __tablename__ = 'tenants'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), unique=True, nullable=False)  # UUID-based tenant identifier
    organization_name = Column(String(200), nullable=False)
    subdomain = Column(String(100), unique=True, nullable=False)
    database_name = Column(String(100), nullable=False)
    schema_name = Column(String(100), nullable=False)
    
    # Contact Information
    admin_email = Column(String(120), nullable=False)
    admin_name = Column(String(200), nullable=False)
    phone = Column(String(20))
    
    # Subscription Details
    subscription_tier = Column(String(20), default=SubscriptionTier.FREE.value)
    subscription_start = Column(DateTime, default=datetime.utcnow)
    subscription_end = Column(DateTime)
    
    # Status and Limits
    status = Column(String(20), default=TenantStatus.PENDING.value)
    max_students = Column(Integer, default=100)
    max_subjects = Column(Integer, default=20)
    max_storage_mb = Column(Integer, default=500)
    
    # Usage Statistics
    current_students = Column(Integer, default=0)
    current_subjects = Column(Integer, default=0)
    current_storage_mb = Column(Float, default=0.0)
    total_results = Column(Integer, default=0)
    
    # Configuration
    custom_domain = Column(String(255))
    settings = Column(JSON, default=lambda: {})
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime)
    
    # Relationships
    audit_logs = relationship("GlobalAudit", back_populates="tenant")
    system_settings = relationship("SystemSettings", back_populates="tenant")
    
    @property
    def is_active(self):
        """Check if tenant is active"""
        return self.status == TenantStatus.ACTIVE.value
    
    @property
    def is_subscription_expired(self):
        """Check if subscription is expired"""
        if not self.subscription_end:
            return False
        return datetime.utcnow() > self.subscription_end
    
    @property
    def usage_percentage(self):
        """Calculate usage percentage"""
        return {
            'students': (self.current_students / self.max_students * 100) if self.max_students > 0 else 0,
            'subjects': (self.current_subjects / self.max_subjects * 100) if self.max_subjects > 0 else 0,
            'storage': (self.current_storage_mb / self.max_storage_mb * 100) if self.max_storage_mb > 0 else 0
        }
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'organization_name': self.organization_name,
            'subdomain': self.subdomain,
            'admin_email': self.admin_email,
            'admin_name': self.admin_name,
            'phone': self.phone,
            'subscription_tier': self.subscription_tier,
            'subscription_start': self.subscription_start.isoformat() if self.subscription_start else None,
            'subscription_end': self.subscription_end.isoformat() if self.subscription_end else None,
            'status': self.status,
            'max_students': self.max_students,
            'max_subjects': self.max_subjects,
            'max_storage_mb': self.max_storage_mb,
            'current_students': self.current_students,
            'current_subjects': self.current_subjects,
            'current_storage_mb': self.current_storage_mb,
            'total_results': self.total_results,
            'custom_domain': self.custom_domain,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'usage_percentage': self.usage_percentage,
            'is_active': self.is_active,
            'is_subscription_expired': self.is_subscription_expired
        }

class SystemSettings(Base):
    """System-wide settings model"""
    __tablename__ = 'system_settings'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=True)  # Null for global settings
    key = Column(String(100), nullable=False)
    value = Column(Text)
    data_type = Column(String(20), default='string')  # string, int, float, bool, json
    description = Column(Text)
    is_global = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="system_settings")
    
    def get_typed_value(self):
        """Get value with proper type casting"""
        if self.data_type == 'int':
            return int(self.value) if self.value else 0
        elif self.data_type == 'float':
            return float(self.value) if self.value else 0.0
        elif self.data_type == 'bool':
            return self.value.lower() in ('true', '1', 'yes') if self.value else False
        elif self.data_type == 'json':
            import json
            return json.loads(self.value) if self.value else {}
        return self.value
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'key': self.key,
            'value': self.get_typed_value(),
            'data_type': self.data_type,
            'description': self.description,
            'is_global': self.is_global,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class GlobalAudit(Base):
    """Global audit logging model"""
    __tablename__ = 'global_audit_logs'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=True)
    superadmin_id = Column(Integer, ForeignKey('superadmins.id'), nullable=True)
    
    # Action Details
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(50))
    description = Column(Text)
    
    # Request Details
    ip_address = Column(String(45))
    user_agent = Column(Text)
    endpoint = Column(String(255))
    method = Column(String(10))
    
    # Data Changes
    old_values = Column(JSON)
    new_values = Column(JSON)
    
    # Metadata
    severity = Column(String(20), default='info')  # info, warning, error, critical
    tags = Column(JSON, default=lambda: [])
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="audit_logs")
    superadmin = relationship("SuperAdmin", back_populates="audit_logs")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'superadmin_id': self.superadmin_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'description': self.description,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'endpoint': self.endpoint,
            'method': self.method,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'severity': self.severity,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class TenantMetrics(Base):
    """Tenant metrics for analytics"""
    __tablename__ = 'tenant_metrics'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    
    # Usage Metrics
    active_users = Column(Integer, default=0)
    students_added = Column(Integer, default=0)
    results_processed = Column(Integer, default=0)
    pdfs_generated = Column(Integer, default=0)
    
    # Performance Metrics
    avg_response_time = Column(Float, default=0.0)
    error_count = Column(Integer, default=0)
    
    # Storage Metrics
    storage_used_mb = Column(Float, default=0.0)
    
    # Revenue Metrics (if applicable)
    revenue_generated = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'date': self.date.isoformat() if self.date else None,
            'active_users': self.active_users,
            'students_added': self.students_added,
            'results_processed': self.results_processed,
            'pdfs_generated': self.pdfs_generated,
            'avg_response_time': self.avg_response_time,
            'error_count': self.error_count,
            'storage_used_mb': self.storage_used_mb,
            'revenue_generated': self.revenue_generated,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
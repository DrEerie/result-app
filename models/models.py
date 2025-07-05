# models/models.py
# This file imports all models for centralized access

from .base import db
from .organization import Organization
from .student import Student
from .subject import Subject
from .result import Result
from .audit_logger import AuditLog
from .usage_tracker import UsageTracking
from .class_settings import ClassSettings

# Import User model from auth module
try:
    from auth.models import User
except ImportError:
    # Fallback if auth module is not available
    User = None

# Export all models
__all__ = [
    'db',
    'Organization', 
    'Student',
    'Subject', 
    'Result',
    'AuditLog',
    'UsageTracking',
    'ClassSettings',
    'User'
]

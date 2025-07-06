# Import the database instance and models
from .base import db
from .organization import Organization
from .student import Student
from .subject import Subject
from .result import Result
from .audit_logger import AuditLog
from .usage_tracker import UsageTracking
from .class_settings import ClassSettings

# Import User model from auth module if available
try:
    from auth.models import User
except ImportError:
    User = None

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

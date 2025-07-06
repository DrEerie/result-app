"""
SuperAdmin Module for EveClus
Handles system-wide administration, tenant management, and global monitoring.
"""

from flask import Blueprint

# Create SuperAdmin Blueprint
superadmin_bp = Blueprint('superadmin', __name__, url_prefix='/superadmin')

# Import views to register routes
from . import views

__all__ = ['superadmin_bp']
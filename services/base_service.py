# services/base_service.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from flask import current_app
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import logging

class BaseService(ABC):
    """
    Abstract base service class that provides common functionality
    for all service classes including error handling, logging, and database operations.
    """
    
    def __init__(self, db_session: Session = None):
        self.db = db_session
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def _log_operation(self, operation: str, details: Dict[str, Any] = None):
        """Log service operations for audit and debugging"""
        log_data = {
            'service': self.__class__.__name__,
            'operation': operation,
            'timestamp': datetime.utcnow().isoformat(),
            'details': details or {}
        }
        self.logger.info(f"Service Operation: {log_data}")
        
    def _handle_db_error(self, error: Exception, operation: str) -> Dict[str, Any]:
        """Standardized database error handling"""
        self.logger.error(f"Database error in {operation}: {str(error)}")
        
        if isinstance(error, SQLAlchemyError):
            return {
                'success': False,
                'error': 'database_error',
                'message': 'A database error occurred. Please try again.',
                'details': str(error) if current_app.debug else None
            }
        
        return {
            'success': False,
            'error': 'unknown_error',
            'message': 'An unexpected error occurred.',
            'details': str(error) if current_app.debug else None
        }
    
    def _validate_tenant_access(self, organization_id: int, user_org_id: int) -> bool:
        """Ensure user can only access their organization's data"""
        return organization_id == user_org_id
    
    def _paginate_query(self, query, page: int = 1, per_page: int = 20):
        """Standard pagination for queries"""
        try:
            paginated = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            return {
                'success': True,
                'data': paginated.items,
                'pagination': {
                    'page': paginated.page,
                    'pages': paginated.pages,
                    'per_page': paginated.per_page,
                    'total': paginated.total,
                    'has_next': paginated.has_next,
                    'has_prev': paginated.has_prev
                }
            }
        except Exception as e:
            return self._handle_db_error(e, 'pagination')
    
    @abstractmethod
    def create(self, data: Dict[str, Any], user_id: int, organization_id: int) -> Dict[str, Any]:
        """Create a new record"""
        pass
    
    @abstractmethod
    def get_by_id(self, record_id: int, user_id: int, organization_id: int) -> Dict[str, Any]:
        """Get record by ID with tenant validation"""
        pass
    
    @abstractmethod
    def update(self, record_id: int, data: Dict[str, Any], user_id: int, organization_id: int) -> Dict[str, Any]:
        """Update existing record"""
        pass
    
    @abstractmethod
    def delete(self, record_id: int, user_id: int, organization_id: int) -> Dict[str, Any]:
        """Delete record"""
        pass
    
    @abstractmethod
    def list_all(self, user_id: int, organization_id: int, **filters) -> Dict[str, Any]:
        """List all records with filtering"""
        pass
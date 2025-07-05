# models/audit_logger.py
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from .base import db
class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'))
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    table_name = db.Column(db.String(100), nullable=False)
    record_id = db.Column(UUID(as_uuid=True), nullable=False)
    action = db.Column(db.String(20), nullable=False)  # INSERT, UPDATE, DELETE
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User')
    organization = db.relationship('Organization')
    
    def __repr__(self):
        return f'<AuditLog {self.table_name} - {self.action}>'
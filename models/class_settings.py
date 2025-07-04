# models/class_settings.py
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from .base import db, BaseModel

class ClassSettings(BaseModel):
    __tablename__ = 'class_settings'
    
    class_name = db.Column(db.String(20), nullable=False)
    section = db.Column(db.String(5))
    academic_year = db.Column(db.String(10), nullable=False)
    max_working_days = db.Column(db.Integer, default=200)
    grading_system = db.Column(db.JSON, default=dict)
    class_teacher_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    settings = db.Column(db.JSON, default=dict)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    
    # Relationships
    class_teacher = db.relationship('User', foreign_keys=[class_teacher_id])
    creator = db.relationship('User', foreign_keys=[created_by])
    
    __table_args__ = (db.UniqueConstraint('organization_id', 'class_name', 'section', 'academic_year'),)
    
    def __repr__(self):
        return f'<ClassSettings {self.class_name}-{self.section} ({self.academic_year})>'

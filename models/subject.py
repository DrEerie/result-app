# models/subject.py
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from .base import db, BaseModel
class Subject(BaseModel):
    __tablename__ = 'subjects'
    
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20))
    max_marks = db.Column(db.Numeric(5, 2), default=100.0)
    class_name = db.Column(db.String(20))
    is_template = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    
    # Relationships
    results = db.relationship('Result', backref='subject', lazy=True)
    
    def __repr__(self):
        return f'<Subject {self.name}>'

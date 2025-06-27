# models/class_settings.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

db = SQLAlchemy()

from models.base import BaseModel

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

# New Attendance Model
class Attendance(BaseModel):
    __tablename__ = 'attendance'
    
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id'), nullable=False)
    class_name = db.Column(db.String(20), nullable=False)
    section = db.Column(db.String(5), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='present')  # present, absent, late, half_day
    marked_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    remarks = db.Column(db.Text)
    
    # Relationships
    marker = db.relationship('User', foreign_keys=[marked_by])
    
    __table_args__ = (db.UniqueConstraint('organization_id', 'student_id', 'date'),)
    
    def __repr__(self):
        return f'<Attendance {self.student.name} - {self.date}: {self.status}>'

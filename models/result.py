# models/result.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

db = SQLAlchemy()

from models.base import BaseModel

class Result(BaseModel):
    __tablename__ = 'results'
    
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(UUID(as_uuid=True), db.ForeignKey('subjects.id'), nullable=False)
    term = db.Column(db.Enum('First Term', 'Second Term', 'Third Term', 'Annual', 'Half Yearly', name='term_type'), default='Annual')
    academic_year = db.Column(db.String(10), nullable=False)
    marks = db.Column(db.Numeric(5, 2), nullable=False)
    max_marks = db.Column(db.Numeric(5, 2), default=100.0)
    grade = db.Column(db.String(5))
    remarks = db.Column(db.Text)
    exam_date = db.Column(db.Date)
    entered_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    verified_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    is_verified = db.Column(db.Boolean, default=False)
    
    __table_args__ = (db.UniqueConstraint('organization_id', 'student_id', 'subject_id', 'term', 'academic_year'),)
    
    def __repr__(self):
        return f'<Result {self.student.name} - {self.subject.name}: {self.marks}>'
    
    @property
    def percentage(self):
        return round((self.marks / self.max_marks) * 100, 2) if self.max_marks > 0 else 0
    
    def calculate_grade(self):
        """Calculate grade based on percentage"""
        percentage = self.percentage
        if percentage >= 90:
            return 'A+'
        elif percentage >= 80:
            return 'A'
        elif percentage >= 70:
            return 'B+'
        elif percentage >= 60:
            return 'B'
        elif percentage >= 50:
            return 'C+'
        elif percentage >= 40:
            return 'C'
        else:
            return 'F'


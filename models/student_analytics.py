from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from .base import db, BaseModel

class StudentAnalytics(BaseModel):
    """Model for storing calculated analytics data for individual students.
    
    This model stores pre-calculated analytics to improve dashboard performance
    and reduce database load during analytics queries.
    """
    __tablename__ = 'student_analytics'
    
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id'), nullable=False)
    academic_year = db.Column(db.String(10), nullable=False)
    term = db.Column(db.Enum('First Term', 'Second Term', 'Third Term', 'Annual', 'Half Yearly', name='term_type'), default='Annual')
    average_marks = db.Column(db.Numeric(5, 2))
    rank_in_class = db.Column(db.Integer)
    attendance_percentage = db.Column(db.Numeric(5, 2))
    improvement_percentage = db.Column(db.Numeric(5, 2))  # Compared to previous term
    strengths = db.Column(db.ARRAY(db.String(50)))  # Array of subject names
    weaknesses = db.Column(db.ARRAY(db.String(50)))  # Array of subject names
    recommendations = db.Column(db.Text)
    last_calculated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship('Student', backref='analytics', lazy=True)
    
    __table_args__ = (db.UniqueConstraint('organization_id', 'student_id', 'academic_year', 'term'),)
    
    def __repr__(self):
        return f'<StudentAnalytics {self.student.name} - {self.academic_year} {self.term}>'
    
    def to_dict(self):
        """Convert model to dictionary for API responses and caching"""
        return {
            'id': str(self.id),
            'student_id': str(self.student_id),
            'academic_year': self.academic_year,
            'term': self.term,
            'average_marks': float(self.average_marks) if self.average_marks else 0,
            'rank_in_class': self.rank_in_class,
            'attendance_percentage': float(self.attendance_percentage) if self.attendance_percentage else 0,
            'improvement_percentage': float(self.improvement_percentage) if self.improvement_percentage else 0,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'recommendations': self.recommendations,
            'last_calculated': self.last_calculated.isoformat() if self.last_calculated else None,
            'organization_id': str(self.organization_id)
        }
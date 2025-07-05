# models/student.py
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from .base import db, BaseModel
from .base import Attendance

class Student(BaseModel):
    __tablename__ = 'students'
    
    roll_no = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(20), nullable=False)
    section = db.Column(db.String(5), nullable=False)
    gender = db.Column(db.String(10))
    date_of_birth = db.Column(db.Date)
    admission_date = db.Column(db.Date, default=datetime.utcnow().date())
    guardian_name = db.Column(db.String(100))
    guardian_phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    photo_url = db.Column(db.Text)
    student_id = db.Column(db.String(50))
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    
    # Relationships
    results = db.relationship('Result', backref='student', lazy=True)
    attendance_records = db.relationship('Attendance', backref='student', lazy=True)
    
    __table_args__ = (db.UniqueConstraint('organization_id', 'roll_no'),)
    
    def __repr__(self):
        return f'<Student {self.name} ({self.roll_no})>'
    
    @property
    def total_attendance(self):
        """Calculate total attendance percentage"""
        total_days = db.session.query(Attendance).filter_by(
            student_id=self.id,
            organization_id=self.organization_id
        ).count()
        
        if total_days == 0:
            return 0
        
        present_days = db.session.query(Attendance).filter_by(
            student_id=self.id,
            organization_id=self.organization_id,
            status='present'
        ).count()
        
        return round((present_days / total_days) * 100, 2)

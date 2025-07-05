# models/base.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from sqlalchemy.ext.declarative import declared_attr

# Create database instance
db = SQLAlchemy()

class BaseModel(db.Model):
    """Base model with common fields for multi-tenancy"""
    __abstract__ = True
    
    @declared_attr
    def id(cls):
        return db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    @declared_attr
    def organization_id(cls):
        return db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)

    @declared_attr
    def created_at(cls):
        return db.Column(db.DateTime, default=datetime.utcnow)

    @declared_attr
    def updated_at(cls):
        return db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @declared_attr
    def deleted_at(cls):
        return db.Column(db.DateTime, nullable=True)
    
    def soft_delete(self):
        """Soft delete the record"""
        self.deleted_at = datetime.utcnow()
        db.session.commit()
        
    def restore(self):
        """Restore soft deleted record"""
        self.deleted_at = None
        db.session.commit()
    
    @property
    def is_deleted(self):
        return self.deleted_at is not None
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
class Attendance(BaseModel):
    """Model for student attendance records"""
    __tablename__ = 'attendance'
    
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # present, absent, late
    remarks = db.Column(db.Text)
    recorded_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    
# models/student.py
from models.subject import Subject


# Initialize database
def init_db(app):
    """Initialize database with app context"""
    with app.app_context():
        db.create_all()
        
        # Create default subject templates
        default_subjects = [
            {'name': 'Mathematics', 'code': 'MATH', 'is_template': True},
            {'name': 'English', 'code': 'ENG', 'is_template': True},
            {'name': 'Science', 'code': 'SCI', 'is_template': True},
            {'name': 'Social Studies', 'code': 'SS', 'is_template': True},
            {'name': 'Hindi', 'code': 'HIN', 'is_template': True},
            {'name': 'Computer Science', 'code': 'CS', 'is_template': True},
        ]
        
        for subject_data in default_subjects:
            if not Subject.query.filter_by(name=subject_data['name'], is_template=True).first():
                subject = Subject(**subject_data, organization_id=None)
                db.session.add(subject)
        
        db.session.commit()
        print("Database initialized with default templates")
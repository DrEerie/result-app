# models/base.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

db = SQLAlchemy()

class BaseModel(db.Model):
    """Base model with common fields for multi-tenancy"""
    __abstract__ = True
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
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
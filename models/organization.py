# models/organization.py
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from .base import db

class Organization(db.Model):
    __tablename__ = 'organizations'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    logo_url = db.Column(db.Text)
    website = db.Column(db.String(255))
    established_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    settings = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    users = db.relationship('User', backref='organization', lazy=True)
    students = db.relationship('Student', backref='organization', lazy=True)
    subjects = db.relationship('Subject', backref='organization', lazy=True)
    subscription = db.relationship('Subscription', backref='organization', uselist=False, lazy=True)
    
    def __repr__(self):
        return f'<Organization {self.name}>'
    
    @property
    def current_subscription(self):
        return self.subscription

# models/usage_tracking.py

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

db = SQLAlchemy()

class UsageTracking(db.Model):
    __tablename__ = 'usage_tracking'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = db.Column(UUID(as_uuid=True), db.ForeignKey('organizations.id'))
    feature = db.Column(db.String(100), nullable=False)
    usage_count = db.Column(db.Integer, default=1)
    metadata = db.Column(db.JSON, default=dict)
    date = db.Column(db.Date, default=datetime.utcnow().date())
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = db.relationship('Organization')
    
    __table_args__ = (db.UniqueConstraint('organization_id', 'feature', 'date'),)
    
    def __repr__(self):
        return f'<UsageTracking {self.feature} - {self.usage_count}>'

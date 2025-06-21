from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    cls = db.Column(db.String(20), nullable=False)
    section = db.Column(db.String(5), nullable=False)

    results = db.relationship('Result', backref='student', lazy=True)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    max_marks = db.Column(db.Float, nullable=False, default=100.0)
    class_name = db.Column(db.String(20), nullable=True)  # Made nullable for backward compatibility
    
    def __init__(self, name, max_marks=100.0, class_name=None):
        self.name = name
        self.max_marks = max_marks
        self.class_name = class_name

    results = db.relationship('Result', backref='subject', lazy=True)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    term = db.Column(db.String(20), nullable=False, default='Annual')
    session = db.Column(db.String(10), nullable=False, 
                       default=lambda: f"{datetime.now().year}-{datetime.now().year + 1}")
    marks = db.Column(db.Float, nullable=False)
    max_marks = db.Column(db.Float, default=100.0)

# Add migration helper
def init_db(app):
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()

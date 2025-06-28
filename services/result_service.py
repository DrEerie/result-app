from services.base_service import BaseService
from models.result import Result
from models.student import Student
from models.subject import Subject
from models.class_settings import ClassSettings
from flask import g

class ResultService(BaseService):
    def __init__(self):
        super().__init__()
        
    def get_student_results(self, student_id):
        """Get all results for a student"""
        return Result.query.filter_by(student_id=student_id, organization_id=g.organization_id).all()
    
    def get_class_results(self, class_name):
        """Get all results for a class"""
        students = Student.query.filter_by(class_name=class_name, organization_id=g.organization_id).all()
        student_ids = [student.id for student in students]
        return Result.query.filter(Result.student_id.in_(student_ids), Result.organization_id==g.organization_id).all()
    
    def create_result(self, data):
        """Create a new result"""
        result = Result(**data, organization_id=g.organization_id)
        self.db.session.add(result)
        self.db.session.commit()
        return result
    
    def update_result(self, result_id, data):
        """Update an existing result"""
        result = Result.query.get_or_404(result_id)
        if result.organization_id != g.organization_id:
            raise PermissionError("Not authorized to access this result")
        for key, value in data.items():
            setattr(result, key, value)
        self.db.session.commit()
        return result
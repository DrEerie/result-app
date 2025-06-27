# services/student_service.py
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from models.student import Student
from models.base import db
from services.base_service import BaseService
from utils.validations import StudentValidator, ValidationError, validate_bulk_data
from utils.error_handlers import ResourceNotFoundError, DuplicateResourceError, BusinessLogicError, audit_log

class StudentService(BaseService):
    """Service layer for student-related operations"""
    
    def __init__(self, db_session: Session = None):
        super().__init__(db_session or db.session)
    
    @audit_log("create_student", "student")
    def create(self, data: Dict[str, Any], user_id: int, organization_id: int) -> Dict[str, Any]:
        """Create a new student"""
        try:
            # Validate input data
            StudentValidator.validate_student_data(data)
            
            # Check for duplicate roll number in same organization and class
            existing_student = self.db.query(Student).filter(
                and_(
                    Student.organization_id == organization_id,
                    Student.roll_number == data['roll_number'],
                    Student.class_name == data['class_name']
                )
            ).first()
            
            if existing_student:
                raise DuplicateResourceError("Student", "roll number in this class")
            
            # Create new student
            student = Student(
                name=data['name'].strip(),
                roll_number=data['roll_number'].strip(),
                class_name=data['class_name'].strip(),
                email=data.get('email', '').strip() if data.get('email') else None,
                phone=data.get('phone', '').strip() if data.get('phone') else None,
                date_of_birth=data.get('date_of_birth'),
                address=data.get('address', '').strip() if data.get('address') else None,
                parent_name=data.get('parent_name', '').strip() if data.get('parent_name') else None,
                parent_phone=data.get('parent_phone', '').strip() if data.get('parent_phone') else None,
                organization_id=organization_id,
                created_by=user_id
            )
            
            self.db.add(student)
            self.db.commit()
            
            self._log_operation("create_student", {
                'student_id': student.id,
                'roll_number': student.roll_number,
                'class_name': student.class_name
            })
            
            return {
                'success': True,
                'data': student.to_dict(),
                'message': 'Student created successfully'
            }
            
        except (ValidationError, DuplicateResourceError) as e:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            return self._handle_db_error(e, "create_student")
    
    def get_by_id(self, student_id: int, user_id: int, organization_id: int) -> Dict[str, Any]:
        """Get student by ID with tenant validation"""
        try:
            student = self.db.query(Student).filter(
                and_(
                    Student.id == student_id,
                    Student.organization_id == organization_id
                )
            ).first()
            
            if not student:
                raise ResourceNotFoundError("Student", student_id)
            
            return {
                'success': True,
                'data': student.to_dict()
            }
            
        except ResourceNotFoundError:
            raise
        except Exception as e:
            return self._handle_db_error(e, "get_student_by_id")
    
    @audit_log("update_student", "student")
    def update(self, student_id: int, data: Dict[str, Any], user_id: int, organization_id: int) -> Dict[str, Any]:
        """Update existing student"""
        try:
            # Validate input data
            StudentValidator.validate_student_data(data)
            
            # Get existing student
            student = self.db.query(Student).filter(
                and_(
                    Student.id == student_id,
                    Student.organization_id == organization_id
                )
            ).first()
            
            if not student:
                raise ResourceNotFoundError("Student", student_id)
            
            # Check for duplicate roll number if roll number is being changed
            if ('roll_number' in data and data['roll_number'] != student.roll_number) or \
               ('class_name' in data and data['class_name'] != student.class_name):
                
                existing_student = self.db.query(Student).filter(
                    and_(
                        Student.organization_id == organization_id,
                        Student.roll_number == data.get('roll_number', student.roll_number),
                        Student.class_name == data.get('class_name', student.class_name),
                        Student.id != student_id
                    )
                ).first()
                
                if existing_student:
                    raise DuplicateResourceError("Student", "roll number in this class")
            
            # Update student fields
            for field, value in data.items():
                if hasattr(student, field):
                    setattr(student, field, value.strip() if isinstance(value, str) else value)
            
            student.updated_by = user_id
            self.db.commit()
            
            self._log_operation("update_student", {
                'student_id': student.id,
                'updated_fields': list(data.keys())
            })
            
            return {
                'success': True,
                'data': student.to_dict(),
                'message': 'Student updated successfully'
            }
            
        except (ValidationError, ResourceNotFoundError, DuplicateResourceError):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            return self._handle_db_error(e, "update_student")
    
    @audit_log("delete_student", "student")
    def delete(self, student_id: int, user_id: int, organization_id: int) -> Dict[str, Any]:
        """Delete student"""
        try:
            student = self.db.query(Student).filter(
                and_(
                    Student.id == student_id,
                    Student.organization_id == organization_id
                )
            ).first()
            
            if not student:
                raise ResourceNotFoundError("Student", student_id)
            
            # Check if student has results
            from models.result import Result
            has_results = self.db.query(Result).filter(Result.student_id == student_id).first()
            
            if has_results:
                raise BusinessLogicError(
                    "Cannot delete student with existing results. Please delete results first.",
                    {'student_id': student_id, 'has_results': True}
                )
            
            self.db.delete(student)
            self.db.commit()
            
            self._log_operation("delete_student", {
                'student_id': student_id,
                'student_name': student.name
            })
            
            return {
                'success': True,
                'message': 'Student deleted successfully'
            }
            
        except (ResourceNotFoundError, BusinessLogicError):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            return self._handle_db_error(e, "delete_student")
    
    def list_all(self, user_id: int, organization_id: int, **filters) -> Dict[str, Any]:
        """List all students with filtering and pagination"""
        try:
            query = self.db.query(Student).filter(Student.organization_id == organization_id)
            
            # Apply filters
            if filters.get('class_name'):
                query = query.filter(Student.class_name == filters['class_name'])
            
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Student.name.ilike(search_term),
                        Student.roll_number.ilike(search_term),
                        Student.email.ilike(search_term)
                    )
                )
            
            # Apply sorting
            sort_by = filters.get('sort_by', 'name')
            sort_order = filters.get('sort_order', 'asc')
            
            if hasattr(Student, sort_by):
                if sort_order.lower() == 'desc':
                    query = query.order_by(getattr(Student, sort_by).desc())
                else:
                    query = query.order_by(getattr(Student, sort_by).asc())
            
            # Apply pagination
            page = filters.get('page', 1)
            per_page = filters.get('per_page', 20)
            
            return self._paginate_query(query, page, per_page)
            
        except Exception as e:
            return self._handle_db_error(e, "list_students")
    
    def get_by_class(self, class_name: str, user_id: int, organization_id: int) -> Dict[str, Any]:
        """Get all students in a specific class"""
        try:
            students = self.db.query(Student).filter(
                and_(
                    Student.organization_id == organization_id,
                    Student.class_name == class_name
                )
            ).order_by(Student.roll_number).all()
            
            return {
                'success': True,
                'data': [student.to_dict() for student in students],
                'total': len(students)
            }
            
        except Exception as e:
            return self._handle_db_error(e, "get_students_by_class")
    
    def get_classes(self, user_id: int, organization_id: int) -> Dict[str, Any]:
        """Get all unique class names for the organization"""
        try:
            classes = self.db.query(Student.class_name).filter(
                Student.organization_id == organization_id
            ).distinct().order_by(Student.class_name).all()
            
            class_list = [cls[0] for cls in classes]
            
            return {
                'success': True,
                'data': class_list,
                'total': len(class_list)
            }
            
        except Exception as e:
            return self._handle_db_error(e, "get_classes")
    
    @audit_log("bulk_create_students", "student")
    def bulk_create(self, students_data: List[Dict[str, Any]], user_id: int, organization_id: int) -> Dict[str, Any]:
        """Create multiple students in bulk"""
        try:
            # Validate all student data
            validation_result = validate_bulk_data(students_data, StudentValidator.validate_student_data)
            
            if validation_result['errors']:
                return {
                    'success': False,
                    'errors': validation_result['errors'],
                    'message': f"Validation failed for {validation_result['error_count']} records"
                }
            
            valid_students = validation_result['valid_records']
            created_students = []
            duplicate_errors = []
            
            for idx, student_data in enumerate(valid_students):
                try:
                    # Check for duplicate roll number
                    existing_student = self.db.query(Student).filter(
                        and_(
                            Student.organization_id == organization_id,
                            Student.roll_number == student_data['roll_number'],
                            Student.class_name == student_data['class_name']
                        )
                    ).first()
                    
                    if existing_student:
                        duplicate_errors.append({
                            'row': idx + 1,
                            'field': 'roll_number',
                            'message': f"Student with roll number {student_data['roll_number']} already exists in class {student_data['class_name']}",
                            'code': 'duplicate_roll_number'
                        })
                        continue
                    
                    # Create student
                    student = Student(
                        name=student_data['name'].strip(),
                        roll_number=student_data['roll_number'].strip(),
                        class_name=student_data['class_name'].strip(),
                        email=student_data.get('email', '').strip() if student_data.get('email') else None,
                        phone=student_data.get('phone', '').strip() if student_data.get('phone') else None,
                        date_of_birth=student_data.get('date_of_birth'),
                        address=student_data.get('address', '').strip() if student_data.get('address') else None,
                        parent_name=student_data.get('parent_name', '').strip() if student_data.get('parent_name') else None,
                        parent_phone=student_data.get('parent_phone', '').strip() if student_data.get('parent_phone') else None,
                        organization_id=organization_id,
                        created_by=user_id
                    )
                    
                    self.db.add(student)
                    created_students.append(student_data)
                    
                except Exception as e:
                    duplicate_errors.append({
                        'row': idx + 1,
                        'field': 'general',
                        'message': f"Error creating student: {str(e)}",
                        'code': 'creation_error'
                    })
            
            # Commit all successful creates
            if created_students:
                self.db.commit()
            
            self._log_operation("bulk_create_students", {
                'total_attempted': len(valid_students),
                'successfully_created': len(created_students),
                'duplicate_errors': len(duplicate_errors)
            })
            
            return {
                'success': True,
                'data': {
                    'created_count': len(created_students),
                    'duplicate_errors': duplicate_errors,
                    'total_processed': len(valid_students)
                },
                'message': f"Successfully created {len(created_students)} students"
            }
            
        except Exception as e:
            self.db.rollback()
            return self._handle_db_error(e, "bulk_create_students")
    
    def search_students(self, search_term: str, user_id: int, organization_id: int, 
                       class_filter: str = None, limit: int = 10) -> Dict[str, Any]:
        """Search students by name, roll number, or email"""
        try:
            query = self.db.query(Student).filter(
                Student.organization_id == organization_id
            )
            if class_filter:
                query = query.filter(Student.class_name == class_filter)
            if search_term:
                query = query.filter(
                    or_(
                        Student.name.ilike(f"%{search_term}%"),
                        Student.roll_number.ilike(f"%{search_term}%"),
                        Student.email.ilike(f"%{search_term}%")
                    )
                )
            students = query.limit(limit).all()
            return {
                'success': True,
                'data': students
            }
        except Exception as e:
            return self._handle_db_error(e, "search_students")
# utils/validations.py
import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from flask import current_app

class ValidationError(Exception):
    """Custom validation error exception"""
    def __init__(self, message: str, field: str = None, code: str = None):
        self.message = message
        self.field = field
        self.code = code
        super().__init__(self.message)

class Validator:
    """Comprehensive validation utility class"""
    
    # Common regex patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^\+?1?-?\.?\s?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$')
    NAME_PATTERN = re.compile(r'^[a-zA-Z\s\-\'\.]{2,50}$')
    
    @staticmethod
    def validate_required(value: Any, field_name: str) -> None:
        """Validate that a field is not empty"""
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"{field_name} is required", field_name, "required")
    
    @staticmethod
    def validate_string_length(value: str, field_name: str, min_length: int = 0, max_length: int = None) -> None:
        """Validate string length"""
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string", field_name, "invalid_type")
        
        if len(value) < min_length:
            raise ValidationError(f"{field_name} must be at least {min_length} characters", field_name, "min_length")
        
        if max_length and len(value) > max_length:
            raise ValidationError(f"{field_name} must be no more than {max_length} characters", field_name, "max_length")
    
    @staticmethod
    def validate_email(email: str, field_name: str = "Email") -> None:
        """Validate email format"""
        if not email or not Validator.EMAIL_PATTERN.match(email):
            raise ValidationError(f"{field_name} must be a valid email address", field_name.lower(), "invalid_email")
    
    @staticmethod
    def validate_phone(phone: str, field_name: str = "Phone") -> None:
        """Validate phone number format"""
        if phone and not Validator.PHONE_PATTERN.match(phone):
            raise ValidationError(f"{field_name} must be a valid phone number", field_name.lower(), "invalid_phone")
    
    @staticmethod
    def validate_name(name: str, field_name: str) -> None:
        """Validate name format"""
        if not name or not Validator.NAME_PATTERN.match(name):
            raise ValidationError(f"{field_name} must contain only letters, spaces, hyphens, apostrophes, and periods", field_name.lower(), "invalid_name")
    
    @staticmethod
    def validate_numeric(value: Any, field_name: str, min_value: float = None, max_value: float = None) -> None:
        """Validate numeric values"""
        try:
            num_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a valid number", field_name.lower(), "invalid_number")
        
        if min_value is not None and num_value < min_value:
            raise ValidationError(f"{field_name} must be at least {min_value}", field_name.lower(), "min_value")
        
        if max_value is not None and num_value > max_value:
            raise ValidationError(f"{field_name} must be no more than {max_value}", field_name.lower(), "max_value")
    
    @staticmethod
    def validate_integer(value: Any, field_name: str, min_value: int = None, max_value: int = None) -> None:
        """Validate integer values"""
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a valid integer", field_name.lower(), "invalid_integer")
        
        if min_value is not None and int_value < min_value:
            raise ValidationError(f"{field_name} must be at least {min_value}", field_name.lower(), "min_value")
        
        if max_value is not None and int_value > max_value:
            raise ValidationError(f"{field_name} must be no more than {max_value}", field_name.lower(), "max_value")
    
    @staticmethod
    def validate_date(date_str: str, field_name: str, date_format: str = "%Y-%m-%d") -> datetime:
        """Validate date format and return datetime object"""
        try:
            return datetime.strptime(date_str, date_format)
        except ValueError:
            raise ValidationError(f"{field_name} must be in format {date_format}", field_name.lower(), "invalid_date")
    
    @staticmethod
    def validate_choice(value: Any, choices: List[Any], field_name: str) -> None:
        """Validate that value is in allowed choices"""
        if value not in choices:
            raise ValidationError(f"{field_name} must be one of: {', '.join(map(str, choices))}", field_name.lower(), "invalid_choice")
    
    @staticmethod
    def validate_list(value: Any, field_name: str, min_items: int = 0, max_items: int = None) -> None:
        """Validate list/array values"""
        if not isinstance(value, list):
            raise ValidationError(f"{field_name} must be a list", field_name.lower(), "invalid_type")
        
        if len(value) < min_items:
            raise ValidationError(f"{field_name} must have at least {min_items} items", field_name.lower(), "min_items")
        
        if max_items and len(value) > max_items:
            raise ValidationError(f"{field_name} must have no more than {max_items} items", field_name.lower(), "max_items")

class StudentValidator:
    """Specific validators for student data"""
    
    @staticmethod
    def validate_student_data(data: Dict[str, Any]) -> None:
        """Validate complete student data"""
        # Required fields
        Validator.validate_required(data.get('name'), 'Student name')
        Validator.validate_required(data.get('roll_number'), 'Roll number')
        Validator.validate_required(data.get('class_name'), 'Class name')
        
        # Validate name
        Validator.validate_name(data['name'], 'Student name')
        Validator.validate_string_length(data['name'], 'Student name', 2, 100)
        
        # Validate roll number
        Validator.validate_string_length(data['roll_number'], 'Roll number', 1, 20)
        
        # Validate class name
        Validator.validate_string_length(data['class_name'], 'Class name', 1, 50)
        
        # Optional fields
        if data.get('email'):
            Validator.validate_email(data['email'])
        
        if data.get('phone'):
            Validator.validate_phone(data['phone'])
        
        if data.get('date_of_birth'):
            birth_date = Validator.validate_date(data['date_of_birth'], 'Date of birth')
            if birth_date > datetime.now():
                raise ValidationError("Date of birth cannot be in the future", "date_of_birth", "future_date")

class ResultValidator:
    """Specific validators for result data"""
    
    @staticmethod
    def validate_result_data(data: Dict[str, Any]) -> None:
        """Validate complete result data"""
        # Required fields
        Validator.validate_required(data.get('student_id'), 'Student ID')
        Validator.validate_required(data.get('subject_id'), 'Subject ID')
        Validator.validate_required(data.get('marks_obtained'), 'Marks obtained')
        Validator.validate_required(data.get('total_marks'), 'Total marks')
        
        # Validate IDs
        Validator.validate_integer(data['student_id'], 'Student ID', 1)
        Validator.validate_integer(data['subject_id'], 'Subject ID', 1)
        
        # Validate marks
        Validator.validate_numeric(data['marks_obtained'], 'Marks obtained', 0)
        Validator.validate_numeric(data['total_marks'], 'Total marks', 1)
        
        # Validate marks logic
        if float(data['marks_obtained']) > float(data['total_marks']):
            raise ValidationError("Marks obtained cannot be greater than total marks", "marks_obtained", "invalid_marks")
        
        # Optional fields
        if data.get('exam_date'):
            exam_date = Validator.validate_date(data['exam_date'], 'Exam date')
            if exam_date > datetime.now():
                raise ValidationError("Exam date cannot be in the future", "exam_date", "future_date")

class OrganizationValidator:
    """Specific validators for organization data"""
    
    @staticmethod
    def validate_organization_data(data: Dict[str, Any]) -> None:
        """Validate complete organization data"""
        # Required fields
        Validator.validate_required(data.get('name'), 'Organization name')
        Validator.validate_required(data.get('email'), 'Organization email')
        
        # Validate name
        Validator.validate_string_length(data['name'], 'Organization name', 2, 100)
        
        # Validate email
        Validator.validate_email(data['email'], 'Organization email')
        
        # Optional fields
        if data.get('phone'):
            Validator.validate_phone(data['phone'], 'Organization phone')
        
        if data.get('address'):
            Validator.validate_string_length(data['address'], 'Address', 0, 500)
        
        if data.get('website'):
            website_pattern = re.compile(r'^https?://[^\s/$.?#].[^\s]*$')
            if not website_pattern.match(data['website']):
                raise ValidationError("Website must be a valid URL", "website", "invalid_url")

def validate_bulk_data(data_list: List[Dict[str, Any]], validator_func, max_records: int = 1000) -> List[Dict[str, Any]]:
    """Validate bulk data with comprehensive error reporting"""
    if not isinstance(data_list, list):
        raise ValidationError("Data must be a list", "data", "invalid_type")
    
    if len(data_list) == 0:
        raise ValidationError("At least one record is required", "data", "empty_list")
    
    if len(data_list) > max_records:
        raise ValidationError(f"Maximum {max_records} records allowed", "data", "too_many_records")
    
    errors = []
    valid_records = []
    
    for index, record in enumerate(data_list):
        try:
            validator_func(record)
            valid_records.append(record)
        except ValidationError as e:
            errors.append({
                'row': index + 1,
                'field': e.field,
                'message': e.message,
                'code': e.code
            })
    
    return {
        'valid_records': valid_records,
        'errors': errors,
        'total_records': len(data_list),
        'valid_count': len(valid_records),
        'error_count': len(errors)
    }
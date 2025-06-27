from typing import Dict, List, Union
import json
import os

# Load grading system from config
def load_grading_config() -> Dict:
    config_path = os.path.join(os.path.dirname(__file__), 'grading_config.json')
    try:
        with open(config_path) as f:
            return json.load(f)
    except:
        return {
            'A+': {'min': 80, 'max': 100},
            'A': {'min': 70, 'max': 79.99},
            'B': {'min': 60, 'max': 69.99},
            'C': {'min': 50, 'max': 59.99},
            'D': {'min': 40, 'max': 49.99},
            'F': {'min': 0, 'max': 39.99}
        }

def calculate_grade(percentage: float) -> str:
    """Calculate grade with input validation"""
    try:
        if not isinstance(percentage, (int, float)):
            raise ValueError("Percentage must be a number")
            
        percentage = float(percentage)
        if percentage < 0 or percentage > 100:
            raise ValueError("Percentage must be between 0 and 100")
            
        grading_system = load_grading_config()
        for grade, range_ in grading_system.items():
            if range_['min'] <= percentage <= range_['max']:
                return grade
                
        return 'F'
    except Exception as e:
        print(f"Error calculating grade: {str(e)}")
        return 'F'

def calculate_percentage(marks, max_marks=100):
    """Calculate percentage from marks using provided max_marks"""
    if max_marks == 0:
        return 0
    return round((marks / max_marks) * 100, 2)

def is_passing_grade(grade):
    """Check if grade is passing (not F)"""
    return grade != 'F'

def calculate_student_overall_result(results):
    """Calculate overall result using dynamic max marks"""
    if not results:
        return {
            'total_marks': 0,
            'total_max_marks': 0,
            'overall_percentage': 0,
            'overall_grade': 'F',
            'is_pass': False,
            'subject_results': []
        }
    
    total_marks = 0
    total_max_marks = 0
    subject_results = []
    has_failed_subject = False
    
    for result in results:
        subject = result.subject
        marks = result.marks
        max_marks = subject.max_marks
        
        # Calculate percentage based on subject's max marks
        percentage = calculate_percentage(marks, max_marks)
        grade = calculate_grade(percentage)
        
        if not is_passing_grade(grade):
            has_failed_subject = True
        
        subject_results.append({
            'subject_name': subject.name,
            'marks': marks,
            'max_marks': max_marks,
            'percentage': percentage,
            'grade': grade,
            'is_pass': is_passing_grade(grade)
        })
        
        total_marks += marks
        total_max_marks += max_marks
    
    # Calculate overall percentage based on total marks and total max marks
    overall_percentage = calculate_percentage(total_marks, total_max_marks)
    overall_grade = calculate_grade(overall_percentage)
    is_pass = not has_failed_subject and is_passing_grade(overall_grade)
    
    return {
        'total_marks': total_marks,
        'total_max_marks': total_max_marks,
        'overall_percentage': overall_percentage,
        'overall_grade': overall_grade,
        'is_pass': is_pass,
        'subject_results': subject_results
    }

def get_grade_color(grade):
    """Get color class for grade display"""
    grade_colors = {
        'A+': 'text-green-600 bg-green-100',
        'A': 'text-green-500 bg-green-50',
        'B': 'text-blue-500 bg-blue-50',
        'C': 'text-yellow-500 bg-yellow-50',
        'D': 'text-orange-500 bg-orange-50',
        'F': 'text-red-500 bg-red-50'
    }
    return grade_colors.get(grade, 'text-gray-500 bg-gray-50')

def get_result_status_color(is_pass):
    """Get color class for pass/fail status"""
    return 'text-green-600 bg-green-100' if is_pass else 'text-red-600 bg-red-100'
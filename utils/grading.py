def calculate_grade(percentage):
    """
    Calculate grade based on percentage
    80% above: A+
    70%-80%: A
    60%-70%: B
    50%-60%: C
    40%-50%: D
    Below 40%: F (Fail)
    """
    if percentage >= 80:
        return 'A+'
    elif percentage >= 70:
        return 'A'
    elif percentage >= 60:
        return 'B'
    elif percentage >= 50:
        return 'C'
    elif percentage >= 40:
        return 'D'
    else:
        return 'F'

def calculate_percentage(marks, max_marks=100):
    """Calculate percentage from marks"""
    if max_marks == 0:
        return 0
    return round((marks / max_marks) * 100, 2)

def is_passing_grade(grade):
    """Check if grade is passing (not F)"""
    return grade != 'F'

def calculate_student_overall_result(results):
    """
    Calculate overall result for a student
    Args:
        results: List of Result objects for a student
    
    Returns:
        dict: {
            'total_marks': float,
            'total_max_marks': float,
            'overall_percentage': float,
            'overall_grade': str,
            'is_pass': bool,
            'subject_results': list of dict with subject details
        }
    """
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
        marks = result.marks
        max_marks = result.max_marks
        percentage = calculate_percentage(marks, max_marks)
        grade = calculate_grade(percentage)
        
        # Check if student failed in this subject
        if not is_passing_grade(grade):
            has_failed_subject = True
        
        subject_results.append({
            'subject_name': result.subject.name,
            'marks': marks,
            'max_marks': max_marks,
            'percentage': percentage,
            'grade': grade,
            'is_pass': is_passing_grade(grade)
        })
        
        total_marks += marks
        total_max_marks += max_marks
    
    # Calculate overall percentage and grade
    overall_percentage = calculate_percentage(total_marks, total_max_marks)
    overall_grade = calculate_grade(overall_percentage)
    
    # Student fails overall if failed in any subject OR overall percentage is below 40%
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
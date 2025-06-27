# routes/api_routes.py
from flask import Blueprint, request, jsonify, g
from auth.decorators import login_required
from middleware.subscription import feature_required
from services.result_service import ResultService
from services.student_service import StudentService
from services.analytics_service import AnalyticsService

api_bp = Blueprint('api', __name__)

@api_bp.route('/students', methods=['GET'])
@login_required
def get_students():
    """API endpoint to get students"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    class_name = request.args.get('class')
    
    students = StudentService.get_students_paginated(
        g.organization_id, 
        page=page, 
        per_page=per_page, 
        class_name=class_name
    )
    
    return jsonify({
        'students': [student.to_dict() for student in students.items],
        'total': students.total,
        'pages': students.pages,
        'current_page': students.page
    })

@api_bp.route('/results', methods=['GET'])
@login_required
def get_results():
    """API endpoint to get results"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    class_name = request.args.get('class')
    exam_type = request.args.get('exam')
    
    results = ResultService.get_results_paginated(
        g.organization_id, 
        page=page, 
        per_page=per_page, 
        class_name=class_name, 
        exam_type=exam_type
    )
    
    return jsonify({
        'results': [result.to_dict() for result in results.items],
        'total': results.total,
        'pages': results.pages,
        'current_page': results.page
    })

@api_bp.route('/analytics/summary', methods=['GET'])
@login_required
@feature_required('analytics')
def get_analytics_summary():
    """API endpoint for analytics summary"""
    class_name = request.args.get('class')
    exam_type = request.args.get('exam')
    
    summary = AnalyticsService.get_performance_summary(
        g.organization_id, 
        class_name=class_name, 
        exam_type=exam_type
    )
    
    return jsonify(summary)

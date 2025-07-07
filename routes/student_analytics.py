from flask import Blueprint, jsonify, request, render_template, current_app, abort, send_file
from flask_login import login_required, current_user
import uuid
import os

from middleware.feature_required import feature_required
from middleware.tenant_required import tenant_required
from services.student_analytics_service import StudentAnalyticsService
from models.student import Student
from jobs.analytics_jobs import calculate_student_analytics_task, generate_student_report_task

student_analytics_bp = Blueprint('student_analytics', __name__)

@student_analytics_bp.route('/dashboard/<uuid:student_id>')
@login_required
@tenant_required
@feature_required('analytics')
def student_dashboard(student_id):
    """Render the student analytics dashboard
    
    Args:
        student_id (UUID): The ID of the student
        
    Returns:
        HTML: The rendered dashboard template
    """
    # Get student
    student = Student.query.filter_by(
        id=student_id, 
        organization_id=current_user.organization_id
    ).first_or_404()
    
    # Get current academic year and term from request or use defaults
    academic_year = request.args.get('academic_year', '2023')
    term = request.args.get('term', 'Annual')
    
    # Get or calculate analytics
    analytics = StudentAnalyticsService.calculate_student_analytics(
        student_id, current_user.organization_id, academic_year, term
    )
    
    # Get comparison data
    comparison = StudentAnalyticsService.get_student_comparison(
        student_id, current_user.organization_id, academic_year, term
    )
    
    # Get performance trends
    period = request.args.get('period', '12months')
    trends = StudentAnalyticsService.get_student_performance_trends(
        student_id, current_user.organization_id, period
    )
    
    # Prepare data for charts
    trend_labels = [t['month'] for t in trends]
    trend_data = [t['average'] for t in trends]
    
    # Prepare subject comparison data
    subjects = []
    student_marks = []
    class_averages = []
    
    for subject, data in comparison.items():
        if subject != 'overall':
            subjects.append(subject)
            student_marks.append(data['student_marks'])
            class_averages.append(data['class_average'])
    
    return render_template(
        'dashboard/student_analytics.html',
        student=student,
        analytics=analytics,
        comparison=comparison,
        trend_labels=trend_labels,
        trend_data=trend_data,
        subjects=subjects,
        student_marks=student_marks,
        class_averages=class_averages,
        academic_year=academic_year,
        term=term,
        period=period
    )

@student_analytics_bp.route('/api/student/<uuid:student_id>')
@login_required
@tenant_required
@feature_required('analytics')
def get_student_analytics(student_id):
    """API endpoint to get student analytics
    
    Args:
        student_id (UUID): The ID of the student
        
    Returns:
        JSON: The student analytics data
    """
    # Get parameters
    academic_year = request.args.get('academic_year', '2023')
    term = request.args.get('term', 'Annual')
    
    # Get or calculate analytics
    analytics = StudentAnalyticsService.calculate_student_analytics(
        student_id, current_user.organization_id, academic_year, term
    )
    
    if not analytics:
        return jsonify({
            'status': 'error',
            'message': 'No results found for the student in the specified period'
        }), 404
    
    return jsonify({
        'status': 'success',
        'data': analytics.to_dict() if hasattr(analytics, 'to_dict') else analytics
    })

@student_analytics_bp.route('/api/student/<uuid:student_id>/comparison')
@login_required
@tenant_required
@feature_required('analytics')
def get_student_comparison(student_id):
    """API endpoint to get student comparison data
    
    Args:
        student_id (UUID): The ID of the student
        
    Returns:
        JSON: The comparison data
    """
    # Get parameters
    academic_year = request.args.get('academic_year', '2023')
    term = request.args.get('term', 'Annual')
    
    # Get comparison data
    comparison = StudentAnalyticsService.get_student_comparison(
        student_id, current_user.organization_id, academic_year, term
    )
    
    if not comparison:
        return jsonify({
            'status': 'error',
            'message': 'No comparison data found for the student'
        }), 404
    
    return jsonify({
        'status': 'success',
        'data': comparison
    })

@student_analytics_bp.route('/api/student/<uuid:student_id>/trends')
@login_required
@tenant_required
@feature_required('analytics')
def get_student_trends(student_id):
    """API endpoint to get student performance trends
    
    Args:
        student_id (UUID): The ID of the student
        
    Returns:
        JSON: The trend data
    """
    # Get parameters
    period = request.args.get('period', '12months')
    
    # Get trend data
    trends = StudentAnalyticsService.get_student_performance_trends(
        student_id, current_user.organization_id, period
    )
    
    if not trends:
        return jsonify({
            'status': 'error',
            'message': 'No trend data found for the student'
        }), 404
    
    return jsonify({
        'status': 'success',
        'data': trends
    })

@student_analytics_bp.route('/api/student/<uuid:student_id>/summary')
@login_required
@tenant_required
@feature_required('analytics')
def get_student_summary(student_id):
    """API endpoint to get a summary of student analytics
    
    Args:
        student_id (UUID): The ID of the student
        
    Returns:
        JSON: The summary data
    """
    # Get summary data
    summary = StudentAnalyticsService.get_student_analytics_summary(
        student_id, current_user.organization_id
    )
    
    return jsonify({
        'status': 'success',
        'data': summary
    })

@student_analytics_bp.route('/api/student/<uuid:student_id>/report', methods=['POST'])
@login_required
@tenant_required
@feature_required('analytics')
def generate_student_report(student_id):
    """API endpoint to generate a student report
    
    Args:
        student_id (UUID): The ID of the student
        
    Returns:
        JSON: Information about the report generation task
    """
    # Get parameters
    data = request.get_json() or {}
    academic_year = data.get('academic_year', request.form.get('academic_year', '2023'))
    term = data.get('term', request.form.get('term', 'Annual'))
    
    # Queue report generation task
    task = generate_student_report_task.delay(
        str(student_id), str(current_user.organization_id), academic_year, term
    )
    
    return jsonify({
        'status': 'success',
        'message': 'Report generation has been queued',
        'task_id': str(task.id)
    })

@student_analytics_bp.route('/api/report/<task_id>/status')
@login_required
@tenant_required
@feature_required('analytics')
def check_report_status(task_id):
    """API endpoint to check the status of a report generation task
    
    Args:
        task_id (str): The ID of the task
        
    Returns:
        JSON: The task status
    """
    # Import here to avoid circular imports
    from jobs.celery_app import celery_app
    
    # Check task status
    task = celery_app.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'status': 'pending',
            'message': 'Report generation is pending'
        }
    elif task.state == 'FAILURE':
        response = {
            'status': 'error',
            'message': str(task.info.get('message', 'Unknown error'))
        }
    elif task.state == 'SUCCESS':
        result = task.get()
        if result.get('status') == 'success':
            response = {
                'status': 'success',
                'message': 'Report generated successfully',
                'file_path': result.get('file_path'),
                'filename': result.get('filename')
            }
        else:
            response = {
                'status': 'error',
                'message': result.get('message', 'Unknown error')
            }
    else:
        response = {
            'status': 'processing',
            'message': 'Report generation is in progress'
        }
    
    return jsonify(response)

@student_analytics_bp.route('/api/report/download/<filename>')
@login_required
@tenant_required
@feature_required('analytics')
def download_report(filename):
    """API endpoint to download a generated report
    
    Args:
        filename (str): The filename of the report
        
    Returns:
        File: The report file
    """
    # Validate filename to prevent directory traversal
    if '..' in filename or '/' in filename:
        abort(400, 'Invalid filename')
    
    # Get reports directory
    reports_dir = current_app.config.get('REPORTS_DIR', 'reports')
    file_path = os.path.join(reports_dir, str(current_user.organization_id), filename)
    
    # Check if file exists
    if not os.path.isfile(file_path):
        abort(404, 'Report not found')
    
    # Check if file belongs to the current organization
    if str(current_user.organization_id) not in file_path:
        abort(403, 'Unauthorized access to report')
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

@student_analytics_bp.route('/api/class/<class_name>/analytics')
@login_required
@tenant_required
@feature_required('analytics')
def calculate_class_analytics(class_name):
    """API endpoint to trigger analytics calculation for a class
    
    Args:
        class_name (str): The name of the class
        
    Returns:
        JSON: Information about the calculation task
    """
    # Get parameters
    academic_year = request.args.get('academic_year', '2023')
    term = request.args.get('term', 'Annual')
    
    # Queue calculation task
    from jobs.analytics_jobs import calculate_all_student_analytics_task
    task = calculate_all_student_analytics_task.delay(
        str(current_user.organization_id), academic_year, term, class_name
    )
    
    return jsonify({
        'status': 'success',
        'message': f'Analytics calculation for class {class_name} has been queued',
        'task_id': str(task.id)
    })
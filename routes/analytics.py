# routes/analytics.py
from flask import Blueprint, request, jsonify, render_template, g
from auth.decorators import login_required, role_required
from middleware.subscription import feature_required
from services.analytics_service import AnalyticsService

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/')
@login_required
@feature_required('analytics')
def dashboard():
    """Analytics dashboard"""
    return render_template('analytics.html')

@analytics_bp.route('/api/performance-summary')
@login_required
@feature_required('analytics')
def performance_summary():
    """Get performance summary"""
    class_name = request.args.get('class')
    exam_type = request.args.get('exam')
    
    summary = AnalyticsService.get_performance_summary(
        g.organization_id, 
        class_name=class_name, 
        exam_type=exam_type
    )
    
    return jsonify(summary)

@analytics_bp.route('/api/grade-distribution')
@login_required
@feature_required('analytics')
def grade_distribution():
    """Get grade distribution"""
    class_name = request.args.get('class')
    subject = request.args.get('subject')
    
    distribution = AnalyticsService.get_grade_distribution(
        g.organization_id, 
        class_name=class_name, 
        subject=subject
    )
    
    return jsonify(distribution)

@analytics_bp.route('/api/trend-analysis')
@login_required
@feature_required('analytics')
def trend_analysis():
    """Get performance trends"""
    class_name = request.args.get('class')
    period = request.args.get('period', '6months')
    
    trends = AnalyticsService.get_performance_trends(
        g.organization_id, 
        class_name=class_name, 
        period=period
    )
    
    return jsonify(trends)

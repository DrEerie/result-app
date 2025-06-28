# routes/dashboard.py
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard home"""
    return render_template('dashboard/index.html')

@dashboard_bp.route('/results')
@login_required
def results():
    """Results management"""
    return render_template('dashboard/results.html')

@dashboard_bp.route('/students')
@login_required
def students():
    """Students management"""
    return render_template('dashboard/students.html')

@dashboard_bp.route('/analytics')
@login_required
def analytics():
    """Analytics dashboard"""
    return render_template('dashboard/analytics.html')

@dashboard_bp.route('/settings')
@login_required
def settings():
    """Settings page"""
    return render_template('dashboard/settings.html')
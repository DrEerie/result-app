# routes/main_routes.py
from flask import Blueprint, render_template, redirect, url_for, g
from auth.decorators import login_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Landing page"""
    return render_template('home.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')

@main_bp.route('/privacy')
def privacy():
    """Privacy policy"""
    return render_template('privacy.html')

@main_bp.route('/terms')
def terms():
    """Terms of service"""
    return render_template('terms.html')

@main_bp.route('/cookies')
def cookies():
    """Cookie policy"""
    return render_template('cookies.html')

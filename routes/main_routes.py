# routes/main_routes.py
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page - redirect authenticated users to dashboard"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('public/index.html')

@main_bp.route('/pricing')
def pricing():
    """Pricing page"""
    return render_template('public/pricing.html')

@main_bp.route('/features')
def features():
    """Features page"""
    return render_template('public/features.html')

@main_bp.route('/testimonials')
def testimonials():
    """Testimonials page"""
    return render_template('public/testimonials.html')

@main_bp.route('/faq')
def faq():
    """FAQ page"""
    return render_template('public/faq.html')

@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('public/contact.html')

@main_bp.route('/privacy')
def privacy():
    """Privacy policy"""
    return render_template('shared/privacy.html')

@main_bp.route('/terms')
def terms():
    """Terms of service"""
    return render_template('shared/terms.html')
@main_bp.route('/cookies')
def cookies():
    """Cookie policy"""
    return render_template('shared/cookies.html')
@main_bp.route('/404')
def not_found():
    """404 Not Found"""
    return render_template('shared/404.html'), 404
@main_bp.route('/500')
def server_error():
    """500 Internal Server Error"""
    return render_template('shared/500.html'), 500
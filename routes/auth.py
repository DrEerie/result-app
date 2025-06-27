# routes/auth.py (continuation)
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from services.auth_service import AuthService
from models.base import User, Organization
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Organization registration"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        # Validate required fields
        required_fields = ['org_name', 'org_email', 'admin_name', 'admin_email', 'admin_password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create slug from organization name
        slug = re.sub(r'[^a-zA-Z0-9-]', '-', data['org_name'].lower())
        slug = re.sub(r'-+', '-', slug).strip('-')
        
        # Check if organization already exists
        if Organization.query.filter_by(slug=slug).first():
            return jsonify({'error': 'Organization with this name already exists'}), 400
        
        # Prepare data
        org_data = {
            'name': data['org_name'],
            'slug': slug,
            'email': data['org_email'],
            'phone': data.get('org_phone'),
            'address': data.get('org_address')
        }
        
        admin_data = {
            'full_name': data['admin_name'],
            'email': data['admin_email'],
            'password': data['admin_password'],
            'phone': data.get('admin_phone')
        }
        
        # Register organization
        result = AuthService.register_organization(org_data, admin_data)
        
        if result['success']:
            flash('Organization registered successfully! Please log in.', 'success')
            return redirect(url_for('auth.login')) if not request.is_json else jsonify({'success': True})
        else:
            flash(result['error'], 'error')
            return redirect(url_for('auth.register')) if not request.is_json else jsonify({'error': result['error']}), 400
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        result = AuthService.login_user_with_supabase(email, password)
        
        if result['success']:
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard')) if not request.is_json else jsonify({'success': True})
        else:
            flash(result['error'], 'error')
            return redirect(url_for('auth.login')) if not request.is_json else jsonify({'error': result['error']}), 401
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    result = AuthService.logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.home'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Password reset request"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        try:
            from services.supabase_client import supabase_client
            supabase_client.get_client().auth.reset_password_email(email)
            flash('Password reset link sent to your email.', 'info')
            return redirect(url_for('auth.login')) if not request.is_json else jsonify({'success': True})
        except Exception as e:
            flash('Error sending reset email. Please try again.', 'error')
            return redirect(url_for('auth.forgot_password')) if not request.is_json else jsonify({'error': str(e)}), 400
    
    return render_template('auth/forgot_password.html')

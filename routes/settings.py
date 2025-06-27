# routes/settings.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, g
from auth.decorators import login_required, role_required
from services.settings_service import SettingsService
from models.subject import Subject
from models.class_settings import ClassSettings

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/')
@login_required
def index():
    """Settings dashboard"""
    return render_template('settings/index.html')

@settings_bp.route('/subjects')
@login_required
@role_required('admin', 'teacher')
def manage_subjects():
    """Manage subjects"""
    subjects = Subject.query.filter_by(organization_id=g.organization_id).all()
    return render_template('customization.html', subjects=subjects)

@settings_bp.route('/subjects/add', methods=['POST'])
@login_required
@role_required('admin', 'teacher')
def add_subject():
    """Add new subject"""
    data = request.get_json() if request.is_json else request.form
    
    subject_data = {
        'name': data.get('name'),
        'code': data.get('code'),
        'max_marks': data.get('max_marks'),
        'pass_marks': data.get('pass_marks'),
        'subject_type': data.get('subject_type', 'theory')
    }
    
    result = SettingsService.create_subject(subject_data, g.organization_id)
    
    if result['success']:
        flash('Subject added successfully!', 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('settings.manage_subjects')) if not request.is_json else jsonify(result)

@settings_bp.route('/class-settings')
@login_required
@role_required('admin', 'teacher')
def class_settings():
    """Manage class settings"""
    class_settings = ClassSettings.query.filter_by(organization_id=g.organization_id).all()
    return render_template('settings/class_settings.html', class_settings=class_settings)

@settings_bp.route('/class-settings/add', methods=['POST'])
@login_required
@role_required('admin', 'teacher')
def add_class_settings():
    """Add class settings"""
    data = request.get_json() if request.is_json else request.form
    
    settings_data = {
        'class_name': data.get('class_name'),
        'grading_system': data.get('grading_system'),
        'grading_config': data.get('grading_config'),
        'promotion_criteria': data.get('promotion_criteria')
    }
    
    result = SettingsService.create_class_settings(settings_data, g.organization_id)
    
    if result['success']:
        flash('Class settings saved successfully!', 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('settings.class_settings')) if not request.is_json else jsonify(result)

@settings_bp.route('/customize-marksheet')
@login_required
@role_required('admin', 'teacher')
def customize_marksheet():
    """Customize individual marksheet"""
    return render_template('customize_result.html')

@settings_bp.route('/customize-class-result')
@login_required
@role_required('admin', 'teacher')
def customize_class_result():
    """Customize class result sheet"""
    return render_template('customize_class_result.html')
@settings_bp.route('/customize-school-profile')
@login_required
@role_required('admin', 'teacher')
def customize_school_profile():
    """Customize school profile"""
    return render_template('customize_school_profile.html') 
@settings_bp.route('/customize-school-profile/save', methods=['POST'])
@login_required
@role_required('admin', 'teacher')
def save_school_profile():
    """Save customized school profile"""
    data = request.get_json() if request.is_json else request.form

    profile_data = {
        'name': data.get('name'),
        'address': data.get('address'),
        'phone': data.get('phone'),
        'email': data.get('email'),
        'website': data.get('website')
    }

    result = SettingsService.update_school_profile(profile_data, g.organization_id)

    if result['success']:
        flash('School profile updated successfully!', 'success')
    else:
        flash(result['error'], 'error')

    return redirect(url_for('settings.customize_school_profile')) if not request.is_json else jsonify(result)
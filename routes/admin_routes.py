# routes/admin_routes.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, g
from auth.decorators import login_required, admin_required
from services.auth_service import AuthService
from models.base import User, Subscription, UsageTracking, AuditLog
from models.organization import Organization

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    stats = {
        'total_users': User.query.filter_by(organization_id=g.organization_id).count(),
        'active_users': User.query.filter_by(organization_id=g.organization_id, is_active=True).count(),
        'subscription_tier': g.current_organization.subscription.tier if g.current_organization.subscription else 'free'
    }
    
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    """Manage users"""
    users = User.query.filter_by(organization_id=g.organization_id).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    """Add new user"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        user_data = {
            'full_name': data.get('full_name'),
            'email': data.get('email'),
            'password': data.get('password'),
            'role': data.get('role'),
            'phone': data.get('phone'),
            'employee_id': data.get('employee_id'),
            'department': data.get('department')
        }
        
        result = AuthService.create_user(user_data, g.organization_id)
        
        if result['success']:
            flash('User created successfully!', 'success')
            return redirect(url_for('admin.manage_users')) if not request.is_json else jsonify({'success': True})
        else:
            flash(result['error'], 'error')
    
    return render_template('admin/add_user.html')

@admin_bp.route('/subscription')
@login_required
@admin_required
def subscription_management():
    """Subscription management"""
    subscription = g.current_organization.subscription
    usage = UsageTracking.query.filter_by(organization_id=g.organization_id).all()
    
    return render_template('admin/subscription.html', subscription=subscription, usage=usage)

@admin_bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    """View audit logs"""
    page = request.args.get('page', 1, type=int)
    logs = AuditLog.query.filter_by(organization_id=g.organization_id)\
                        .order_by(AuditLog.created_at.desc())\
                        .paginate(page=page, per_page=50, error_out=False)
    
    return render_template('admin/audit_logs.html', logs=logs)

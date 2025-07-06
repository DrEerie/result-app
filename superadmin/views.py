"""
SuperAdmin Views for EveClus
Handles SuperAdmin dashboard, authentication, and management views.
"""

from flask import render_template, request, redirect, url_for, flash, jsonify, session, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
from . import superadmin_bp
from .decorators import superadmin_required, permission_required, master_admin_required, log_superadmin_action, Permissions
from .models import SuperAdmin, Tenant, SystemSettings, GlobalAudit, TenantMetrics, TenantStatus, SubscriptionTier
from .tenant_manager import TenantManager
from services.supabase_client import get_superadmin_client
import logging

logger = logging.getLogger(__name__)

@superadmin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """SuperAdmin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('superadmin/login.html')
        
        try:
            supabase = get_superadmin_client()
            
            # Get superadmin by username
            response = supabase.table('superadmins').select('*').eq('username', username).execute()
            
            if not response.data:
                flash('Invalid username or password.', 'error')
                return render_template('superadmin/login.html')
            
            superadmin = response.data[0]
            
            # Check password
            if not check_password_hash(superadmin['password_hash'], password):
                flash('Invalid username or password.', 'error')
                return render_template('superadmin/login.html')
            
            # Check if account is active
            if not superadmin.get('is_active', False):
                flash('Account is inactive. Please contact administrator.', 'error')
                return render_template('superadmin/login.html')
            
            # Update last login
            supabase.table('superadmins').update({
                'last_login': datetime.utcnow().isoformat()
            }).eq('id', superadmin['id']).execute()
            
            # Set session
            session['superadmin_id'] = superadmin['id']
            session['superadmin_username'] = superadmin['username']
            session['is_master'] = superadmin.get('is_master', False)
            
            # Log login
            supabase.table('global_audit_logs').insert({
                'superadmin_id': superadmin['id'],
                'action': 'login',
                'resource_type': 'superadmin',
                'description': f"SuperAdmin {username} logged in",
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'endpoint': request.endpoint,
                'method': request.method,
                'severity': 'info'
            }).execute()
            
            flash('Login successful!', 'success')
            return redirect(url_for('superadmin.dashboard'))
            
        except Exception as e:
            logger.error(f"SuperAdmin login error: {str(e)}")
            flash('Login failed. Please try again.', 'error')
            return render_template('superadmin/login.html')
    
    return render_template('superadmin/login.html')

@superadmin_bp.route('/logout')
def logout():
    """SuperAdmin logout"""
    try:
        if 'superadmin_id' in session:
            supabase = get_superadmin_client()
            supabase.table('global_audit_logs').insert({
                'superadmin_id': session['superadmin_id'],
                'action': 'logout',
                'resource_type': 'superadmin',
                'description': f"SuperAdmin {session.get('superadmin_username', 'unknown')} logged out",
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'endpoint': request.endpoint,
                'method': request.method,
                'severity': 'info'
            }).execute()
    except Exception as e:
        logger.error(f"Error logging logout: {str(e)}")
    
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('superadmin.login'))

@superadmin_bp.route('/dashboard')
@superadmin_required
def dashboard():
    return render_template('superadmin/dashboard.html')
@superadmin_bp.route('/tenants')
@superadmin_required
def tenants():
    return render_template('superadmin/tenants.html')


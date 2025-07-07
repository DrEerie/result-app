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
@log_superadmin_action('view', 'dashboard')
def dashboard():
    """SuperAdmin dashboard with system overview"""
    try:
        supabase = get_superadmin_client()
        
        # Get all tenants
        tenants_response = supabase.table('tenants').select('*').execute()
        tenants_data = tenants_response.data if tenants_response.data else []
        
        # Calculate stats
        stats = {
            'total_tenants': len(tenants_data),
            'active_tenants': sum(1 for t in tenants_data if t.get('status') == TenantStatus.ACTIVE.value),
            'monthly_revenue': 0,  # Will calculate below
            'active_users': 0,     # Will calculate below
            'avg_response_time': 45  # Sample data
        }
        
        # Get tenant metrics for revenue calculation
        now = datetime.utcnow()
        current_month_start = datetime(now.year, now.month, 1)
        
        # Get current month revenue
        metrics_response = supabase.table('tenant_metrics')\
            .select('revenue_generated')\
            .gte('date', current_month_start.isoformat())\
            .execute()
        
        stats['monthly_revenue'] = sum(float(m.get('revenue_generated', 0)) for m in metrics_response.data) if metrics_response.data else 0
        
        # Get active users count (in a real implementation, this would be from a users table)
        # For now, we'll use sample data
        stats['active_users'] = stats['active_tenants'] * 15  # Assuming average 15 users per tenant
        
        # System health data
        system_health = {
            'cpu_usage': 32,
            'memory_usage': 45,
            'disk_usage': 28,
            'db_connections': 15,
            'services': [
                {'name': 'Web Server', 'status': 'Healthy', 'status_class': 'bg-green-100 text-green-800'},
                {'name': 'Database', 'status': 'Healthy', 'status_class': 'bg-green-100 text-green-800'},
                {'name': 'Background Workers', 'status': 'Warning', 'status_class': 'bg-yellow-100 text-yellow-800'},
                {'name': 'Email Service', 'status': 'Healthy', 'status_class': 'bg-green-100 text-green-800'}
            ]
        }
        
        # Recent activity from audit logs
        audit_response = supabase.table('global_audit_logs')\
            .select('*')\
            .order('created_at', desc=True)\
            .limit(5)\
            .execute()
        
        recent_activity = []
        if audit_response.data:
            for log in audit_response.data:
                # Get superadmin info if available
                superadmin_info = None
                if log.get('superadmin_id'):
                    superadmin_response = supabase.table('superadmins')\
                        .select('username, full_name')\
                        .eq('id', log.get('superadmin_id'))\
                        .execute()
                    if superadmin_response.data and len(superadmin_response.data) > 0:
                        superadmin_info = superadmin_response.data[0]
                
                recent_activity.append({
                    'id': log.get('id'),
                    'action': log.get('action'),
                    'resource_type': log.get('resource_type'),
                    'description': log.get('description'),
                    'timestamp': datetime.fromisoformat(log.get('created_at')).strftime('%Y-%m-%d %H:%M:%S') if log.get('created_at') else '',
                    'user': superadmin_info.get('full_name') if superadmin_info else 'Unknown'
                })
        
        # Chart data
        # In a real implementation, these would be actual data from the database
        # For now, we'll create sample data
        
        # Tenant growth over last 12 months
        tenant_growth = {
            'labels': [(now - timedelta(days=30*i)).strftime('%b %Y') for i in range(11, -1, -1)],
            'values': [5, 7, 10, 8, 12, 15, 18, 14, 20, 25, 30, 28]  # Sample data
        }
        
        # Revenue trend over last 12 months
        revenue_trend = {
            'labels': [(now - timedelta(days=30*i)).strftime('%b %Y') for i in range(11, -1, -1)],
            'values': [1200, 1500, 1800, 2200, 2500, 3000, 3200, 3500, 4000, 4200, 4500, 5000]  # Sample data
        }
        
        # Tenant distribution by status
        tenant_distribution = {
            'labels': ['Active', 'Trial', 'Expired', 'Canceled'],
            'values': [
                sum(1 for t in tenants_data if t.get('status') == TenantStatus.ACTIVE.value and not (t.get('subscription_end') and datetime.utcnow() < datetime.fromisoformat(t.get('subscription_end')))),
                sum(1 for t in tenants_data if t.get('status') == TenantStatus.ACTIVE.value and t.get('subscription_end') and datetime.utcnow() < datetime.fromisoformat(t.get('subscription_end'))),
                sum(1 for t in tenants_data if t.get('subscription_end') and datetime.utcnow() > datetime.fromisoformat(t.get('subscription_end'))),
                sum(1 for t in tenants_data if t.get('status') == TenantStatus.DELETED.value)
            ]
        }
        
        # Subscription tiers
        subscription_tiers = {
            'labels': ['Free', 'Basic', 'Premium', 'Enterprise'],
            'values': [
                sum(1 for t in tenants_data if t.get('subscription_tier') == SubscriptionTier.FREE.value),
                sum(1 for t in tenants_data if t.get('subscription_tier') == SubscriptionTier.BASIC.value),
                sum(1 for t in tenants_data if t.get('subscription_tier') == SubscriptionTier.PREMIUM.value),
                sum(1 for t in tenants_data if t.get('subscription_tier') == SubscriptionTier.ENTERPRISE.value)
            ]
        }
        
        return render_template('superadmin/dashboard.html',
                              stats=stats,
                              system_health=system_health,
                              recent_activity=recent_activity,
                              tenant_growth=tenant_growth,
                              revenue_trend=revenue_trend,
                              tenant_distribution=tenant_distribution,
                              subscription_tiers=subscription_tiers)
                              
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        flash(f"Error loading dashboard: {str(e)}", 'error')
        return render_template('superadmin/dashboard.html')

@superadmin_bp.route('/tenants')
@superadmin_required
def tenants():
    return render_template('superadmin/tenants.html')

@superadmin_bp.route('/billing-overview')
@superadmin_required
@log_superadmin_action('view', 'billing_overview')
def billing_overview():
    """Display system-wide billing overview"""
    try:
        supabase = get_superadmin_client()
        
        # Get all tenants with subscription information
        tenants_response = supabase.table('tenants').select('*').execute()
        tenants_data = tenants_response.data if tenants_response.data else []
        
        # Calculate billing statistics
        stats = {
            'total_tenants': len(tenants_data),
            'active_tenants': sum(1 for t in tenants_data if t.get('status') == TenantStatus.ACTIVE.value),
            'trial_tenants': sum(1 for t in tenants_data if t.get('status') == TenantStatus.ACTIVE.value and t.get('subscription_end') and datetime.utcnow() < datetime.fromisoformat(t.get('subscription_end'))),
            'expired_tenants': sum(1 for t in tenants_data if t.get('subscription_end') and datetime.utcnow() > datetime.fromisoformat(t.get('subscription_end'))),
            'canceled_tenants': sum(1 for t in tenants_data if t.get('status') == TenantStatus.DELETED.value),
            'free_tenants': sum(1 for t in tenants_data if t.get('subscription_tier') == SubscriptionTier.FREE.value),
            'premium_tenants': sum(1 for t in tenants_data if t.get('subscription_tier') == SubscriptionTier.PREMIUM.value),
            'enterprise_tenants': sum(1 for t in tenants_data if t.get('subscription_tier') == SubscriptionTier.ENTERPRISE.value),
            'expiring_trials': 0,  # Will calculate below
            'monthly_revenue': 0,  # Will calculate below
            'revenue_change': 0    # Will calculate below
        }
        
        # Calculate expiring trials (trials ending in next 7 days)
        now = datetime.utcnow()
        seven_days_later = now + timedelta(days=7)
        stats['expiring_trials'] = sum(1 for t in tenants_data 
                                     if t.get('status') == TenantStatus.ACTIVE.value 
                                     and t.get('subscription_end') 
                                     and now < datetime.fromisoformat(t.get('subscription_end')) < seven_days_later)
        
        # Get tenant metrics for revenue calculation
        current_month_start = datetime(now.year, now.month, 1)
        last_month_start = current_month_start - timedelta(days=1)
        last_month_start = datetime(last_month_start.year, last_month_start.month, 1)
        
        # Get current month revenue
        metrics_response = supabase.table('tenant_metrics')\
            .select('revenue_generated')\
            .gte('date', current_month_start.isoformat())\
            .execute()
        
        current_month_revenue = sum(float(m.get('revenue_generated', 0)) for m in metrics_response.data) if metrics_response.data else 0
        
        # Get last month revenue
        last_metrics_response = supabase.table('tenant_metrics')\
            .select('revenue_generated')\
            .gte('date', last_month_start.isoformat())\
            .lt('date', current_month_start.isoformat())\
            .execute()
        
        last_month_revenue = sum(float(m.get('revenue_generated', 0)) for m in last_metrics_response.data) if last_metrics_response.data else 0
        
        # Calculate revenue change percentage
        stats['monthly_revenue'] = current_month_revenue
        if last_month_revenue > 0:
            stats['revenue_change'] = round(((current_month_revenue - last_month_revenue) / last_month_revenue) * 100, 1)
        
        # Get recent invoices
        # In a real implementation, this would fetch from an invoices table
        # For now, we'll create sample data
        recent_invoices = [
            {
                'id': 1,
                'invoice_number': 'INV-2023-001',
                'tenant_name': 'Acme School',
                'date': datetime.utcnow() - timedelta(days=2),
                'amount': 49.99,
                'status': 'Paid',
                'status_class': 'bg-green-100 text-green-800'
            },
            {
                'id': 2,
                'invoice_number': 'INV-2023-002',
                'tenant_name': 'Springfield Elementary',
                'date': datetime.utcnow() - timedelta(days=5),
                'amount': 99.99,
                'status': 'Paid',
                'status_class': 'bg-green-100 text-green-800'
            },
            {
                'id': 3,
                'invoice_number': 'INV-2023-003',
                'tenant_name': 'Riverdale High',
                'date': datetime.utcnow() - timedelta(days=10),
                'amount': 149.99,
                'status': 'Pending',
                'status_class': 'bg-yellow-100 text-yellow-800'
            }
        ]
        
        # Prepare tenant data for display
        tenants = []
        for t in tenants_data:
            # Determine status class
            status_class = ''
            if t.get('status') == TenantStatus.ACTIVE.value:
                status_class = 'status-active'
            elif t.get('status') == TenantStatus.PENDING.value:
                status_class = 'status-trial'
            elif t.get('status') == TenantStatus.SUSPENDED.value:
                status_class = 'status-expired'
            elif t.get('status') == TenantStatus.DELETED.value:
                status_class = 'status-canceled'
            
            # Determine tier class
            tier_class = ''
            if t.get('subscription_tier') == SubscriptionTier.FREE.value:
                tier_class = 'tier-free'
            elif t.get('subscription_tier') == SubscriptionTier.BASIC.value:
                tier_class = 'tier-basic'
            elif t.get('subscription_tier') == SubscriptionTier.PREMIUM.value:
                tier_class = 'tier-premium'
            elif t.get('subscription_tier') == SubscriptionTier.ENTERPRISE.value:
                tier_class = 'tier-enterprise'
            
            # Calculate monthly fee based on tier
            monthly_fee = 0
            if t.get('subscription_tier') == SubscriptionTier.BASIC.value:
                monthly_fee = 29.99
            elif t.get('subscription_tier') == SubscriptionTier.PREMIUM.value:
                monthly_fee = 99.99
            elif t.get('subscription_tier') == SubscriptionTier.ENTERPRISE.value:
                monthly_fee = 299.99
            
            # Determine next billing date
            next_billing_date = None
            if t.get('subscription_end'):
                next_billing_date = datetime.fromisoformat(t.get('subscription_end'))
            
            tenants.append({
                'id': t.get('id'),
                'name': t.get('organization_name'),
                'email': t.get('admin_email'),
                'subscription_tier': t.get('subscription_tier'),
                'subscription_status': t.get('status'),
                'monthly_fee': monthly_fee,
                'next_billing_date': next_billing_date,
                'status_class': status_class,
                'tier_class': tier_class
            })
        
        # Generate revenue chart data
        # In a real implementation, this would be actual data from the database
        # For now, we'll create sample data
        now = datetime.utcnow()
        revenue_data = {
            'labels': [(now - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30, 0, -1)],
            'values': [round(float(50 + i * 2.5 + (i % 5) * 10), 2) for i in range(30)]
        }
        
        return render_template('superadmin/billing_overview.html',
                              stats=stats,
                              recent_invoices=recent_invoices,
                              tenants=tenants,
                              revenue_data=revenue_data)
                              
    except Exception as e:
        logger.error(f"Error fetching billing overview: {str(e)}")
        flash(f"Error fetching billing overview: {str(e)}", 'error')
        return render_template('superadmin/billing_overview.html', 
                              stats={},
                              recent_invoices=[],
                              tenants=[],
                              revenue_data={'labels': [], 'values': []})

@superadmin_bp.route('/api/revenue-data')
@superadmin_required
def get_revenue_data():
    """API endpoint to get revenue data for charts"""
    try:
        period = request.args.get('period', '30')
        period = int(period)
        
        # In a real implementation, this would fetch actual data from the database
        # For now, we'll create sample data
        now = datetime.utcnow()
        revenue_data = {
            'labels': [(now - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(period, 0, -1)],
            'values': [round(float(50 + i * 2.5 + (i % 5) * 10), 2) for i in range(period)]
        }
        
        return jsonify(revenue_data)
        
    except Exception as e:
        logger.error(f"Error fetching revenue data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@superadmin_bp.route('/system-health')
@superadmin_required
@log_superadmin_action('view', 'system_health')
def system_health():
    """Display system health monitoring page"""
    try:
        # In a real implementation, these would be fetched from monitoring services
        # For now, we'll create sample data
        
        # System status overview
        system_status = "Healthy"
        uptime = "15 days, 7 hours"
        cpu_usage = 32
        active_alerts = 2
        
        # Resource usage charts data
        now = datetime.utcnow()
        hours = [now - timedelta(hours=i) for i in range(24, 0, -1)]
        
        cpu_chart_data = {
            'labels': [h.strftime('%H:%M') for h in hours],
            'values': [round(20 + 15 * (i % 3) + (i % 5) * 2) for i in range(24)]
        }
        
        memory_chart_data = {
            'labels': [h.strftime('%H:%M') for h in hours],
            'values': [round(40 + 10 * (i % 4) + (i % 6) * 3) for i in range(24)]
        }
        
        disk_usage = {
            'used': 256,  # GB
            'free': 744   # GB
        }
        
        # Service status
        services = [
            {
                'name': 'Web Server',
                'status': 'Healthy',
                'status_class': 'status-healthy',
                'uptime': '15 days, 7 hours',
                'last_check': (now - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'name': 'Database',
                'status': 'Healthy',
                'status_class': 'status-healthy',
                'uptime': '15 days, 7 hours',
                'last_check': (now - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'name': 'Cache',
                'status': 'Healthy',
                'status_class': 'status-healthy',
                'uptime': '10 days, 3 hours',
                'last_check': (now - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'name': 'Background Workers',
                'status': 'Warning',
                'status_class': 'status-warning',
                'uptime': '5 days, 12 hours',
                'last_check': (now - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'name': 'Email Service',
                'status': 'Healthy',
                'status_class': 'status-healthy',
                'uptime': '15 days, 7 hours',
                'last_check': (now - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'name': 'Storage Service',
                'status': 'Healthy',
                'status_class': 'status-healthy',
                'uptime': '15 days, 7 hours',
                'last_check': (now - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
        
        # Recent errors
        recent_errors = [
            {
                'id': 'ERR-001',
                'timestamp': (now - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
                'service': 'Background Workers',
                'type': 'Connection Error',
                'message': 'Failed to connect to message queue after 3 retries'
            },
            {
                'id': 'ERR-002',
                'timestamp': (now - timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S'),
                'service': 'Email Service',
                'type': 'Timeout',
                'message': 'SMTP connection timeout after 30 seconds'
            }
        ]
        
        # Database stats
        db_stats = {
            'connection_pool_status': 'Healthy',
            'active_connections': 12,
            'max_connections': 100,
            'size': '4.2 GB',
            'last_backup': (now - timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S'),
            'replication_status': 'Synchronized'
        }
        
        # Query performance data
        query_performance = {
            'labels': ['Auth', 'User', 'Tenant', 'Billing', 'Reports'],
            'values': [15, 22, 18, 35, 42]
        }
        
        return render_template('superadmin/system_health.html',
                              system_status=system_status,
                              uptime=uptime,
                              cpu_usage=cpu_usage,
                              active_alerts=active_alerts,
                              cpu_chart_data=cpu_chart_data,
                              memory_chart_data=memory_chart_data,
                              disk_usage=disk_usage,
                              services=services,
                              recent_errors=recent_errors,
                              db_stats=db_stats,
                              query_performance=query_performance)
                              
    except Exception as e:
        logger.error(f"Error fetching system health data: {str(e)}")
        flash(f"Error fetching system health data: {str(e)}", 'error')
        return render_template('superadmin/system_health.html')

@superadmin_bp.route('/audit-logs')
@superadmin_required
@log_superadmin_action('view', 'audit_logs')
def audit_logs():
    """Display system-wide audit logs"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Get filter parameters
    action = request.args.get('action')
    resource_type = request.args.get('resource_type')
    severity = request.args.get('severity')
    date_range = request.args.get('date_range')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        supabase = get_superadmin_client()
        query = supabase.table('global_audit_logs').select('*')
        
        # Apply filters
        if action:
            query = query.eq('action', action.lower())
        
        if resource_type:
            query = query.eq('resource_type', resource_type.lower())
            
        if severity:
            query = query.eq('severity', severity.lower())
            
        # Date filtering
        if date_range:
            now = datetime.utcnow()
            if date_range == 'today':
                start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.gte('created_at', start.isoformat())
            elif date_range == 'yesterday':
                start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                end = now.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.gte('created_at', start.isoformat()).lt('created_at', end.isoformat())
            elif date_range == 'last7days':
                start = (now - timedelta(days=7))
                query = query.gte('created_at', start.isoformat())
            elif date_range == 'last30days':
                start = (now - timedelta(days=30))
                query = query.gte('created_at', start.isoformat())
            elif date_range == 'thismonth':
                start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                query = query.gte('created_at', start.isoformat())
            elif date_range == 'lastmonth':
                last_month = now.month - 1 if now.month > 1 else 12
                last_month_year = now.year if now.month > 1 else now.year - 1
                start = datetime(last_month_year, last_month, 1)
                end = datetime(now.year, now.month, 1)
                query = query.gte('created_at', start.isoformat()).lt('created_at', end.isoformat())
        elif start_date and end_date:
            # Custom date range
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Include the end date
                query = query.gte('created_at', start.isoformat()).lt('created_at', end.isoformat())
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
        
        # Order by most recent first
        query = query.order('created_at', desc=True)
        
        # Handle export request
        if request.args.get('export') == 'csv':
            # Get all logs for export (limit to reasonable number)
            export_limit = 1000
            response = query.limit(export_limit).execute()
            
            if response.data:
                # Generate CSV
                import csv
                from io import StringIO
                from flask import Response
                
                output = StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow(['Timestamp', 'User', 'Action', 'Resource Type', 'Resource ID', 
                                'Severity', 'IP Address', 'Description'])
                
                # Write data
                for log in response.data:
                    writer.writerow([
                        log.get('created_at'),
                        log.get('superadmin_id', 'System'),
                        log.get('action'),
                        log.get('resource_type'),
                        log.get('resource_id', ''),
                        log.get('severity'),
                        log.get('ip_address'),
                        log.get('description')
                    ])
                
                # Create response
                output.seek(0)
                return Response(
                    output.getvalue(),
                    mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment;filename=audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
                )
            else:
                flash('No data to export.', 'warning')
        
        # Pagination for display
        total_count_response = query.count().execute()
        total_count = total_count_response.count if hasattr(total_count_response, 'count') else 0
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get paginated results
        response = query.range(offset, offset + per_page - 1).execute()
        
        # Create a pagination object
        class Pagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                
            @property
            def pages(self):
                return max(1, (self.total + self.per_page - 1) // self.per_page)
                
            @property
            def has_prev(self):
                return self.page > 1
                
            @property
            def has_next(self):
                return self.page < self.pages
                
            @property
            def prev_num(self):
                return self.page - 1 if self.has_prev else None
                
            @property
            def next_num(self):
                return self.page + 1 if self.has_next else None
                
            @property
            def first_item(self):
                return (self.page - 1) * self.per_page + 1 if self.items else 0
                
            @property
            def last_item(self):
                return min(self.page * self.per_page, self.total)
                
            def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
                last = 0
                for num in range(1, self.pages + 1):
                    if num <= left_edge or \
                       (num > self.page - left_current - 1 and num < self.page + right_current) or \
                       num > self.pages - right_edge:
                        if last + 1 != num:
                            yield None
                        yield num
                        last = num
        
        logs = Pagination(response.data, page, per_page, total_count)
        
        # Helper functions for template
        def action_class(action):
            action = action.lower() if action else ''
            if action in ['create', 'add']:
                return 'action-create'
            elif action in ['update', 'modify']:
                return 'action-update'
            elif action in ['delete', 'remove']:
                return 'action-delete'
            elif action == 'login':
                return 'action-login'
            else:
                return 'action-other'
                
        def severity_class(severity):
            severity = severity.lower() if severity else ''
            if severity == 'info':
                return 'severity-info'
            elif severity == 'warning':
                return 'severity-warning'
            elif severity == 'error':
                return 'severity-error'
            else:
                return ''
        
        return render_template('superadmin/audit_logs.html', 
                              logs=logs,
                              action_class=action_class,
                              severity_class=severity_class)
                              
    except Exception as e:
        logger.error(f"Error fetching audit logs: {str(e)}")
        flash(f"Error fetching audit logs: {str(e)}", 'error')
        return render_template('superadmin/audit_logs.html', logs=[])

@superadmin_bp.route('/audit-log/<log_id>')
@superadmin_required
def get_audit_log_details(log_id):
    """Get detailed information for a specific audit log entry"""
    try:
        supabase = get_superadmin_client()
        response = supabase.table('global_audit_logs').select('*').eq('id', log_id).execute()
        
        if response.data and len(response.data) > 0:
            log_data = response.data[0]
            
            # Get superadmin info if available
            superadmin_info = None
            if log_data.get('superadmin_id'):
                superadmin_response = supabase.table('superadmins').select('username').eq('id', log_data['superadmin_id']).execute()
                if superadmin_response.data and len(superadmin_response.data) > 0:
                    superadmin_info = superadmin_response.data[0]['username']
            
            # Format response
            result = {
                'id': log_data.get('id'),
                'created_at': log_data.get('created_at'),
                'user': superadmin_info,
                'action': log_data.get('action'),
                'resource_type': log_data.get('resource_type'),
                'resource_id': log_data.get('resource_id'),
                'description': log_data.get('description'),
                'ip_address': log_data.get('ip_address'),
                'user_agent': log_data.get('user_agent'),
                'endpoint': log_data.get('endpoint'),
                'method': log_data.get('method'),
                'severity': log_data.get('severity'),
                'old_values': log_data.get('old_values'),
                'new_values': log_data.get('new_values')
            }
            
            return jsonify(result)
        else:
            return jsonify({'error': 'Log entry not found'}), 404
            
    except Exception as e:
        logger.error(f"Error fetching audit log details: {str(e)}")
        return jsonify({'error': str(e)}), 500


# routes/billing_routes.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, g, send_file
from auth.decorators import login_required, admin_required
from services.billing_service import BillingService
from datetime import datetime
import io

billing_bp = Blueprint('billing', __name__, url_prefix='/billing')
billing_service = BillingService()

@billing_bp.route('/invoices')
@login_required
@admin_required
def invoices():
    """View organization invoices"""
    # This would typically fetch invoices from a database
    # For now, we'll just render a template that allows generating invoices
    return render_template('admin/invoices.html')

@billing_bp.route('/generate-invoice', methods=['POST'])
@login_required
@admin_required
def generate_invoice():
    """Generate a new invoice"""
    try:
        # Get billing period from form if provided
        billing_period = None
        if request.form.get('start_date') and request.form.get('end_date'):
            try:
                start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
                end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
                billing_period = {
                    'start_date': start_date,
                    'end_date': end_date
                }
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD format.', 'error')
                return redirect(url_for('billing.invoices'))
        
        # Generate invoice
        result = billing_service.generate_invoice(g.organization_id, billing_period)
        
        if not result.get('success'):
            flash(f"Failed to generate invoice: {result.get('message')}", 'error')
            return redirect(url_for('billing.invoices'))
        
        # Store invoice data in session for download
        from flask import session
        session['last_invoice'] = {
            'invoice_number': result['invoice_data']['invoice_number'],
            'issue_date': result['invoice_data']['issue_date']
        }
        
        # If send_email parameter is provided, send invoice by email
        if request.form.get('send_email') == 'true':
            email_result = billing_service.send_invoice_email(
                g.organization_id, 
                result['invoice_data'],
                result['pdf_buffer']
            )
            
            if email_result.get('success'):
                flash('Invoice generated and sent by email successfully!', 'success')
            else:
                flash(f"Invoice generated but email failed: {email_result.get('message')}", 'warning')
        else:
            flash('Invoice generated successfully!', 'success')
        
        # Redirect to download route
        return redirect(url_for('billing.download_invoice', invoice_number=result['invoice_data']['invoice_number']))
        
    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'error')
        return redirect(url_for('billing.invoices'))

@billing_bp.route('/download-invoice/<invoice_number>')
@login_required
@admin_required
def download_invoice(invoice_number):
    """Download a generated invoice"""
    try:
        # In a real implementation, we would fetch the invoice from storage
        # For now, we'll regenerate it
        result = billing_service.generate_invoice(g.organization_id)
        
        if not result.get('success'):
            flash(f"Failed to generate invoice: {result.get('message')}", 'error')
            return redirect(url_for('billing.invoices'))
        
        # Send PDF file
        buffer = result['pdf_buffer']
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"Invoice_{invoice_number}.pdf"
        )
        
    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'error')
        return redirect(url_for('billing.invoices'))

# Superadmin routes for billing management
@billing_bp.route('/admin/overview')
@login_required
def admin_billing_overview():
    """Superadmin billing overview"""
    # Check if user is superadmin
    if g.user.role != 'super_admin':
        flash('Access denied. Superadmin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    # In a real implementation, we would fetch billing data for all organizations
    # For now, we'll just render a template
    return render_template('superadmin/billing_overview.html')
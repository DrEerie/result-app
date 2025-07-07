# services/billing_service.py
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
import io
from flask import current_app, g
from sqlalchemy.orm import Session

from models.base import db
from auth.models import Subscription
from models.organization import Organization
from services.base_service import BaseService
from services.pdf_service import BasePDFService
from utils.error_handlers import ResourceNotFoundError, BusinessLogicError, audit_log

class BillingService(BaseService):
    """Service for billing and invoice operations"""
    
    def __init__(self, db_session: Session = None):
        super().__init__(db_session or db.session)
        self.pdf_service = InvoicePDFService()
    
    @audit_log("generate_invoice", "subscription")
    def generate_invoice(self, organization_id: str, billing_period: Optional[Dict[str, datetime]] = None) -> Dict[str, Any]:
        """Generate invoice for an organization"""
        try:
            # Get organization and subscription
            organization = self.db.query(Organization).filter_by(id=organization_id).first()
            if not organization:
                return {
                    'success': False,
                    'error': 'organization_not_found',
                    'message': 'Organization not found'
                }
            
            subscription = organization.subscription
            if not subscription:
                return {
                    'success': False,
                    'error': 'subscription_not_found',
                    'message': 'No active subscription found for this organization'
                }
            
            # Determine billing period if not provided
            if not billing_period:
                today = datetime.utcnow().date()
                
                # Default to current month
                start_date = datetime(today.year, today.month, 1)
                if today.month == 12:
                    end_date = datetime(today.year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = datetime(today.year, today.month + 1, 1) - timedelta(days=1)
                
                billing_period = {
                    'start_date': start_date,
                    'end_date': end_date
                }
            
            # Generate invoice data
            invoice_data = {
                'invoice_number': f"INV-{uuid.uuid4().hex[:8].upper()}",
                'organization': {
                    'id': str(organization.id),
                    'name': organization.name,
                    'email': organization.email,
                    'address': organization.address or 'N/A',
                    'phone': organization.phone or 'N/A'
                },
                'subscription': {
                    'id': str(subscription.id),
                    'tier': subscription.tier,
                    'billing_cycle': subscription.billing_cycle,
                    'amount': float(subscription.amount),
                    'currency': subscription.currency
                },
                'billing_period': {
                    'start_date': billing_period['start_date'].strftime('%Y-%m-%d'),
                    'end_date': billing_period['end_date'].strftime('%Y-%m-%d')
                },
                'issue_date': datetime.utcnow().strftime('%Y-%m-%d'),
                'due_date': (datetime.utcnow() + timedelta(days=15)).strftime('%Y-%m-%d'),
                'items': [
                    {
                        'description': f"{subscription.tier.capitalize()} Plan Subscription",
                        'quantity': 1,
                        'unit_price': float(subscription.amount),
                        'total': float(subscription.amount)
                    }
                ],
                'subtotal': float(subscription.amount),
                'tax': 0.0,  # Can be calculated based on tax rules
                'total': float(subscription.amount)
            }
            
            # Generate PDF invoice
            pdf_buffer = self.pdf_service.generate_invoice(invoice_data)
            
            return {
                'success': True,
                'invoice_data': invoice_data,
                'pdf_buffer': pdf_buffer
            }
            
        except Exception as e:
            self.logger.error(f"Error generating invoice: {str(e)}")
            return self._handle_db_error(e, "generate_invoice")
    
    def send_invoice_email(self, organization_id: str, invoice_data: Dict[str, Any], pdf_buffer: io.BytesIO) -> Dict[str, Any]:
        """Send invoice email to organization"""
        try:
            from services.email_service import send_email
            
            organization = self.db.query(Organization).filter_by(id=organization_id).first()
            if not organization:
                return {
                    'success': False,
                    'error': 'organization_not_found',
                    'message': 'Organization not found'
                }
            
            # Prepare email data
            email_data = {
                'to': organization.email,
                'subject': f"Invoice #{invoice_data['invoice_number']} for {organization.name}",
                'template': 'emails/invoice.html',
                'context': {
                    'organization': organization,
                    'invoice': invoice_data
                },
                'attachments': [
                    {
                        'filename': f"Invoice_{invoice_data['invoice_number']}.pdf",
                        'content': pdf_buffer.getvalue(),
                        'content_type': 'application/pdf'
                    }
                ]
            }
            
            # Send email
            email_result = send_email(**email_data)
            
            return {
                'success': True,
                'message': 'Invoice email sent successfully',
                'email_result': email_result
            }
            
        except Exception as e:
            self.logger.error(f"Error sending invoice email: {str(e)}")
            return {
                'success': False,
                'error': 'email_error',
                'message': f"Failed to send invoice email: {str(e)}"
            }

class InvoicePDFService(BasePDFService):
    """Service for generating invoice PDFs"""
    
    def generate_invoice(self, invoice_data: Dict[str, Any]) -> io.BytesIO:
        """Generate invoice PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize='A4', 
                               topMargin=0.5*inch, bottomMargin=0.5*inch,
                               leftMargin=0.5*inch, rightMargin=0.5*inch)
        
        # Build invoice content
        story = self._build_invoice(invoice_data)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _build_invoice(self, invoice_data: Dict[str, Any]) -> List:
        """Build invoice content"""
        elements = []
        
        # Add header
        elements.extend(self._create_invoice_header(invoice_data))
        elements.append(Spacer(1, 20))
        
        # Add invoice details
        elements.extend(self._create_invoice_details(invoice_data))
        elements.append(Spacer(1, 20))
        
        # Add items table
        elements.extend(self._create_invoice_items(invoice_data))
        elements.append(Spacer(1, 20))
        
        # Add totals
        elements.extend(self._create_invoice_totals(invoice_data))
        elements.append(Spacer(1, 20))
        
        # Add footer
        elements.extend(self._create_invoice_footer(invoice_data))
        
        return elements
    
    def _create_invoice_header(self, invoice_data: Dict[str, Any]) -> List:
        """Create invoice header"""
        elements = []
        
        # Create header with logo and company info
        header_data = []
        
        # Logo placeholder
        logo_cell = ""
        try:
            # Use app logo if available
            logo_path = current_app.config.get('COMPANY_LOGO')
            if logo_path:
                logo_img = Image(logo_path, width=1.5*inch, height=1.5*inch)
                logo_cell = logo_img
        except Exception:
            self.logger.warning("Failed to load company logo")
        
        # Company info
        company_name = current_app.config.get('COMPANY_NAME', 'EduResult')
        company_info = [
            [Paragraph(f"<b>{company_name}</b>", self.styles['CustomHeader'])],
            [Paragraph(current_app.config.get('COMPANY_ADDRESS', ''), self.styles['Normal'])],
            [Paragraph(current_app.config.get('COMPANY_EMAIL', ''), self.styles['Normal'])],
            [Paragraph(current_app.config.get('COMPANY_PHONE', ''), self.styles['Normal'])]
        ]
        
        # Invoice title
        invoice_title = [
            [Paragraph("<b>INVOICE</b>", self.styles['CustomHeader'])],
            [Paragraph(f"Invoice #: {invoice_data['invoice_number']}", self.styles['Normal'])],
            [Paragraph(f"Date: {invoice_data['issue_date']}", self.styles['Normal'])],
            [Paragraph(f"Due Date: {invoice_data['due_date']}", self.styles['Normal'])]
        ]
        
        header_table = Table([[logo_cell, company_info, invoice_title]], colWidths=[1.5*inch, 3*inch, 2*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(header_table)
        return elements
    
    def _create_invoice_details(self, invoice_data: Dict[str, Any]) -> List:
        """Create invoice details section"""
        elements = []
        
        # Bill to section
        elements.append(Paragraph("<b>Bill To:</b>", self.styles['Normal']))
        elements.append(Paragraph(invoice_data['organization']['name'], self.styles['Normal']))
        if invoice_data['organization']['address']:
            elements.append(Paragraph(invoice_data['organization']['address'], self.styles['Normal']))
        elements.append(Paragraph(f"Email: {invoice_data['organization']['email']}", self.styles['Normal']))
        if invoice_data['organization']['phone']:
            elements.append(Paragraph(f"Phone: {invoice_data['organization']['phone']}", self.styles['Normal']))
        
        elements.append(Spacer(1, 10))
        
        # Billing period
        elements.append(Paragraph(f"<b>Billing Period:</b> {invoice_data['billing_period']['start_date']} to {invoice_data['billing_period']['end_date']}", self.styles['Normal']))
        elements.append(Paragraph(f"<b>Subscription:</b> {invoice_data['subscription']['tier'].capitalize()} Plan ({invoice_data['subscription']['billing_cycle']})", self.styles['Normal']))
        
        return elements
    
    def _create_invoice_items(self, invoice_data: Dict[str, Any]) -> List:
        """Create invoice items table"""
        elements = []
        
        # Table header
        items_data = [['Description', 'Quantity', 'Unit Price', 'Total']]
        
        # Add items
        for item in invoice_data['items']:
            items_data.append([
                item['description'],
                str(item['quantity']),
                f"{item['unit_price']:.2f} {invoice_data['subscription']['currency']}",
                f"{item['total']:.2f} {invoice_data['subscription']['currency']}"
            ])
        
        # Create table
        items_table = Table(items_data, colWidths=[4*inch, 1*inch, 1.5*inch, 1.5*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(items_table)
        return elements
    
    def _create_invoice_totals(self, invoice_data: Dict[str, Any]) -> List:
        """Create invoice totals section"""
        elements = []
        
        # Totals table
        totals_data = [
            ['Subtotal:', f"{invoice_data['subtotal']:.2f} {invoice_data['subscription']['currency']}"],
            ['Tax:', f"{invoice_data['tax']:.2f} {invoice_data['subscription']['currency']}"],
            ['Total:', f"{invoice_data['total']:.2f} {invoice_data['subscription']['currency']}"]
        ]
        
        totals_table = Table(totals_data, colWidths=[6*inch, 2*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(totals_table)
        return elements
    
    def _create_invoice_footer(self, invoice_data: Dict[str, Any]) -> List:
        """Create invoice footer"""
        elements = []
        
        # Payment instructions
        elements.append(Paragraph("<b>Payment Instructions:</b>", self.styles['Normal']))
        elements.append(Paragraph("Please make payment by the due date to avoid service interruption.", self.styles['Normal']))
        
        # Payment methods
        payment_methods = current_app.config.get('PAYMENT_METHODS', [])
        if payment_methods:
            elements.append(Paragraph("<b>Payment Methods:</b>", self.styles['Normal']))
            for method in payment_methods:
                elements.append(Paragraph(f"- {method}", self.styles['Normal']))
        
        # Thank you note
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Thank you for your business!", self.styles['Normal']))
        
        # Generated timestamp
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(
            f"Generated on: {datetime.utcnow().strftime('%B %d, %Y %H:%M:%S UTC')}",
            self.styles['Normal']
        ))
        
        return elements
# services/email_service.py
import resend
import base64
from typing import Dict, Any, List, Optional
from flask import current_app, render_template
import logging

logger = logging.getLogger(__name__)

def init_email_service(app):
    """Initialize email service with app config"""
    resend_api_key = app.config.get('RESEND_API_KEY')
    if not resend_api_key:
        logger.warning("RESEND_API_KEY not configured. Email functionality will not work.")
        return
    
    resend.api_key = resend_api_key
    logger.info("Email service initialized with Resend")

def send_email(to: str, subject: str, template: Optional[str] = None, 
               html: Optional[str] = None, context: Dict[str, Any] = None,
               attachments: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Send email using Resend
    
    Args:
        to: Recipient email address
        subject: Email subject
        template: Template path (relative to templates folder)
        html: HTML content (used if template not provided)
        context: Template context variables
        attachments: List of attachments with filename, content, and content_type
    
    Returns:
        Dict with success status and message
    """
    try:
        # Validate required parameters
        if not to or not subject:
            return {
                'success': False,
                'error': 'missing_parameters',
                'message': 'Recipient email and subject are required'
            }
        
        # Get HTML content from template or direct HTML
        email_html = html
        if template and not html:
            try:
                # Add current_app.config to context
                context = context or {}
                context['config'] = current_app.config
                context['now'] = datetime.utcnow()
                
                email_html = render_template(template, **context)
            except Exception as e:
                logger.error(f"Failed to render email template {template}: {str(e)}")
                return {
                    'success': False,
                    'error': 'template_error',
                    'message': f"Failed to render email template: {str(e)}"
                }
        
        if not email_html:
            return {
                'success': False,
                'error': 'missing_content',
                'message': 'Email content is required'
            }
        
        # Prepare email data
        email_data = {
            "from": current_app.config.get('EMAIL_FROM', 'noreply@eduresult.com'),
            "to": to,
            "subject": subject,
            "html": email_html
        }
        
        # Add attachments if provided
        if attachments:
            email_data["attachments"] = []
            for attachment in attachments:
                # Convert binary content to base64 if needed
                content = attachment['content']
                if isinstance(content, bytes):
                    content = base64.b64encode(content).decode('utf-8')
                
                email_data["attachments"].append({
                    "filename": attachment['filename'],
                    "content": content,
                    "content_type": attachment.get('content_type', 'application/octet-stream')
                })
        
        # Send email
        response = resend.Emails.send(email_data)
        
        return {
            'success': True,
            'message': 'Email sent successfully',
            'response': response
        }
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return {
            'success': False,
            'error': 'email_error',
            'message': f"Failed to send email: {str(e)}"
        }

# Import datetime here to avoid circular import in the function
from datetime import datetime

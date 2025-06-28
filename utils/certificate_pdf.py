"""
Certificate PDF generation service
"""
from typing import Dict, Any, List
from io import BytesIO
from datetime import datetime
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, SimpleDocTemplate, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.graphics.shapes import Drawing
from reportlab.lib.styles import ParagraphStyle
from services.pdf_service import BasePDFService

class CertificatePDFService(BasePDFService):
    """Service for generating certificates"""
    
    def generate_certificate(self, certificate_data: Dict[str, Any], organization_data: Dict[str, Any], 
                           customization: Dict[str, Any]) -> BytesIO:
        """Generate a certificate"""
        elements = []
        
        # Add decorative border if enabled
        if customization.get('show_border', True):
            elements.extend(self._create_decorative_border())
        
        # Add header with logo
        elements.extend(self._create_certificate_header(organization_data, customization))
        elements.append(Spacer(1, 40))
        
        # Add certificate title
        elements.extend(self._create_certificate_title(certificate_data))
        elements.append(Spacer(1, 30))
        
        # Add main content
        elements.extend(self._create_certificate_content(certificate_data))
        elements.append(Spacer(1, 40))
        
        # Add footer with signatures
        elements.extend(self._create_certificate_footer(organization_data, customization))
        
        # Generate PDF
        return self._generate_pdf(elements, organization_data, customization)
    
    def _create_decorative_border(self) -> List:
        """Create decorative border for certificate"""
        elements = []
        
        # Create border table
        border_style = TableStyle([
            ('GRID', (0, 0), (-1, -1), 2, colors.gold),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.gold),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        
        # Add decorative corners
        corner_size = 0.5 * inch
        border_data = [[' ']]
        border_table = Table(border_data, colWidths=[7*inch], rowHeights=[9*inch])
        border_table.setStyle(border_style)
        
        elements.append(border_table)
        return elements
    
    def _create_certificate_header(self, organization_data: Dict[str, Any], customization: Dict[str, Any]) -> List:
        """Create certificate header with logo"""
        elements = []
        
        # Add organization logo if available
        if customization.get('logo'):
            try:
                logo_img = Image(customization['logo'], width=1.5*inch, height=1.5*inch)
                elements.append(logo_img)
                elements.append(Spacer(1, 20))
            except Exception:
                print("Failed to load organization logo")
        
        # Add organization name
        org_name = organization_data.get('name', 'Organization Name')
        elements.append(Paragraph(org_name, self.styles['CustomHeader']))
        
        if organization_data.get('address'):
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(organization_data['address'], self.styles['CustomNormal']))
        
        return elements
    
    def _create_certificate_title(self, certificate_data: Dict[str, Any]) -> List:
        """Create certificate title section"""
        elements = []
        
        # Add certificate type
        cert_type = certificate_data.get('type', 'Certificate of Achievement')
        elements.append(Paragraph(cert_type.upper(), self.styles['CustomHeader']))
        
        # Add "This is to certify that" text
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("This is to certify that", self.styles['CustomNormal']))
        
        # Add recipient name
        elements.append(Spacer(1, 10))
        recipient_name = certificate_data.get('recipient_name', '')
        name_style = self.styles.add(ParagraphStyle(
            'RecipientName',
            parent=self.styles['CustomHeader'],
            fontSize=24,
            textColor=colors.darkblue,
            alignment=TA_CENTER
        ))
        elements.append(Paragraph(recipient_name, name_style))
        
        return elements
    
    def _create_certificate_content(self, certificate_data: Dict[str, Any]) -> List:
        """Create main certificate content"""
        elements = []
        
        # Add achievement description
        achievement = certificate_data.get('achievement', '')
        elements.append(Paragraph(achievement, self.styles['CustomNormal']))
        
        # Add additional details if available
        if details := certificate_data.get('details'):
            elements.append(Spacer(1, 15))
            elements.append(Paragraph(details, self.styles['CustomNormal']))
        
        # Add date
        elements.append(Spacer(1, 20))
        date_text = f"Awarded on {certificate_data.get('date', datetime.now().strftime('%B %d, %Y'))}"
        elements.append(Paragraph(date_text, self.styles['CustomNormal']))
        
        return elements
    
    def _create_certificate_footer(self, organization_data: Dict[str, Any], customization: Dict[str, Any]) -> List:
        """Create certificate footer with signatures"""
        elements = []
        
        # Create signature lines
        signature_data = []
        signatures = customization.get('signatures', [])
        
        if signatures:
            sig_row = []
            title_row = []
            width = 2 * inch
            
            for sig in signatures:
                sig_row.append('_' * 30)
                title_row.append(sig.get('title', ''))
            
            signature_data = [sig_row, title_row]
        else:
            # Default signature layout
            signature_data = [
                ['_' * 30, '_' * 30],
                ['Principal', 'Academic Director']
            ]
        
        # Create signature table
        sig_table = Table(signature_data, colWidths=[2.5*inch] * len(signature_data[0]))
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 10),
            ('TOPPADDING', (0, 1), (-1, 1), 10),
        ]))
        
        elements.append(sig_table)
        
        # Add certificate number if available
        if cert_number := customization.get('certificate_number'):
            elements.append(Spacer(1, 20))
            elements.append(Paragraph(
                f"Certificate No: {cert_number}",
                self.styles['CustomNormal']
            ))
        
        return elements
    
    def _generate_pdf(self, elements: List, organization_data: Dict[str, Any], customization: Dict[str, Any]) -> BytesIO:
        """Generate PDF from elements"""
        buffer = BytesIO()
        
        # Use landscape orientation for certificates
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Add watermark if enabled
        if customization.get('watermark'):
            elements.insert(0, self._create_watermark(customization['watermark']))
        
        # Add QR code if enabled
        if customization.get('qr_data'):
            elements.append(self._create_qr_code(customization['qr_data']))
        
        doc.build(elements)
        return buffer 
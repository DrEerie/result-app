# services/pdf_service.py
import io
from typing import Dict, Any, List, Optional
from flask import Response, current_app
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import black, white, blue, red, green, HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF
from datetime import datetime
import base64
import qrcode
from PIL import Image as PILImage

class BasePDFService:
    """Base class for PDF generation with common functionality"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup common custom styles for PDF generation"""
        # Header style
        self.styles.add(ParagraphStyle(
            name='CustomHeader',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Subheader style
        self.styles.add(ParagraphStyle(
            name='CustomSubHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Normal text style
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            alignment=TA_LEFT
        ))
        
        # Grade style
        self.styles.add(ParagraphStyle(
            name='Grade',
            parent=self.styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            textColor=colors.darkgreen
        ))
    
    def _create_header_section(self, organization_data: Dict[str, Any], customization: Dict[str, Any]) -> List:
        """Create common header section with logo and organization details"""
        elements = []
        
        # Create header table for logo and institute info
        header_data = []
        
        # Logo column
        logo_cell = ""
        if customization.get('logo'):
            try:
                logo_img = Image(customization['logo'], width=60, height=60)
                logo_cell = logo_img
            except Exception:
                print("Failed to load organization logo")
        
        # Organization info column
        org_info = [
            [Paragraph(organization_data.get('name', 'School Name'), self.styles['CustomHeader'])],
            [Paragraph(organization_data.get('address', ''), self.styles['Normal'])],
            [Paragraph(organization_data.get('contact', ''), self.styles['Normal'])]
        ]
        
        header_table = Table([[logo_cell, org_info]], colWidths=[80, 400])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(header_table)
        return elements
    
    def _create_footer_section(self, organization_data: Dict[str, Any], customization: Dict[str, Any]) -> List:
        """Create common footer with signatures"""
        elements = []
        
        # Signature table
        signature_data = [
            ['_________________', '_________________', '_________________'],
            ['Class Teacher', 'Principal', 'Parent/Guardian']
        ]
        
        signature_table = Table(signature_data, colWidths=[2*inch, 2*inch, 2*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ]))
        
        elements.append(signature_table)
        elements.append(Spacer(1, 20))
        
        # Generated timestamp
        elements.append(Paragraph(
            "Generated on: " + datetime.now().strftime("%B %d, %Y"),
            self.styles['Normal']
        ))
        
        return elements
    
    def _create_watermark(self, watermark_text: str) -> Drawing:
        """Create watermark for the PDF"""
        width, height = A4
        drawing = Drawing(width, height)
        
        # Create rotated text using affine transformation
        import math
        radians = math.radians(45)
        cos_theta = math.cos(radians)
        sin_theta = math.sin(radians)
        
        # Calculate center point
        cx, cy = width/2, height/2
        
        # Create text string with rotation around center
        text = String(
            cx, cy,
            watermark_text,
            fontSize=60,
            fillColor=colors.Color(0, 0, 0, alpha=0.1),
            textAnchor='middle'
        )
        
        # Apply rotation transformation
        text.x = cx + (text.x - cx) * cos_theta - (text.y - cy) * sin_theta
        text.y = cy + (text.x - cx) * sin_theta + (text.y - cy) * cos_theta
        
        drawing.add(text)
        return drawing
    
    def _create_qr_code(self, data: Dict[str, Any]) -> Image:
        """Create QR code with data"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(str(data))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, 'PNG')
        buffer.seek(0)
        
        return Image(buffer, width=1.5*inch, height=1.5*inch)
    
    def _calculate_grade(self, percentage: float) -> str:
        """Calculate grade based on percentage"""
        if percentage >= 90:
            return 'A+'
        elif percentage >= 80:
            return 'A'
        elif percentage >= 70:
            return 'B+'
        elif percentage >= 60:
            return 'B'
        elif percentage >= 50:
            return 'C'
        elif percentage >= 40:
            return 'D'
        else:
            return 'F'
    
    def _get_position_suffix(self, position: int) -> str:
        """Get position with appropriate suffix (1st, 2nd, 3rd, etc.)"""
        if 10 <= position % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(position % 10, 'th')
        return f"{position}{suffix}"
    
    def stream_pdf_response(self, pdf_buffer: io.BytesIO, filename: str) -> Any:
        """Stream PDF as response"""
        pdf_buffer.seek(0)
        from flask import Response
        return Response(
            pdf_buffer,
            mimetype='application/pdf',
            headers={'Content-Disposition': f'inline; filename="{filename}"'}
        )

class PDFService(BasePDFService):
    """Enhanced PDF generation service with modern styling and multiple templates"""
    
    def generate_marksheet(self, student_data: Dict[str, Any], results: List[Dict[str, Any]], 
                          organization_data: Dict[str, Any], template: str = 'modern',
                          customization: Optional[Dict[str, Any]] = None) -> io.BytesIO:
        """Generate individual student marksheet with specified template"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
        
        # Select template builder
        template_builders = {
            'modern': self._build_modern_marksheet,
            'classic': self._build_classic_marksheet,
            'compact': self._build_compact_marksheet
        }
        
        builder = template_builders.get(template, self._build_modern_marksheet)
        story = builder(student_data, results, organization_data, customization or {})
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_class_result(self, class_data: Dict[str, Any], students_results: List[Dict[str, Any]], 
                            organization_data: Dict[str, Any], template: str = 'modern',
                            customization: Optional[Dict[str, Any]] = None) -> io.BytesIO:
        """Generate class result sheet with specified template"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Select template builder
        template_builders = {
            'modern': self._build_modern_class_result,
            'classic': self._build_classic_class_result,
            'compact': self._build_compact_class_result
        }
        
        builder = template_builders.get(template, self._build_modern_class_result)
        story = builder(class_data, students_results, organization_data, customization or {})
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _build_modern_marksheet(self, student_data: Dict[str, Any], results: List[Dict[str, Any]], 
                              organization_data: Dict[str, Any], customization: Dict[str, Any]) -> List:
        """Build modern template for individual marksheet"""
        story = []
        
        # Add watermark if specified
        if customization.get('watermark'):
            story.append(self._create_watermark(customization['watermark']))
        
        # Header with logo
        story.extend(self._create_header_section(organization_data, customization))
        story.append(Spacer(1, 20))
        
        # Student information card
        story.extend(self._create_student_info_card(student_data))
        story.append(Spacer(1, 20))
        
        # Results table
        story.extend(self._create_results_table(results))
        story.append(Spacer(1, 20))
        
        # Performance analytics if enabled
        if customization.get('include_analytics', True):
            story.extend(self._create_performance_analytics(results))
            story.append(Spacer(1, 20))
        
        # Attendance section
        if student_data.get('attendance'):
            story.extend(self._create_attendance_section(student_data['attendance']))
            story.append(Spacer(1, 20))
        
        # Remarks section
        if student_data.get('remarks'):
            story.extend(self._create_remarks_section(student_data['remarks']))
            story.append(Spacer(1, 20))
        
        # QR code if enabled
        if customization.get('include_qr', True):
            story.append(self._create_qr_code(student_data))
            story.append(Spacer(1, 20))
        
        # Footer with signatures
        story.extend(self._create_footer_section(organization_data, customization))
        
        return story
    
    def _build_modern_class_result(self, class_data: Dict[str, Any], students_results: List[Dict[str, Any]], 
                                 organization_data: Dict[str, Any], customization: Dict[str, Any]) -> List:
        """Build modern template for class result sheet"""
        story = []
        
        # Add watermark if specified
        if customization.get('watermark'):
            story.append(self._create_watermark(customization['watermark']))
        
        # Header with logo
        story.extend(self._create_header_section(organization_data, customization))
        story.append(Spacer(1, 15))
        
        # Class information
        story.append(Paragraph(
            f"Class Result Sheet - {class_data.get('name', 'Class')}",
            self.styles['CustomSubHeader']
        ))
        story.append(Spacer(1, 15))
        
        # Class statistics
        story.extend(self._create_class_statistics(students_results))
        story.append(Spacer(1, 15))
        
        # Results table
        story.extend(self._create_class_results_table(students_results))
        story.append(Spacer(1, 15))
        
        # Performance analytics if enabled
        if customization.get('include_analytics', True):
            story.extend(self._create_class_analytics(students_results))
            story.append(Spacer(1, 20))
        
        # Footer with signatures
        story.extend(self._create_footer_section(organization_data, customization))
        
        return story
    
    def _build_classic_marksheet(self, student_data: Dict[str, Any], results: List[Dict[str, Any]], 
                               organization_data: Dict[str, Any], customization: Dict[str, Any]) -> List:
        """Build classic template for individual marksheet"""
        story = []
        
        # Classic header with border
        story.extend(self._create_classic_header(organization_data))
        story.append(Spacer(1, 15))
        
        # Student details in classic format
        story.extend(self._create_classic_student_details(student_data))
        story.append(Spacer(1, 15))
        
        # Traditional results table
        story.extend(self._create_classic_results_table(results))
        story.append(Spacer(1, 15))
        
        # Classic footer
        story.extend(self._create_classic_footer(organization_data))
        
        return story
    
    def _build_compact_marksheet(self, student_data: Dict[str, Any], results: List[Dict[str, Any]], 
                               organization_data: Dict[str, Any], customization: Dict[str, Any]) -> List:
        """Build compact template for individual marksheet"""
        story = []
        
        # Compact header
        story.extend(self._create_compact_header(organization_data))
        story.append(Spacer(1, 10))
        
        # Compact student info and results in columns
        story.extend(self._create_compact_layout(student_data, results))
        story.append(Spacer(1, 10))
        
        # Compact footer
        story.extend(self._create_compact_footer(organization_data))
        
        return story
    
    def _build_classic_class_result(self, class_data: Dict[str, Any], students_results: List[Dict[str, Any]], 
                                  organization_data: Dict[str, Any], customization: Dict[str, Any]) -> List:
        """Build classic template for class result sheet"""
        story = []
        
        # Classic header with border
        story.extend(self._create_classic_header(organization_data))
        story.append(Spacer(1, 15))
        
        # Class information
        story.extend(self._create_classic_class_info(class_data))
        story.append(Spacer(1, 15))
        
        # Results table
        story.extend(self._create_classic_class_results_table(students_results))
        story.append(Spacer(1, 15))
        
        # Classic footer
        story.extend(self._create_classic_footer(organization_data))
        
        return story
    
    def _build_compact_class_result(self, class_data: Dict[str, Any], students_results: List[Dict[str, Any]], 
                                  organization_data: Dict[str, Any], customization: Dict[str, Any]) -> List:
        """Build compact template for class result sheet"""
        story = []
        
        # Compact header
        story.extend(self._create_compact_header(organization_data))
        story.append(Spacer(1, 10))
        
        # Compact class info and results
        story.extend(self._create_compact_class_layout(class_data, students_results))
        story.append(Spacer(1, 10))
        
        # Compact footer
        story.extend(self._create_compact_footer(organization_data))
        
        return story
    
    def _create_student_info_card(self, student_data: Dict[str, Any]) -> List:
        """Create student information card"""
        elements = []
        
        student_info_data = [
            ['Student Name:', student_data.get('name', 'N/A')],
            ['Roll Number:', student_data.get('roll_number', 'N/A')],
            ['Class:', student_data.get('class_name', 'N/A')],
            ['Academic Year:', student_data.get('academic_year', datetime.now().year)]
        ]
        
        student_info_table = Table(student_info_data, colWidths=[2*inch, 3*inch])
        student_info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(student_info_table)
        return elements
    
    def _create_results_table(self, results: List[Dict[str, Any]]) -> List:
        """Create results table with grades"""
        elements = []
        
        if results:
            results_data = [['Subject', 'Marks Obtained', 'Total Marks', 'Percentage', 'Grade']]
            
            total_obtained = 0
            total_maximum = 0
            
            for result in results:
                marks_obtained = result.get('marks_obtained', 0)
                total_marks = result.get('total_marks', 0)
                percentage = (marks_obtained / total_marks * 100) if total_marks > 0 else 0
                grade = self._calculate_grade(percentage)
                
                results_data.append([
                    result.get('subject_name', 'N/A'),
                    str(marks_obtained),
                    str(total_marks),
                    f"{percentage:.1f}%",
                    grade
                ])
                
                total_obtained += marks_obtained
                total_maximum += total_marks
            
            # Add total row
            overall_percentage = (total_obtained / total_maximum * 100) if total_maximum > 0 else 0
            overall_grade = self._calculate_grade(overall_percentage)
            
            results_data.append([
                'TOTAL',
                str(total_obtained),
                str(total_maximum),
                f"{overall_percentage:.1f}%",
                overall_grade
            ])
            
            # Create results table
            results_table = Table(results_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1*inch, 0.8*inch])
            results_table.setStyle(TableStyle([
                # Header row styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                
                # Data rows styling
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -2), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.beige, colors.white]),
                
                # Total row styling
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 11),
                
                # Grid styling
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            elements.append(results_table)
            
            # Grade summary
            elements.append(Spacer(1, 15))
            elements.append(Paragraph(f"Overall Grade: {overall_grade}", self.styles['Grade']))
            elements.append(Paragraph(f"Overall Percentage: {overall_percentage:.1f}%", self.styles['Grade']))
        
        return elements
    
    def _create_performance_analytics(self, results: List[Dict[str, Any]]) -> List:
        """Create performance analytics section with charts"""
        elements = []
        
        # Add bar chart for subject-wise performance
        elements.append(Paragraph("Subject-wise Performance", self.styles['CustomNormal']))
        elements.append(Spacer(1, 10))
        elements.append(self._create_bar_chart(results))
        elements.append(Spacer(1, 15))
        
        # Add pie chart for grade distribution
        elements.append(Paragraph("Grade Distribution", self.styles['CustomNormal']))
        elements.append(Spacer(1, 10))
        elements.append(self._create_pie_chart(results))
        
        return elements
    
    def _create_attendance_section(self, attendance_data: Dict[str, Any]) -> List:
        """Create attendance section"""
        elements = []
        
        days_present = attendance_data.get('days_present', 0)
        total_days = attendance_data.get('total_days', 0)
        percentage = (days_present / total_days * 100) if total_days > 0 else 0
        
        attendance_table = Table([
            ['Days Present', 'Total Days', 'Attendance Percentage'],
            [str(days_present), str(total_days), f"{percentage:.1f}%"]
        ], colWidths=[2*inch, 2*inch, 2*inch])
        
        attendance_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ]))
        
        elements.append(Paragraph("Attendance Record", self.styles['CustomSubHeader']))
        elements.append(Spacer(1, 10))
        elements.append(attendance_table)
        
        return elements
    
    def _create_remarks_section(self, remarks: str) -> List:
        """Create remarks section"""
        elements = []
        
        elements.append(Paragraph("Remarks", self.styles['CustomSubHeader']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(remarks, self.styles['CustomNormal']))
        
        return elements
    
    def _create_class_statistics(self, students_results: List[Dict[str, Any]]) -> List:
        """Create class statistics section"""
        elements = []
        
        # Calculate statistics
        total_students = len(students_results)
        passed_students = sum(1 for s in students_results if s.get('is_pass', False))
        pass_percentage = (passed_students / total_students * 100) if total_students > 0 else 0
        
        # Create statistics table
        stats_data = [
            ['Total Students', 'Passed Students', 'Pass Percentage'],
            [str(total_students), str(passed_students), f"{pass_percentage:.1f}%"]
        ]
        
        stats_table = Table(stats_data, colWidths=[2*inch, 2*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ]))
        
        elements.append(stats_table)
        return elements
    
    def _create_class_results_table(self, students_results: List[Dict[str, Any]]) -> List:
        """Create class results table"""
        elements = []
        
        if students_results:
            # Prepare table headers
            headers = ['S.No', 'Roll No', 'Student Name', 'Total Marks', 'Percentage', 'Grade', 'Rank']
            
            # Prepare table data
            table_data = [headers]
            
            # Sort students by percentage for ranking
            sorted_students = sorted(
                students_results,
                key=lambda x: x.get('percentage', 0),
                reverse=True
            )
            
            for idx, student in enumerate(sorted_students, 1):
                row = [
                    str(idx),
                    student.get('roll_number', ''),
                    student.get('name', ''),
                    str(student.get('total_marks', 0)),
                    f"{student.get('percentage', 0):.1f}%",
                    student.get('grade', ''),
                    str(idx)
                ]
                table_data.append(row)
            
            # Create table
            results_table = Table(table_data, repeatRows=1)
            results_table.setStyle(TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                
                # Data styling
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('ALIGN', (2, 1), (2, -1), 'LEFT'),  # Student name left-aligned
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
                
                # Grid
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            elements.append(results_table)
        
        return elements
    
    def _create_class_analytics(self, students_results: List[Dict[str, Any]]) -> List:
        """Create class analytics section"""
        elements = []
        
        # Grade distribution chart
        elements.append(Paragraph("Grade Distribution", self.styles['CustomNormal']))
        elements.append(Spacer(1, 10))
        
        # Calculate grade distribution
        grade_counts = {'A+': 0, 'A': 0, 'B+': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        for student in students_results:
            grade = student.get('grade', 'F')
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        # Create pie chart
        drawing = Drawing(400, 200)
        pie = Pie()
        pie.x = 100
        pie.y = 0
        pie.width = 200
        pie.height = 200
        pie.data = list(grade_counts.values())
        pie.labels = list(grade_counts.keys())
        
        drawing.add(pie)
        elements.append(drawing)
        
        return elements
    
    def _create_classic_header(self, organization_data: Dict[str, Any]) -> List:
        """Create classic header with border"""
        elements = []
        
        # Create bordered header
        header_text = organization_data.get('name', 'School Name')
        header = Table([[Paragraph(header_text, self.styles['CustomHeader'])]], 
                      style=[
                          ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                          ('BOX', (0, 0), (-1, -1), 2, colors.black),
                          ('TOPPADDING', (0, 0), (-1, -1), 10),
                          ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                      ])
        elements.append(header)
        
        # Add address if available
        if organization_data.get('address'):
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(organization_data['address'], self.styles['CustomNormal']))
        
        return elements
    
    def _create_classic_student_details(self, student_data: Dict[str, Any]) -> List:
        """Create classic student details section"""
        elements = []
        
        # Student details in traditional format
        details_data = [
            ['Name of Student:', student_data.get('name', 'N/A')],
            ['Roll Number:', student_data.get('roll_number', 'N/A')],
            ['Class & Section:', f"{student_data.get('class_name', 'N/A')} {student_data.get('section', '')}"],
            ['Academic Year:', str(student_data.get('academic_year', datetime.now().year))]
        ]
        
        details_table = Table(details_data, colWidths=[2*inch, 4*inch],
                            style=[
                                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, -1), 11),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ])
        elements.append(details_table)
        
        return elements
    
    def _create_classic_results_table(self, results: List[Dict[str, Any]]) -> List:
        """Create classic results table"""
        elements = []
        
        if results:
            # Classic table with borders
            table_data = [['Subject', 'Maximum Marks', 'Marks Obtained', 'Grade']]
            
            for result in results:
                table_data.append([
                    result.get('subject_name', 'N/A'),
                    str(result.get('total_marks', 0)),
                    str(result.get('marks_obtained', 0)),
                    self._calculate_grade(result.get('percentage', 0))
                ])
            
            table = Table(table_data, style=[
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
            ])
            elements.append(table)
        
        return elements
    
    def _create_classic_footer(self, organization_data: Dict[str, Any]) -> List:
        """Create classic footer with traditional styling"""
        elements = []
        
        # Signature lines with titles
        signature_data = [
            ['________________', '________________', '________________'],
            ['Class Teacher', 'Principal', 'Parent/Guardian']
        ]
        
        signature_table = Table(signature_data, colWidths=[2*inch, 2*inch, 2*inch],
                              style=[
                                  ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                  ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                                  ('FONTSIZE', (0, 0), (-1, -1), 10),
                              ])
        
        elements.append(signature_table)
        elements.append(Spacer(1, 20))
        
        # Date and authentication
        elements.append(Paragraph(
            f"Date: {datetime.now().strftime('%d/%m/%Y')}",
            self.styles['CustomNormal']
        ))
        
        return elements
    
    def _create_compact_header(self, organization_data: Dict[str, Any]) -> List:
        """Create compact header"""
        elements = []
        
        # Minimal header with organization name
        header_text = organization_data.get('name', 'School Name')
        elements.append(Paragraph(header_text, self.styles['CustomHeader']))
        
        return elements
    
    def _create_compact_layout(self, student_data: Dict[str, Any], results: List[Dict[str, Any]]) -> List:
        """Create compact layout combining student info and results"""
        elements = []
        
        # Combine student info and results in a compact format
        info_text = (
            f"Name: {student_data.get('name', 'N/A')} | "
            f"Roll No: {student_data.get('roll_number', 'N/A')} | "
            f"Class: {student_data.get('class_name', 'N/A')}"
        )
        elements.append(Paragraph(info_text, self.styles['CustomNormal']))
        elements.append(Spacer(1, 10))
        
        # Compact results table
        if results:
            table_data = [['Subject', 'Marks', 'Grade']]
            for result in results:
                table_data.append([
                    result.get('subject_name', 'N/A'),
                    f"{result.get('marks_obtained', 0)}/{result.get('total_marks', 0)}",
                    self._calculate_grade(result.get('percentage', 0))
                ])
            
            table = Table(table_data, style=[
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
            ])
            elements.append(table)
        
        return elements
    
    def _create_compact_footer(self, organization_data: Dict[str, Any]) -> List:
        """Create compact footer"""
        elements = []
        
        # Minimal footer with date
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%d/%m/%Y')}",
            self.styles['CustomNormal']
        ))
        
        return elements
    
    def _create_classic_class_info(self, class_data: Dict[str, Any]) -> List:
        """Create classic class information section"""
        elements = []
        
        # Class details in traditional format
        info_data = [
            ['Class:', class_data.get('name', 'N/A')],
            ['Section:', class_data.get('section', 'N/A')],
            ['Academic Year:', str(class_data.get('academic_year', datetime.now().year))],
            ['Examination:', class_data.get('exam_name', 'Final Examination')]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch],
                         style=[
                             ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                             ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                             ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                             ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                         ])
        elements.append(info_table)
        
        return elements
    
    def _create_classic_class_results_table(self, students_results: List[Dict[str, Any]]) -> List:
        """Create classic class results table"""
        elements = []
        
        if students_results:
            # Traditional table with full borders
            table_data = [['Roll No.', 'Student Name', 'Total Marks', 'Percentage', 'Grade', 'Position']]
            
            # Sort by percentage for ranking
            sorted_students = sorted(
                students_results,
                key=lambda x: x.get('percentage', 0),
                reverse=True
            )
            
            for idx, student in enumerate(sorted_students, 1):
                table_data.append([
                    student.get('roll_number', ''),
                    student.get('name', ''),
                    str(student.get('total_marks', 0)),
                    f"{student.get('percentage', 0):.1f}%",
                    student.get('grade', ''),
                    self._get_position_suffix(idx)
                ])
            
            table = Table(table_data, style=[
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Student names left-aligned
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
            ])
            elements.append(table)
        
        return elements
    
    def _create_compact_class_layout(self, class_data: Dict[str, Any], students_results: List[Dict[str, Any]]) -> List:
        """Create compact layout for class results"""
        elements = []
        
        # Compact class info
        info_text = (
            f"Class: {class_data.get('name', 'N/A')} | "
            f"Section: {class_data.get('section', 'N/A')} | "
            f"Academic Year: {class_data.get('academic_year', datetime.now().year)}"
        )
        elements.append(Paragraph(info_text, self.styles['CustomNormal']))
        elements.append(Spacer(1, 10))
        
        # Compact results table
        if students_results:
            table_data = [['Roll No', 'Name', 'Total', '%', 'Grade']]
            
            # Sort by percentage
            sorted_students = sorted(
                students_results,
                key=lambda x: x.get('percentage', 0),
                reverse=True
            )
            
            for student in sorted_students:
                table_data.append([
                    student.get('roll_number', ''),
                    student.get('name', ''),
                    str(student.get('total_marks', 0)),
                    f"{student.get('percentage', 0):.1f}%",
                    student.get('grade', '')
                ])
            
            table = Table(table_data, style=[
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Names left-aligned
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),  # Smaller font for compact view
            ])
            elements.append(table)
        
        return elements
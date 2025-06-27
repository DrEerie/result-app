# services/pdf_service.py
import io
from typing import Dict, Any, List, Optional
from flask import Response, current_app
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white, blue, red, green
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import base64

class PDFStreamingService:
    """Service for generating and streaming PDFs without disk storage"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for PDF generation"""
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
        
        # Student info style
        self.styles.add(ParagraphStyle(
            name='StudentInfo',
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
    
    def generate_marksheet_pdf(self, student_data: Dict[str, Any], results: List[Dict[str, Any]], 
                              organization_data: Dict[str, Any]) -> io.BytesIO:
        """Generate individual student marksheet PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
        
        # Build PDF content
        story = []
        
        # Organization header
        story.append(Paragraph(organization_data.get('name', 'School Name'), self.styles['CustomHeader']))
        if organization_data.get('address'):
            story.append(Paragraph(organization_data['address'], self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Marksheet title
        story.append(Paragraph("STUDENT MARKSHEET", self.styles['CustomSubHeader']))
        story.append(Spacer(1, 20))
        
        # Student information
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
        
        story.append(student_info_table)
        story.append(Spacer(1, 30))
        
        # Results table
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
            
            story.append(results_table)
            story.append(Spacer(1, 30))
            
            # Grade summary
            story.append(Paragraph(f"Overall Grade: {overall_grade}", self.styles['Grade']))
            story.append(Paragraph(f"Overall Percentage: {overall_percentage:.1f}%", self.styles['Grade']))
        
        # Footer
        story.append(Spacer(1, 40))
        story.append(Paragraph("Generated on: " + datetime.now().strftime("%B %d, %Y"), self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_class_result_pdf(self, class_data: Dict[str, Any], students_results: List[Dict[str, Any]], 
                                 organization_data: Dict[str, Any]) -> io.BytesIO:
        """Generate class result sheet PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        story = []
        
        # Organization header
        story.append(Paragraph(organization_data.get('name', 'School Name'), self.styles['CustomHeader']))
        if organization_data.get('address'):
            story.append(Paragraph(organization_data['address'], self.styles['Normal']))
        story.append(Spacer(1, 15))
        
        # Class result title
        story.append(Paragraph(f"CLASS RESULT SHEET - {class_data.get('name', 'Class')}", self.styles['CustomSubHeader']))
        story.append(Spacer(1, 15))
        
        # Class information
        class_info = f"Academic Year: {class_data.get('academic_year', datetime.now().year)} | "
        class_info += f"Total Students: {len(students_results)}"
        story.append(Paragraph(class_info, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Results table
        if students_results:
            # Prepare table headers
            headers = ['S.No', 'Roll No', 'Student Name']
            subjects = []
            
            # Get all subjects from first student
            if students_results[0].get('results'):
                subjects = [result.get('subject_name', '') for result in students_results[0]['results']]
                headers.extend(subjects)
            
            headers.extend(['Total', 'Percentage', 'Grade', 'Rank'])
            
            # Prepare table data
            table_data = [headers]
            
            # Sort students by total marks (for ranking)
            sorted_students = sorted(students_results, key=lambda x: x.get('total_marks', 0), reverse=True)
            
            for idx, student in enumerate(sorted_students, 1):
                row = [
                    str(idx),
                    student.get('roll_number', ''),
                    student.get('name', '')
                ]
                
                # Add subject marks
                for subject in subjects:
                    subject_result = next((r for r in student.get('results', []) if r.get('subject_name') == subject), None)
                    if subject_result:
                        row.append(str(subject_result.get('marks_obtained', 0)))
                    else:
                        row.append('0')
                
                # Add totals
                total_marks = student.get('total_marks', 0)
                total_maximum = student.get('total_maximum', 0)
                percentage = (total_marks / total_maximum * 100) if total_maximum > 0 else 0
                grade = self._calculate_grade(percentage)
                
                row.extend([
                    str(total_marks),
                    f"{percentage:.1f}%",
                    grade,
                    str(idx)
                ])
                
                table_data.append(row)
            
            # Create table with dynamic column widths
            col_count = len(headers)
            page_width = 7.5 * inch  # Available width
            col_width = page_width / col_count
            
            class_table = Table(table_data, colWidths=[col_width] * col_count)
            class_table.setStyle(TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                
                # Data styling
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
                
                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
            ]))
            
            story.append(class_table)
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("Generated on: " + datetime.now().strftime("%B %d, %Y"), self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
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
    
    def stream_pdf_response(self, pdf_buffer: io.BytesIO, filename: str) -> Response:
        """Create Flask response for PDF streaming"""
        pdf_buffer.seek(0)
        
        return Response(
            pdf_buffer.getvalue(),
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'inline; filename="{filename}"',
                'Content-Type': 'application/pdf',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
    
    def generate_bulk_marksheets(self, students_data: List[Dict[str, Any]], 
                               organization_data: Dict[str, Any]) -> io.BytesIO:
        """Generate multiple marksheets in a single PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
        
        story = []
        
        for idx, student_data in enumerate(students_data):
            # Add page break for subsequent students
            if idx > 0:
                from reportlab.platypus import PageBreak
                story.append(PageBreak())
            
            # Generate marksheet content for each student
            student_story = self._generate_single_marksheet_content(
                student_data, 
                student_data.get('results', []), 
                organization_data
            )
            story.extend(student_story)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _generate_single_marksheet_content(self, student_data: Dict[str, Any], 
                                         results: List[Dict[str, Any]], 
                                         organization_data: Dict[str, Any]) -> List:
        """Generate content for a single marksheet (reusable for bulk generation)"""
        story = []
        
        # Organization header
        story.append(Paragraph(organization_data.get('name', 'School Name'), self.styles['CustomHeader']))
        if organization_data.get('address'):
            story.append(Paragraph(organization_data['address'], self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Marksheet title
        story.append(Paragraph("STUDENT MARKSHEET", self.styles['CustomSubHeader']))
        story.append(Spacer(1, 20))
        
        # Student information
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
        
        story.append(student_info_table)
        story.append(Spacer(1, 30))
        
        # Results table (similar to marksheet generation)
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
            
            story.append(results_table)
            story.append(Spacer(1, 30))
            
            # Grade summary
            story.append(Paragraph(f"Overall Grade: {overall_grade}", self.styles['Grade']))
            story.append(Paragraph(f"Overall Percentage: {overall_percentage:.1f}%", self.styles['Grade']))
        
        # Footer
        story.append(Spacer(1, 40))
        story.append(Paragraph("Generated on: " + datetime.now().strftime("%B %d, %Y"), self.styles['Normal']))
        
        return story
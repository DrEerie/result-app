from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Register custom fonts (optional)
try:
    pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
except:
    pass  # Use default fonts if Arial is not available

def generate_result_pdf(student_data, save_path):
    """Generate PDF with dynamic max marks"""
    doc = SimpleDocTemplate(save_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30
    )
    elements.append(Paragraph(f"Result Card - {student_data['name']}", header_style))
    
    # Student Info
    student_info = [
        ['Name:', student_data['name']],
        ['Roll No:', student_data['roll_no']],
        ['Class:', f"{student_data['cls']}-{student_data['section']}"]
    ]
    info_table = Table(student_info, colWidths=[100, 300])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 20))

    # Marks Table
    marks_data = [['Subject', 'Marks Obtained', 'Maximum Marks', 'Percentage', 'Grade']]
    for subject in student_data['overall_result']['subject_results']:
        marks_data.append([
            subject['subject_name'],
            str(subject['marks']),
            str(subject['max_marks']),  # Show subject's max marks
            f"{subject['percentage']}%",
            subject['grade']
        ])
    
    marks_table = Table(marks_data, colWidths=[150, 100, 100, 100])
    marks_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey)
    ]))
    elements.append(marks_table)
    elements.append(Spacer(1, 20))

    # Overall Result
    overall_data = [
        ['Total Marks:', f"{student_data['overall_result']['total_marks']}/{student_data['overall_result']['total_max_marks']}"],
        ['Overall Percentage:', f"{student_data['overall_result']['overall_percentage']}%"],
        ['Grade:', student_data['overall_result']['overall_grade']],
        ['Status:', 'PASS' if student_data['overall_result']['is_pass'] else 'FAIL']
    ]
    overall_table = Table(overall_data, colWidths=[100, 300])
    overall_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)
    ]))
    elements.append(overall_table)

    # Add school logo/header
    elements.append(Spacer(1, 30))
    
    # Add watermark
    def add_watermark(canvas, doc):
        canvas.saveState()
        canvas.setFillColorRGB(0.95, 0.95, 0.95)
        canvas.setFont("Helvetica", 100)
        canvas.translate(300, 400)
        canvas.rotate(45)
        canvas.drawString(0, 0, "RESULT")
        canvas.restoreState()
    
    doc.build(elements, onFirstPage=add_watermark, onLaterPages=add_watermark)
    return save_path

def generate_class_pdf(class_data, save_path):
    """Generate PDF result for an entire class"""
    doc = SimpleDocTemplate(save_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    
    # Header
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30
    )
    elements.append(Paragraph(f"Class {class_data['cls']}-{class_data['section']} Results", header_style))
    
    # Table header
    table_data = [['Roll No', 'Name', 'Total Marks', 'Percentage', 'Grade', 'Status']]
    
    # Add student rows
    for student in sorted(class_data['students'], key=lambda x: x['roll_no']):
        result = student['overall_result']
        table_data.append([
            student['roll_no'],
            student['name'],
            f"{result['total_marks']}/{result['total_max_marks']}",
            f"{result['overall_percentage']}%",
            result['overall_grade'],
            'PASS' if result['is_pass'] else 'FAIL'
        ])
    
    # Create and style table
    table = Table(table_data, colWidths=[60, 150, 80, 70, 50, 50])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER')
    ]))
    elements.append(table)
    
    doc.build(elements)
    return save_path

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from PIL import Image
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.utils import ImageReader
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF
import qrcode
from io import BytesIO
import os
from datetime import datetime

# Enhanced PDF generation for academic results with modern styling. generate pdf-1
def generate_result_pdf(student_data, output_path, customization_data=None):
    """Enhanced PDF generation with modern academic styling"""
    try:
        # Initialize document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=20,
            leftMargin=20,
            topMargin=30,
            bottomMargin=30
        )
        
        # Get template choice
        template = customization_data.get('template', 'modern') if customization_data else 'modern'
        
        # Build content based on template
        if template == 'classic':
            story = _build_classic_template(student_data, customization_data)
        elif template == 'compact':
            story = _build_compact_template(student_data, customization_data)
        else:  # modern (default)
            story = _build_modern_template(student_data, customization_data)
        
        # Build PDF
        doc.build(story)
        return True
        
    except Exception as e:
        print(f"Error generating enhanced PDF: {str(e)}")
        return False

def _build_modern_template(student_data, customization_data):
    """Build modern academic template with clean design"""
    story = []
    styles = _get_enhanced_styles(customization_data)
    
    # Header Section
    story.extend(_create_header_section(student_data, customization_data, styles))
    story.append(Spacer(1, 20))
    
    # Student Information Card
    story.extend(_create_student_info_card(student_data, customization_data, styles))
    story.append(Spacer(1, 20))
    
    # Results Table
    story.extend(_create_results_table(student_data, customization_data, styles))
    story.append(Spacer(1, 20))
    
    # Performance Analytics (if enabled)
    if customization_data and customization_data.get('include_analytics', True):
        story.extend(_create_performance_analytics(student_data, customization_data, styles))
        story.append(Spacer(1, 20))
    
    # Attendance Section
    story.extend(_create_attendance_section(student_data, customization_data, styles))
    story.append(Spacer(1, 20))
    
    # Remarks Section
    story.extend(_create_remarks_section(student_data, customization_data, styles))
    story.append(Spacer(1, 20))
    
    # Footer with Signatures
    story.extend(_create_footer_section(student_data, customization_data, styles))
    
    return story

def _build_classic_template(student_data, customization_data):
    """Build traditional academic template"""
    story = []
    styles = _get_enhanced_styles(customization_data, theme='classic')
    
    # Classic header with border
    story.extend(_create_classic_header(student_data, customization_data, styles))
    story.append(Spacer(1, 15))
    
    # Student details in classic format
    story.extend(_create_classic_student_details(student_data, customization_data, styles))
    story.append(Spacer(1, 15))
    
    # Traditional results table
    story.extend(_create_classic_results_table(student_data, customization_data, styles))
    story.append(Spacer(1, 15))
    
    # Classic footer
    story.extend(_create_classic_footer(student_data, customization_data, styles))
    
    return story

def _build_compact_template(student_data, customization_data):
    """Build space-efficient compact template"""
    story = []
    styles = _get_enhanced_styles(customization_data, theme='compact')
    
    # Compact header
    story.extend(_create_compact_header(student_data, customization_data, styles))
    story.append(Spacer(1, 10))
    
    # Compact student info and results in columns
    story.extend(_create_compact_layout(student_data, customization_data, styles))
    story.append(Spacer(1, 10))
    
    # Compact footer
    story.extend(_create_compact_footer(student_data, customization_data, styles))
    
    return story

def _get_enhanced_styles(customization_data, theme='modern'):
    """Create enhanced styles based on theme and customization"""
    styles = getSampleStyleSheet()
    
    # Get colors from customization
    main_color = colors.toColor(customization_data.get('main_color', '#1E40AF')) if customization_data else colors.blue
    header_color = colors.toColor(customization_data.get('header_color', '#E5E7EB')) if customization_data else colors.lightgrey
    
    # Enhanced styles
    styles.add(ParagraphStyle(
        name='EnhancedTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=20,
        textColor=main_color,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='InstituteHeader',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=10,
        textColor=main_color,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=15,
        spaceAfter=10,
        textColor=main_color,
        fontName='Helvetica-Bold',
        borderWidth=1,
        borderColor=main_color,
        borderPadding=5
    ))
    
    styles.add(ParagraphStyle(
        name='StudentInfo',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=5,
        fontName='Helvetica'
    ))
    
    styles.add(ParagraphStyle(
        name='TableHeader',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.black,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER
    ))
    
    return styles

def _create_header_section(student_data, customization_data, styles):
    """Create modern header with logo and institute details"""
    header_elements = []
    
    # Create header table for logo and institute info
    header_data = []
    
    # Logo column
    logo_cell = ""
    if customization_data and customization_data.get('logo'):
        try:
            logo_img = Image(customization_data['logo'], width=60, height=60)
            logo_cell = logo_img
        except:
            logo_cell = ""
    
    # Institute info column
    institute_name = customization_data.get('institute_name', 'School Name') if customization_data else 'School Name'
    exam_name = customization_data.get('exam_name', 'Examination') if customization_data else 'Examination'
    
    institute_info = f"""
    <b>{institute_name}</b><br/>
    <i>{exam_name}</i><br/>
    Academic Session: {datetime.now().year}
    """
    
    # QR Code column (if enabled)
    qr_cell = ""
    if customization_data and customization_data.get('include_qr', True):
        qr_cell = _create_qr_code(student_data)
    
    header_data.append([logo_cell, Paragraph(institute_info, styles['InstituteHeader']), qr_cell])
    
    header_table = Table(header_data, colWidths=[80, 350, 80])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 0), (1, 0), 14),
    ]))
    
    header_elements.append(header_table)
    
    # Add decorative line
    header_elements.append(Spacer(1, 10))
    line_data = [[''] * 3]
    line_table = Table(line_data, colWidths=[510])
    line_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 2, colors.blue),
    ]))
    header_elements.append(line_table)
    
    return header_elements

def _create_student_info_card(student_data, customization_data, styles):
    """Create modern student information card"""
    card_elements = []
    
    # Student photo (if available)
    photo_cell = ""
    if customization_data and customization_data.get('student_photo'):
        try:
            photo_img = Image(customization_data['student_photo'], width=80, height=100)
            photo_cell = photo_img
        except:
            photo_cell = ""
    
    # Student details
    student_info = f"""
    <b>Student Name:</b> {student_data['name']}<br/>
    <b>Roll Number:</b> {student_data['roll_no']}<br/>
    <b>Class:</b> {student_data['cls']}<br/>
    <b>Section:</b> {student_data['section']}<br/>
    """
    
    # Create student info table
    info_data = [[photo_cell, Paragraph(student_info, styles['StudentInfo'])]]
    info_table = Table(info_data, colWidths=[100, 400])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightyellow),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    
    card_elements.append(info_table)
    return card_elements

def _create_results_table(student_data, customization_data, styles):
    """Create enhanced results table with proper formatting"""
    table_elements = []
    
    # Section header
    table_elements.append(Paragraph("📊 Academic Performance", styles['SectionHeader']))
    table_elements.append(Spacer(1, 10))
    
    # Get subject results
    results = student_data.get('overall_result', {})
    subjects = results.get('subjects', [])
    
    # Table headers
    headers = ['Subject', 'Max Marks', 'Obtained', 'Grade', 'Percentage']
    table_data = [headers]
    
    # Add subject data
    for subject in subjects:
        row = [
            subject.get('name', ''),
            str(subject.get('max_marks', '')),
            str(subject.get('obtained_marks', '')),
            subject.get('grade', ''),
            f"{subject.get('percentage', 0):.1f}%"
        ]
        table_data.append(row)
    
    # Add totals row
    total_max = sum(s.get('max_marks', 0) for s in subjects)
    total_obtained = sum(s.get('obtained_marks', 0) for s in subjects)
    total_percentage = (total_obtained / total_max * 100) if total_max > 0 else 0
    
    table_data.append([
        'TOTAL',
        str(total_max),
        str(total_obtained),
        results.get('overall_grade', ''),
        f"{total_percentage:.1f}%"
    ])
    
    # Create table
    results_table = Table(table_data, colWidths=[120, 80, 80, 60, 80])
    
    # Enhanced table styling
    main_color = colors.toColor(customization_data.get('main_color', '#1E40AF')) if customization_data else colors.blue
    header_color = colors.toColor(customization_data.get('header_color', '#E5E7EB')) if customization_data else colors.lightgrey
    
    results_table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Data rows styling
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 10),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        
        # Total row styling
        ('BACKGROUND', (0, -1), (-1, -1), main_color),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        
        # Borders
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 2, main_color),
        
        # Padding
        ('PADDING', (0, 0), (-1, -1), 8),
        
        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
    ]))
    
    table_elements.append(results_table)
    return table_elements

def _create_performance_analytics(student_data, customization_data, styles):
    """Create performance charts and analytics"""
    analytics_elements = []
    
    # Section header
    analytics_elements.append(Paragraph("📈 Performance Analytics", styles['SectionHeader']))
    analytics_elements.append(Spacer(1, 10))
    
    # Get chart type from customization
    chart_type = customization_data.get('chart_type', 'bar') if customization_data else 'bar'
    
    if chart_type == 'bar':
        chart = _create_bar_chart(student_data, customization_data)
    elif chart_type == 'pie':
        chart = _create_pie_chart(student_data, customization_data)
    else:
        chart = _create_bar_chart(student_data, customization_data)  # default
    
    if chart:
        analytics_elements.append(chart)
    
    return analytics_elements

def _create_bar_chart(student_data, customization_data):
    """Create performance bar chart"""
    try:
        results = student_data.get('overall_result', {})
        subjects = results.get('subjects', [])
        
        if not subjects:
            return None
        
        # Create chart
        drawing = Drawing(400, 200)
        chart = VerticalBarChart()
        chart.x = 50
        chart.y = 50
        chart.height = 125
        chart.width = 300
        
        # Data
        chart.data = [[s.get('percentage', 0) for s in subjects]]
        chart.categoryAxis.categoryNames = [s.get('name', '')[:8] for s in subjects]
        
        # Styling
        chart.bars[0].fillColor = colors.blue
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = 100
        chart.categoryAxis.labels.boxAnchor = 'ne'
        chart.categoryAxis.labels.dx = 8
        chart.categoryAxis.labels.dy = -2
        chart.categoryAxis.labels.angle = 30
        
        drawing.add(chart)
        return drawing
    except:
        return None

def _create_pie_chart(student_data, customization_data):
    """Create grade distribution pie chart"""
    try:
        results = student_data.get('overall_result', {})
        subjects = results.get('subjects', [])
        
        if not subjects:
            return None
        
        # Count grades
        grade_counts = {}
        for subject in subjects:
            grade = subject.get('grade', 'N/A')
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        # Create chart
        drawing = Drawing(300, 200)
        pie = Pie()
        pie.x = 50
        pie.y = 50
        pie.width = 100
        pie.height = 100
        
        pie.data = list(grade_counts.values())
        pie.labels = list(grade_counts.keys())
        pie.slices.strokeWidth = 0.5
        
        drawing.add(pie)
        return drawing
    except:
        return None

def _create_attendance_section(student_data, customization_data, styles):
    """Create attendance information section"""
    attendance_elements = []
    
    # Section header
    attendance_elements.append(Paragraph("📅 Attendance Record", styles['SectionHeader']))
    attendance_elements.append(Spacer(1, 10))
    
    # Attendance data
    days_present = student_data.get('days_present', 0)
    max_days = student_data.get('max_days', 0)
    attendance_percentage = (days_present / max_days * 100) if max_days > 0 else 0
    
    # Create attendance table
    attendance_data = [
        ['Days Present', 'Total Days', 'Attendance %'],
        [str(days_present), str(max_days), f"{attendance_percentage:.1f}%"]
    ]
    
    attendance_table = Table(attendance_data, colWidths=[100, 100, 100])
    attendance_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    
    attendance_elements.append(attendance_table)
    return attendance_elements

def _create_remarks_section(student_data, customization_data, styles):
    """Create remarks section"""
    remarks_elements = []
    
    # Section header
    remarks_elements.append(Paragraph("💭 Remarks", styles['SectionHeader']))
    remarks_elements.append(Spacer(1, 10))
    
    # Get remarks
    if customization_data and customization_data.get('remarks_type') == 'manual':
        remarks_text = customization_data.get('remarks', 'No remarks provided.')
    else:
        # Auto-generate based on performance
        results = student_data.get('overall_result', {})
        total_percentage = results.get('percentage', 0)
        
        if total_percentage >= 90:
            remarks_text = "Excellent performance! Keep up the outstanding work."
        elif total_percentage >= 75:
            remarks_text = "Good performance. Continue your efforts to achieve excellence."
        elif total_percentage >= 60:
            remarks_text = "Satisfactory performance. Focus on improvement in weaker areas."
        elif total_percentage >= 40:
            remarks_text = "Needs improvement. Please work harder and seek additional help."
        else:
            remarks_text = "Poor performance. Immediate attention and extra effort required."
    
    remarks_para = Paragraph(remarks_text, styles['Normal'])
    
    # Create remarks box
    remarks_data = [[remarks_para]]
    remarks_table = Table(remarks_data, colWidths=[500])
    remarks_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightyellow),
        ('PADDING', (0, 0), (-1, -1), 15),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    remarks_elements.append(remarks_table)
    return remarks_elements

def _create_footer_section(student_data, customization_data, styles):
    """Create footer with signatures"""
    footer_elements = []
    
    # Add spacing
    footer_elements.append(Spacer(1, 30))
    
    # Signature section
    principal_name = customization_data.get('principal_name', 'Principal') if customization_data else 'Principal'
    teacher_name = customization_data.get('teacher_name', 'Class Teacher') if customization_data else 'Class Teacher'
    
    signature_data = [
        ['Date: ___________', '', 'Parent Signature'],
        ['', '', ''],
        ['', '', ''],
        [f'({principal_name})', f'({teacher_name})', ''],
        ['Principal', 'Class Teacher', '']
    ]
    
    signature_table = Table(signature_data, colWidths=[150, 150, 150])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 3), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 2), (-1, 2), 20),
    ]))
    
    footer_elements.append(signature_table)
    
    # Add watermark if specified
    if customization_data and customization_data.get('watermark_type'):
        footer_elements.extend(_add_watermark(customization_data))
    
    return footer_elements

def _create_qr_code(student_data):
    """Create QR code for result verification"""
    try:
        # Create QR code data
        qr_data = f"Student: {student_data['name']}\nRoll: {student_data['roll_no']}\nClass: {student_data['cls']}-{student_data['section']}"
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=2, border=1)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to ReportLab image
        img_buffer = BytesIO()
        qr_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return Image(img_buffer, width=60, height=60)
    except:
        return ""

def _add_watermark(customization_data):
    """Add watermark to document"""
    watermark_elements = []
    
    # This is a placeholder - actual watermark implementation would require
    # more complex canvas manipulation or custom page templates
    
    return watermark_elements

# Classic template functions (simplified versions)
def _create_classic_header(student_data, customization_data, styles):
    """Create classic academic header"""
    header_elements = []
    
    institute_name = customization_data.get('institute_name', 'School Name') if customization_data else 'School Name'
    header_elements.append(Paragraph(f"<b>{institute_name}</b>", styles['EnhancedTitle']))
    header_elements.append(Paragraph("ACADEMIC RESULT CARD", styles['InstituteHeader']))
    header_elements.append(Spacer(1, 10))
    
    return header_elements

def _create_classic_student_details(student_data, customization_data, styles):
    """Create classic student details layout"""
    details_elements = []
    
    # Simple student info table
    student_info = [
        ['Student Name:', student_data['name'], 'Roll Number:', student_data['roll_no']],
        ['Class:', student_data['cls'], 'Section:', student_data['section']]
    ]
    
    info_table = Table(student_info, colWidths=[100, 150, 100, 150])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    
    details_elements.append(info_table)
    return details_elements

def _create_classic_results_table(student_data, customization_data, styles):
    """Create classic results table"""
    # Similar to modern but with traditional styling
    return _create_results_table(student_data, customization_data, styles)

def _create_classic_footer(student_data, customization_data, styles):
    """Create classic footer"""
    return _create_footer_section(student_data, customization_data, styles)

# Compact template functions
def _create_compact_header(student_data, customization_data, styles):
    """Create compact header"""
    return _create_classic_header(student_data, customization_data, styles)

def _create_compact_layout(student_data, customization_data, styles):
    """Create compact layout combining multiple sections"""
    compact_elements = []
    
    # Combine student info and results in a more compact format
    compact_elements.extend(_create_student_info_card(student_data, customization_data, styles))
    compact_elements.append(Spacer(1, 10))
    compact_elements.extend(_create_results_table(student_data, customization_data, styles))
    
    return compact_elements

def _create_compact_footer(student_data, customization_data, styles):
    """Create compact footer"""
    return _create_footer_section(student_data, customization_data, styles)
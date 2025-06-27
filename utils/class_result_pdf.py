from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from datetime import datetime

def generate_class_pdf(class_data, output_path, customization_data=None):
    """Generate enhanced PDF for entire class with modern styling and customization."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=20,
        leftMargin=20,
        topMargin=30,
        bottomMargin=30
    )
    styles = getSampleStyleSheet()
    main_color = colors.toColor(customization_data.get('main_color', '#1E40AF')) if customization_data else colors.blue

    # Title/Header
    story = []
    institute_name = customization_data.get('institute_name', 'School Name') if customization_data else 'School Name'
    exam_name = customization_data.get('exam_name', 'Examination') if customization_data else 'Examination'
    story.append(Paragraph(f"<b>{institute_name}</b>", ParagraphStyle('Title', fontSize=20, alignment=TA_CENTER, textColor=main_color)))
    story.append(Paragraph(f"{exam_name} - Class {class_data['cls']} Section {class_data['section']}", ParagraphStyle('Heading2', fontSize=14, alignment=TA_CENTER)))
    story.append(Spacer(1, 16))

    # Table header
    headers = ['Roll No', 'Name', 'Attendance', 'Subjects', 'Total %', 'Grade', 'Status']
    table_data = [headers]

    # Table rows
    for student in class_data['students']:
        overall = student['overall_result']
        subjects_str = ", ".join(
            f"{s['subject_name']} ({s['marks']}/{s['max_marks']}, {s['grade']})"
            for s in overall['subject_results']
        )
        attendance_str = f"{student['days_present']}/{student['max_days']} ({(student['days_present']/student['max_days']*100):.1f}%)"
        table_data.append([
            student['roll_no'],
            student['name'],
            attendance_str,
            subjects_str,
            f"{overall['overall_percentage']}%",
            overall['overall_grade'],
            "PASS" if overall['is_pass'] else "FAIL"
        ])

    # Table styling
    table = Table(table_data, colWidths=[60, 100, 90, 180, 50, 40, 40])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), main_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('ALIGN', (3, 1), (3, -1), 'LEFT'),
    ]))

    story.append(table)
    story.append(Spacer(1, 20))

    # Optional: Add class remarks if provided
    if customization_data and customization_data.get('class_remarks'):
        story.append(Paragraph("<b>Remarks:</b>", styles['Heading3']))
        story.append(Paragraph(customization_data['class_remarks'], styles['Normal']))

    # Footer
    principal = customization_data.get('principal_name', 'Principal') if customization_data else 'Principal'
    teacher = customization_data.get('teacher_name', 'Class Teacher') if customization_data else 'Class Teacher'
    story.append(Spacer(1, 30))
    footer_table = Table([
        [f"({principal})", f"({teacher})"],
        ["Principal", "Class Teacher"]
    ], colWidths=[200, 200])
    footer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(footer_table)

    doc.build(story)

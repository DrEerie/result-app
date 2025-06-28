from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib.units import inch
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing
from services.pdf_service import BasePDFService
from io import BytesIO

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

class ClassResultPDFService(BasePDFService):
    """Service for generating class result sheets"""
    
    def generate_class_result(self, class_data: Dict[str, Any], students_results: List[Dict[str, Any]], 
                            organization_data: Dict[str, Any], customization: Dict[str, Any]) -> BytesIO:
        """Generate a class result sheet"""
        elements = []
        
        # Add header
        elements.extend(self._create_header_section(organization_data, customization))
        elements.append(Spacer(1, 20))
        
        # Add class information
        elements.extend(self._create_class_info_section(class_data))
        elements.append(Spacer(1, 20))
        
        # Add results table
        elements.extend(self._create_class_results_table(students_results))
        elements.append(Spacer(1, 20))
        
        # Add performance analytics
        if customization.get('show_analytics', True):
            elements.extend(self._create_class_analytics(students_results))
            elements.append(Spacer(1, 20))
        
        # Add footer with signatures
        elements.extend(self._create_footer_section(organization_data, customization))
        
        # Generate PDF
        return self._generate_pdf(elements, organization_data, customization)
    
    def _create_class_info_section(self, class_data: Dict[str, Any]) -> List:
        """Create class information section"""
        elements = []
        
        # Class details table
        class_info = [
            ['Class:', class_data.get('name', 'N/A'), 'Section:', class_data.get('section', 'N/A')],
            ['Academic Year:', class_data.get('academic_year', 'N/A'), 'Total Students:', str(class_data.get('total_students', 0))],
            ['Class Teacher:', class_data.get('class_teacher', 'N/A'), 'Exam Type:', class_data.get('exam_type', 'N/A')]
        ]
        
        info_table = Table(class_info, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
        ]))
        
        elements.append(info_table)
        return elements
    
    def _create_class_results_table(self, students_results: List[Dict[str, Any]]) -> List:
        """Create class results table"""
        elements = []
        
        # Get all unique subjects
        subjects = sorted(list(set(
            subject['name']
            for student in students_results
            for subject in student.get('subjects', [])
        )))
        
        # Table header
        header = ['Roll No.', 'Student Name'] + subjects + ['Total', 'Percentage', 'Grade', 'Position']
        
        # Table data
        data = [header]
        
        # Sort students by percentage in descending order
        sorted_results = sorted(
            students_results,
            key=lambda x: x.get('total_percentage', 0),
            reverse=True
        )
        
        # Add student rows
        for position, student in enumerate(sorted_results, 1):
            row = [
                student.get('roll_number', 'N/A'),
                student.get('name', 'N/A')
            ]
            
            # Add subject marks
            subject_marks = {
                subject['name']: subject['marks']
                for subject in student.get('subjects', [])
            }
            row.extend(str(subject_marks.get(subject, '-')) for subject in subjects)
            
            # Add totals
            row.extend([
                str(student.get('total_marks', 0)),
                f"{student.get('total_percentage', 0):.1f}%",
                self._calculate_grade(student.get('total_percentage', 0)),
                self._get_position_suffix(position)
            ])
            
            data.append(row)
        
        # Create table
        col_widths = [1*inch, 2*inch] + [0.8*inch] * len(subjects) + [0.8*inch, 1*inch, 0.8*inch, 0.8*inch]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        return elements
    
    def _create_class_analytics(self, students_results: List[Dict[str, Any]]) -> List:
        """Create class analytics section"""
        elements = []
        
        # Subject-wise average performance
        elements.append(Paragraph("Subject-wise Class Average", self.styles['CustomNormal']))
        elements.append(Spacer(1, 10))
        elements.append(self._create_subject_averages_chart(students_results))
        elements.append(Spacer(1, 15))
        
        # Grade distribution
        elements.append(Paragraph("Class Grade Distribution", self.styles['CustomNormal']))
        elements.append(Spacer(1, 10))
        elements.append(self._create_grade_distribution_chart(students_results))
        elements.append(Spacer(1, 15))
        
        # Class statistics
        elements.extend(self._create_class_statistics(students_results))
        
        return elements
    
    def _create_subject_averages_chart(self, students_results: List[Dict[str, Any]]) -> Drawing:
        """Create bar chart for subject-wise class averages"""
        # Calculate subject averages
        subject_totals = {}
        subject_counts = {}
        
        for student in students_results:
            for subject in student.get('subjects', []):
                name = subject['name']
                marks = subject.get('marks', 0)
                max_marks = subject.get('max_marks', 100)
                
                if max_marks > 0:
                    percentage = (marks / max_marks) * 100
                    subject_totals[name] = subject_totals.get(name, 0) + percentage
                    subject_counts[name] = subject_counts.get(name, 0) + 1
        
        subjects = []
        averages = []
        for subject in sorted(subject_totals.keys()):
            subjects.append(subject)
            avg = subject_totals[subject] / subject_counts[subject]
            averages.append(avg)
        
        # Create drawing
        drawing = Drawing(400, 200)
        
        # Create bar chart
        bc = VerticalBarChart()
        bc.x = 50
        bc.y = 50
        bc.height = 125
        bc.width = 300
        bc.data = [averages]
        bc.categoryAxis.categoryNames = subjects
        bc.categoryAxis.labels.boxAnchor = 'ne'
        bc.categoryAxis.labels.angle = 30
        bc.categoryAxis.labels.dx = -8
        bc.categoryAxis.labels.dy = -2
        bc.valueAxis.valueMin = 0
        bc.valueAxis.valueMax = 100
        bc.valueAxis.valueStep = 10
        bc.bars[0].fillColor = colors.lightblue
        
        drawing.add(bc)
        return drawing
    
    def _create_grade_distribution_chart(self, students_results: List[Dict[str, Any]]) -> Drawing:
        """Create pie chart for grade distribution"""
        # Calculate grade distribution
        grade_counts = {'A+': 0, 'A': 0, 'B+': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        
        for student in students_results:
            percentage = student.get('total_percentage', 0)
            grade = self._calculate_grade(percentage)
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        # Filter out grades with zero count
        grades = []
        counts = []
        for grade, count in grade_counts.items():
            if count > 0:
                grades.append(grade)
                counts.append(count)
        
        # Create drawing
        drawing = Drawing(400, 200)
        
        # Create pie chart
        pc = Pie()
        pc.x = 150
        pc.y = 50
        pc.width = 100
        pc.height = 100
        pc.data = counts
        pc.labels = grades
        pc.slices.strokeWidth = 0.5
        
        drawing.add(pc)
        return drawing
    
    def _create_class_statistics(self, students_results: List[Dict[str, Any]]) -> List:
        """Create class statistics section"""
        elements = []
        
        # Calculate statistics
        total_students = len(students_results)
        passing_students = sum(1 for s in students_results if s.get('total_percentage', 0) >= 40)
        highest_percentage = max((s.get('total_percentage', 0) for s in students_results), default=0)
        lowest_percentage = min((s.get('total_percentage', 0) for s in students_results), default=0)
        
        if total_students > 0:
            avg_percentage = sum(s.get('total_percentage', 0) for s in students_results) / total_students
            pass_percentage = (passing_students / total_students) * 100
        else:
            avg_percentage = 0
            pass_percentage = 0
        
        # Create statistics table
        stats_data = [
            ['Total Students', str(total_students), 'Passing Students', str(passing_students)],
            ['Highest Percentage', f"{highest_percentage:.1f}%", 'Lowest Percentage', f"{lowest_percentage:.1f}%"],
            ['Average Percentage', f"{avg_percentage:.1f}%", 'Pass Percentage', f"{pass_percentage:.1f}%"]
        ]
        
        stats_table = Table(stats_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        stats_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
        ]))
        
        elements.append(Paragraph("Class Statistics", self.styles['CustomSubHeader']))
        elements.append(Spacer(1, 10))
        elements.append(stats_table)
        
        return elements
    
    def _generate_pdf(self, elements: List, organization_data: Dict[str, Any], customization: Dict[str, Any]) -> BytesIO:
        """Generate PDF from elements"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer)
        
        # Add watermark if enabled
        if customization.get('watermark'):
            elements.insert(0, self._create_watermark(customization['watermark']))
        
        # Add QR code if enabled
        if customization.get('qr_data'):
            elements.append(self._create_qr_code(customization['qr_data']))
        
        doc.build(elements)
        return buffer

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from PIL import Image
from io import BytesIO

def generate_result_pdf(student_data, output_path, customization_data=None):
    """Generate PDF result for a student with optional customization"""
    width, height = A4  # Standard A4 size
    c = canvas.Canvas(output_path, pagesize=A4)
    
    # Use simple layout if requested or if no customization data
    if customization_data and not customization_data.get('use_simple_layout', False):
        _generate_custom_layout(c, width, height, student_data, customization_data)
    else:
        _generate_simple_layout(c, width, height, student_data)
    
    c.save()

def _add_image_to_canvas(c, image_path, x, y, max_width, max_height):
    """Helper function to add image to canvas with proper scaling"""
    try:
        with Image.open(image_path) as img:
            # Calculate aspect ratio and new dimensions
            aspect = img.width / img.height
            if aspect > 1:
                width = min(max_width, img.width)
                height = width / aspect
            else:
                height = min(max_height, img.height)
                width = height * aspect
            c.drawImage(image_path, x, y, width=width, height=height, preserveAspectRatio=True)
            return width, height
    except Exception as e:
        print(f"Error processing image {image_path}: {str(e)}")
        return 0, 0

def _generate_simple_layout(c, width, height, student_data):
    """Generate simple PDF layout without customization"""
    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height-30, "Student Result Card")
    
    # Student info
    c.setFont("Helvetica", 12)
    y = height - 60
    c.drawString(50, y, f"Name: {student_data['name']}")
    c.drawString(50, y-20, f"Roll No: {student_data['roll_no']}")
    c.drawString(50, y-40, f"Class: {student_data['cls']}")
    c.drawString(50, y-60, f"Section: {student_data['section']}")
    
    # Results table
    y -= 100
    _draw_results_table(c, student_data['overall_result'], 50, y, width-100)

def _generate_custom_layout(c, width, height, student_data, customization_data):
    """Generate custom PDF layout with images and styling"""
    # Process logo
    logo_width = width * 0.2  # 20% of page width
    logo_height = height * 0.1  # 10% of page height
    
    if customization_data.get('logo'):
        actual_w, actual_h = _add_image_to_canvas(c, customization_data['logo'], 
                                                50, height - logo_height - 50,
                                                logo_width, logo_height)
        logo_width = actual_w  # Update with actual width for text positioning

    # Process student photo if available
    photo_size = min(width * 0.2, height * 0.2)  # 20% of smallest page dimension
    if customization_data.get('student_photo'):
        _add_image_to_canvas(c, customization_data['student_photo'],
                           width - photo_size - 50, height - photo_size - 50,
                           photo_size, photo_size)

    # Add watermark if specified
    if customization_data.get('watermark_type') == 'text' and customization_data.get('watermark_text'):
        c.saveState()
        c.setFillColorRGB(0.9, 0.9, 0.9, alpha=0.3)  # Light gray with transparency
        c.setFont("Helvetica", 60)
        c.translate(width/2, height/2)
        c.rotate(45)
        c.drawCentredString(0, 0, customization_data['watermark_text'])
        c.restoreState()
    elif customization_data.get('watermark_type') == 'image' and customization_data.get('watermark_img'):
        try:
            wm_width = width * 0.5  # 50% of page width
            _add_image_to_canvas(c, customization_data['watermark_img'],
                               width/4, height/4,  # Center the watermark
                               wm_width, wm_width)
        except Exception as e:
            print(f"Error processing watermark image: {str(e)}")

    # Header text with institute name and exam name
    c.setFont("Helvetica-Bold", 16)
    y_offset = height - 40
    if customization_data.get('institute_name'):
        c.drawCentredString(width/2, y_offset, customization_data['institute_name'])
        y_offset -= 25
    if customization_data.get('exam_name'):
        c.drawCentredString(width/2, y_offset, customization_data['exam_name'])
        y_offset -= 35
    
    # Student info with proper positioning
    c.setFont("Helvetica", 12)
    info_x = 50 if not customization_data.get('logo') else 50 + logo_width + 20
    y = height - 120
    
    c.drawString(info_x, y, f"Name: {student_data['name']}")
    c.drawString(info_x, y-20, f"Roll No: {student_data['roll_no']}")
    c.drawString(info_x, y-40, f"Class: {student_data['cls']}")
    c.drawString(info_x, y-60, f"Section: {student_data['section']}")
    
    # Results table
    y -= 100
    _draw_results_table(c, student_data['overall_result'], 50, y, width-100)
    
    # Footer with signatures
    y = 50
    if customization_data.get('principal_name'):
        c.drawString(50, y, f"Principal: {customization_data['principal_name']}")
    if customization_data.get('teacher_name'):
        c.drawString(width-200, y, f"Teacher: {customization_data['teacher_name']}")

def _draw_results_table(c, overall_result, x, y, width):
    """Draw results table with proper spacing"""
    # Table headers
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x, y, "Subject")
    c.drawString(x+150, y, "Marks")
    c.drawString(x+250, y, "Grade")
    
    # Table content
    c.setFont("Helvetica", 12)
    y -= 20
    for subject in overall_result['subject_results']:
        c.drawString(x, y, subject['subject_name'])
        c.drawString(x+150, y, f"{subject['marks']}/{subject['max_marks']}")
        c.drawString(x+250, y, subject['grade'])
        y -= 20
    
    # Overall result
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x, y, f"Overall Grade: {overall_result['overall_grade']}")
    c.drawString(x+250, y, "PASS" if overall_result['is_pass'] else "FAIL")

def generate_class_pdf(class_data, output_path, customization_data=None):
    """Generate PDF for entire class with optional customization"""
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # Similar structure to individual result, but with multiple students per page
    students_per_page = 3
    for i, student in enumerate(class_data['students']):
        if i > 0 and i % students_per_page == 0:
            c.showPage()
        
        # Calculate vertical position for each student
        y_offset = height - (i % students_per_page) * (height/students_per_page) - 50
        
        # Add student data with proper spacing
        _add_student_to_class_pdf(c, student, width, y_offset, customization_data)
    
    c.save()

def _add_student_to_class_pdf(c, student, width, y_offset, customization_data):
    """Add individual student to class PDF"""
    # Add header for each student
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_offset, f"{student['name']} (Roll No: {student['roll_no']})")
    
    # Add results with proper spacing
    y = y_offset - 20
    c.setFont("Helvetica", 10)
    for subject in student['overall_result']['subject_results']:
        c.drawString(50, y, 
                    f"{subject['subject_name']}: {subject['marks']}/{subject['max_marks']} ({subject['grade']})")
        y -= 15
    
    # Add overall grade
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y-10, 
                f"Overall: {student['overall_result']['overall_grade']} "
                f"({'PASS' if student['overall_result']['is_pass'] else 'FAIL'})")

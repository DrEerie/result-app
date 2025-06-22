from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from models.models import db, Student, Subject, Result, init_db, ClassSettings
from utils.grading import calculate_student_overall_result, get_grade_color, get_result_status_color
from utils.pdf_generator import generate_result_pdf, generate_class_pdf
from datetime import datetime
import os
import io

# Add import for Excel export
try:
    import openpyxl
except ImportError:
    openpyxl = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_change_this_in_production'

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'database')
os.makedirs(db_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(db_path, 'result.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Updated and consistent subject mapping for different classes
CLASS_SUBJECTS = {
    'Mont': ['English', 'Math'],
    'Nur': ['English', 'Math', 'Drawing'],
    'KG': ['English', 'Math', 'Science'],
    '1': ['English', 'Math', 'Science', 'Social Studies'],
    '2': ['English', 'Math', 'Science', 'Social Studies'],
    '3': ['English', 'Math', 'Science', 'Social Studies'],
    '4': ['English', 'Math', 'Science', 'Social Studies'],
    '5': ['English', 'Math', 'Science', 'Social Studies'],
    '6': ['English', 'Math', 'Science', 'Social Studies'],
    '7': ['English', 'Math', 'Science', 'Social Studies'],
    '8': ['English', 'Math', 'Science', 'Social Studies'],
    '9': ['Physics', 'Chemistry', 'Math', 'Biology'],
    '10': ['Physics', 'Chemistry', 'Math', 'Biology'],
    '11': ['Physics', 'Chemistry', 'Math', 'Biology'],
    '12': ['Physics', 'Chemistry', 'Math', 'Biology']
}

@app.route('/')
def home():
    # Get stats for dashboard
    with app.app_context():
        total_students = Student.query.count()
        total_results = Result.query.count()
        
        # Get unique classes and subjects
        classes = db.session.query(Student.cls).distinct().count()
        subjects = Subject.query.count()
    
    stats = {
        'total_students': total_students,
        'total_classes': classes,
        'total_subjects': subjects,
        'total_results': total_results
    }
    
    return render_template('home.html', stats=stats)

@app.route('/enter', methods=['GET', 'POST'])
def enter_result():
    if request.method == 'POST':
        try:
            name = request.form.get('student_name', '').strip()
            roll_no = request.form.get('roll_no', '').strip()
            cls = request.form.get('cls', '').strip()
            section = request.form.get('section', '').strip()
            days_present = int(request.form.get('days_present', 0))
            action = request.form.get('action_type', 'insert')

            # Get max_days from class settings
            class_settings = ClassSettings.query.filter_by(class_name=cls).first()
            max_days = class_settings.max_days if class_settings else 200
            
            # Validation
            if not all([name, roll_no, cls, section]):
                flash("All fields are required!", "error")
                return render_template('enter_result.html', prefill=request.form)

            try:
                if days_present < 0 or days_present > max_days:
                    raise ValueError
            except ValueError:
                flash(f"Days present must be between 0 and {max_days}", "error")
                return render_template('enter_result.html', prefill=request.form)
            
            # Check if student exists
            existing_student = Student.query.filter_by(roll_no=roll_no).first()
            
            if existing_student and action == 'insert':
                return render_template('enter_result.html', 
                                     existing_roll=roll_no, 
                                     prefill=request.form)

            # Handle different actions
            if existing_student:
                if action == 'delete':
                    delete_student(existing_student)
                    student = Student(
                        name=name, 
                        roll_no=roll_no, 
                        cls=cls, 
                        section=section,
                        days_present=days_present,
                        max_days=max_days
                    )
                    db.session.add(student)
                elif action == 'overwrite':
                    existing_student.name = name
                    existing_student.cls = cls
                    existing_student.section = section
                    existing_student.days_present = days_present
                    existing_student.max_days = max_days
                    student = existing_student
            else:
                student = Student(
                    name=name, 
                    roll_no=roll_no, 
                    cls=cls, 
                    section=section,
                    days_present=days_present,
                    max_days=max_days
                )
                db.session.add(student)

            db.session.commit()
            
            # Add results
            marks_added = add_results(student, cls, request.form)
            
            if marks_added:
                flash(f"✅ Result for {name} (Roll: {roll_no}) added successfully!", "success")
            else:
                flash("⚠️ Student added but no marks were entered!", "warning")
                
            return redirect(url_for('enter_result'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error: {str(e)}", "error")
            return render_template('enter_result.html', 
                                 class_subjects=CLASS_SUBJECTS,
                                 prefill=request.form)
    
    return render_template('enter_result.html', class_subjects=CLASS_SUBJECTS)

def delete_student(student):
    """Delete student and all their results"""
    Result.query.filter_by(student_id=student.id).delete()
    db.session.delete(student)

def overwrite_student(student, name, cls, section):
    """Update student info and delete old results"""
    Result.query.filter_by(student_id=student.id).delete()
    student.name = name
    student.cls = cls
    student.section = section
    return student

def add_results(student, cls, form_data):
    """Add marks for the student based on their class"""
    marks_added = 0
    
    # Get subjects for this class
    subjects = Subject.query.filter_by(class_name=cls).all()
    
    for subject in subjects:
        marks_key = f"marks_{subject.name.lower().replace(' ', '_')}"
        marks = form_data.get(marks_key, '').strip()
        
        if marks:
            try:
                marks_value = float(marks)
                if 0 <= marks_value <= subject.max_marks:
                    result = Result(
                        student_id=student.id,
                        subject_id=subject.id,
                        marks=marks_value,
                        term='Annual'
                    )
                    db.session.add(result)
                    marks_added += 1
                else:
                    flash(f"⚠️ Marks for {subject.name} should be between 0-{subject.max_marks}", "warning")
            except ValueError:
                flash(f"⚠️ Invalid marks for {subject.name}", "warning")
    
    if marks_added > 0:
        db.session.commit()
    
    return marks_added

@app.route('/view')
def view_results():
    """View all student results with grades and calculations"""
    students = Student.query.all()
    
    # Prepare students data with calculated results
    students_data = []
    for student in students:
        # Get all results for this student
        results = Result.query.filter_by(student_id=student.id).all()
        
        # Calculate overall result using grading system
        overall_result = calculate_student_overall_result(results)
        
        # Add color classes for display
        overall_result['grade_color'] = get_grade_color(overall_result['overall_grade'])
        overall_result['status_color'] = get_result_status_color(overall_result['is_pass'])
        
        # Add color classes to subject results
        for subject in overall_result['subject_results']:
            subject['grade_color'] = get_grade_color(subject['grade'])
        
        # Create student object with results and attendance
        student_data = {
            'id': student.id,
            'name': student.name,
            'roll_no': student.roll_no,
            'cls': student.cls,
            'section': student.section,
            'days_present': student.days_present,
            'max_days': student.max_days,
            'overall_result': overall_result
        }
        
        students_data.append(student_data)
    
    # Sort students by class and roll number
    students_data.sort(key=lambda x: (x['cls'], x['roll_no']))
    
    return render_template('view_result.html', students=students_data)

@app.route('/student/<int:student_id>')
def student_detail(student_id):
    """View detailed result for a specific student"""
    student = Student.query.get_or_404(student_id)
    results = Result.query.filter_by(student_id=student.id).all()
    overall_result = calculate_student_overall_result(results)
    
    # Add color classes
    overall_result['grade_color'] = get_grade_color(overall_result['overall_grade'])
    overall_result['status_color'] = get_result_status_color(overall_result['is_pass'])
    
    for subject in overall_result['subject_results']:
        subject['grade_color'] = get_grade_color(subject['grade'])
    
    return render_template('student_detail.html', 
                         student=student, 
                         overall_result=overall_result)

@app.route('/download_pdf/<int:student_id>')
def download_pdf(student_id):
    """Generate and download PDF result for a student"""
    student = Student.query.get_or_404(student_id)
    results = Result.query.filter_by(student_id=student.id).all()
    overall_result = calculate_student_overall_result(results)
    
    student_data = {
        'name': student.name,
        'roll_no': student.roll_no,
        'cls': student.cls,
        'section': student.section,
        'days_present': student.days_present,
        'max_days': student.max_days,
        'overall_result': overall_result
    }
    
    # Create PDFs directory if it doesn't exist
    pdf_dir = os.path.join(app.static_folder, 'pdfs')
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Generate PDF filename
    filename = f"result_{student.roll_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = os.path.join(pdf_dir, filename)
    
    # Generate PDF
    generate_result_pdf(student_data, pdf_path)
    
    # Send file
    return send_file(pdf_path, as_attachment=True)

@app.route('/bulk_entry', methods=['GET', 'POST'])
def bulk_entry():
    """Handle bulk result entry for a class"""
    if request.method == 'POST':
        cls = request.form.get('cls')
        section = request.form.get('section')
        
        # Get class settings for max_days
        class_settings = ClassSettings.query.filter_by(class_name=cls).first()
        max_days = class_settings.max_days if class_settings else 200
        
        # Get student data from form
        roll_numbers = request.form.getlist('roll_no[]')
        names = request.form.getlist('name[]')
        
        success_count = 0
        for i in range(len(roll_numbers)):
            try:
                # Get attendance for this student
                days_present = int(request.form.get(f'days_present_{i}', 0))
                if days_present < 0 or days_present > max_days:
                    flash(f"Invalid attendance for student {names[i]}", "error")
                    continue
                
                # Create or update student
                student = Student.query.filter_by(roll_no=roll_numbers[i]).first()
                if not student:
                    student = Student(
                        roll_no=roll_numbers[i],
                        name=names[i],
                        cls=cls,
                        section=section,
                        days_present=days_present,
                        max_days=max_days
                    )
                    db.session.add(student)
                    db.session.flush()
                else:
                    student.days_present = days_present
                    student.max_days = max_days
                
                # Add results for each subject
                for subject_name in CLASS_SUBJECTS.get(cls, []):
                    marks_key = f"marks_{i}_{subject_name.lower().replace(' ', '_')}"
                    marks = request.form.get(marks_key)
                    if marks and marks.strip():
                        subject = Subject.query.filter_by(name=subject_name, class_name=cls).first()
                        if subject:
                            result = Result(
                                student_id=student.id,
                                subject_id=subject.id,
                                marks=float(marks),
                                term='Annual'
                            )
                            db.session.add(result)
                success_count += 1
            except Exception as e:
                flash(f"Error adding student {names[i]}: {str(e)}", "error")
                continue
        
        db.session.commit()
        flash(f"Successfully added results for {success_count} students!", "success")
        return redirect(url_for('view_results'))
            
    return render_template('bulk_entry.html', class_subjects=CLASS_SUBJECTS)

@app.route('/class_pdf/<cls>/<section>')
def download_class_pdf(cls, section):
    """Generate and download PDF result for entire class"""
    students = Student.query.filter_by(cls=cls, section=section).all()
    if not students:
        flash("No students found in this class!", "error")
        return redirect(url_for('view_results'))
    
    class_data = {
        'cls': cls,
        'section': section,
        'students': []
    }
    
    for student in students:
        results = Result.query.filter_by(student_id=student.id).all()
        overall_result = calculate_student_overall_result(results)
        class_data['students'].append({
            'name': student.name,
            'roll_no': student.roll_no,
            'days_present': student.days_present,
            'max_days': student.max_days,
            'overall_result': overall_result
        })
    
    # Generate PDF filename
    filename = f"class_{cls}_{section}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_dir = os.path.join(app.static_folder, 'pdfs')
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.join(pdf_dir, filename)
    
    # Generate class PDF
    generate_class_pdf(class_data, pdf_path)
    
    return send_file(pdf_path, as_attachment=True)

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """Clear all results from database"""
    try:
        Result.query.delete()
        Student.query.delete()
        db.session.commit()
        flash("Successfully cleared all result history!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error clearing history: {str(e)}", "error")
    return redirect(url_for('view_results'))

@app.route('/edit/<int:student_id>', methods=['GET', 'POST'])
def edit_result(student_id):
    student = Student.query.get_or_404(student_id)
    results = Result.query.filter_by(student_id=student_id).all()
    
    # Get subjects specific to student's class
    class_subjects = Subject.query.filter_by(class_name=student.cls).all()
    
    if request.method == 'POST':
        try:
            # Update attendance
            days_present = request.form.get('days_present', type=int)
            if days_present is not None:
                if 0 <= days_present <= student.max_days:
                    student.days_present = days_present
                else:
                    flash(f"Days present must be between 0 and {student.max_days}", "error")
                    return redirect(url_for('edit_result', student_id=student_id))

            # Update subject marks
            for subject in class_subjects:
                marks_key = f'marks_{subject.id}'
                marks_str = request.form.get(marks_key, '').strip()
                
                if marks_str:
                    marks = float(marks_str)
                    if 0 <= marks <= subject.max_marks:
                        result = Result.query.filter_by(
                            student_id=student_id,
                            subject_id=subject.id
                        ).first() or Result(
                            student_id=student_id,
                            subject_id=subject.id
                        )
                        result.marks = marks
                        if result.id is None:
                            db.session.add(result)
                    else:
                        flash(f"Marks for {subject.name} must be between 0 and {subject.max_marks}", "error")
                        return redirect(url_for('edit_result', student_id=student_id))
            
            db.session.commit()
            flash("Results updated successfully!", "success")
            return redirect(url_for('view_results'))
            
        except ValueError:
            flash("Invalid values entered", "error")
            return redirect(url_for('edit_result', student_id=student_id))
    
    return render_template('edit_result.html', 
                         student=student, 
                         results=results,
                         all_subjects=class_subjects)  # Pass only class-specific subjects

@app.route('/analytics')
def analytics():
    """Show result analytics with charts"""
    students = Student.query.all()
    subjects = Subject.query.all()
    results = Result.query.all()

    # Calculate attendance statistics
    good_attendance_count = sum(1 for s in students if (s.days_present / s.max_days * 100) >= 75)
    poor_attendance_count = len(students) - good_attendance_count

    # Class-wise average marks
    class_averages = {}
    for student in students:
        student_results = Result.query.filter_by(student_id=student.id).all()
        total = sum(r.marks for r in student_results)
        count = len(student_results)
        if count:
            class_averages.setdefault(student.cls, []).append(total / count)
    
    class_avg_data = [
        {"cls": cls, "avg": round(sum(vals)/len(vals), 2) if vals else 0}
        for cls, vals in class_averages.items()
    ]

    # Subject toppers
    subject_toppers = []
    for subject in subjects:
        top_result = (
            db.session.query(Result, Student)
            .join(Student, Result.student_id == Student.id)
            .filter(Result.subject_id == subject.id)
            .order_by(Result.marks.desc())
            .first()
        )
        if top_result:
            result, student = top_result
            subject_toppers.append({
                "subject": subject.name,
                "student": student.name,
                "marks": result.marks
            })

    # Pass/fail distribution
    pass_count = 0
    fail_count = 0
    for student in students:
        student_results = Result.query.filter_by(student_id=student.id).all()
        overall = calculate_student_overall_result(student_results)
        if overall['is_pass']:
            pass_count += 1
        else:
            fail_count += 1

    return render_template(
        'analytics.html',
        class_avg_data=class_avg_data,
        subject_toppers=subject_toppers,
        pass_count=pass_count,
        fail_count=fail_count,
        good_attendance_count=good_attendance_count,
        poor_attendance_count=poor_attendance_count
    )

@app.route('/export_excel')
def export_excel():
    """Export results with dynamic max marks"""
    if openpyxl is None:
        flash("openpyxl is not installed. Please install it to enable Excel export.", "error")
        return redirect(url_for('view_results'))

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Results"

    # Header
    ws.append([
        "Roll No", "Name", "Class", "Section", 
        "Days Present", "Max Days", "Attendance %",
        "Subject", "Marks Obtained", "Maximum Marks", 
        "Percentage", "Grade", "Status"
    ])

    students = Student.query.all()
    for student in students:
        results = Result.query.filter_by(student_id=student.id).all()
        overall = calculate_student_overall_result(results)
        attendance_percent = (student.days_present / student.max_days * 100)
        
        for subject_result in overall['subject_results']:
            ws.append([
                student.roll_no,
                student.name,
                student.cls,
                student.section,
                student.days_present,
                student.max_days,
                f"{attendance_percent:.1f}%",
                subject_result['subject_name'],
                subject_result['marks'],
                subject_result['max_marks'],
                f"{subject_result['percentage']}%",
                subject_result['grade'],
                "PASS" if subject_result['is_pass'] else "FAIL"
            ])

    # Save to BytesIO and send as file
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="all_results.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route('/customization', methods=['GET', 'POST'])
def customization():
    """Handle customization page (was subject management)"""
    if request.method == 'POST':
        class_name = request.form.get('class_name')
        subject_names = request.form.getlist('subject_names[]')
        max_marks = request.form.getlist('max_marks[]')
        max_days = request.form.get('max_days', 200, type=int)

        try:
            # Update class settings
            settings = ClassSettings.query.filter_by(class_name=class_name).first()
            if not settings:
                settings = ClassSettings(class_name=class_name)
                db.session.add(settings)
            settings.max_days = max_days

            # Remove old subjects for this class
            Subject.query.filter_by(class_name=class_name).delete()

            # Add new subjects
            for name, marks in zip(subject_names, max_marks):
                if name.strip():  # Only add if name is not empty
                    subject = Subject(
                        name=name.strip(),
                        max_marks=float(marks),
                        class_name=class_name
                    )
                    db.session.add(subject)

            db.session.commit()
            flash('Settings and subjects updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating settings: {str(e)}', 'error')

        return redirect(url_for('customization'))

    # For GET request, get all classes and their settings
    classes = list(CLASS_SUBJECTS.keys())
    class_settings = {s.class_name: s.max_days for s in ClassSettings.query.all()}
    
    return render_template('customization.html', 
                         classes=classes,
                         class_settings=class_settings)

# Ensure this route is also present
@app.route('/api/subjects/<class_name>')
def get_class_subjects(class_name):
    """API endpoint to get subjects for a class"""
    try:
        subjects = Subject.query.filter_by(class_name=class_name).all()
        return jsonify([{
            'name': subject.name,
            'max_marks': subject.max_marks
        } for subject in subjects])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/class_settings/<class_name>')
def get_class_settings(class_name):
    """API endpoint to get settings for a class"""
    try:
        settings = ClassSettings.query.filter_by(class_name=class_name).first()
        return jsonify({
            'max_days': settings.max_days if settings else 200
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def init_database():
    """Initialize database with tables and default subjects"""
    with app.app_context():
        try:
            # Only create tables that don't exist
            db.create_all()
            
            # Add default class settings if they don't exist
            for cls in CLASS_SUBJECTS.keys():
                settings = ClassSettings.query.filter_by(class_name=cls).first()
                if not settings:
                    settings = ClassSettings(class_name=cls, max_days=200)
                    db.session.add(settings)
            
            # Add default subjects for each class if they don't exist
            for cls, subjects in CLASS_SUBJECTS.items():
                for subject_name in subjects:
                    existing = Subject.query.filter_by(
                        name=subject_name,
                        class_name=cls
                    ).first()
                    
                    if not existing:
                        subject = Subject(
                            name=subject_name,
                            max_marks=100.0,
                            class_name=cls
                        )
                        db.session.add(subject)
            
            db.session.commit()
            print("Database initialized successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Database initialization failed: {str(e)}")

# API endpoint definitions above...

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/cookies')
def cookies():
    return render_template('cookies.html')

if __name__ == '__main__':
    init_database()
    app.run(debug=True)
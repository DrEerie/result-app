from flask import Flask, render_template, request, redirect, url_for, flash
from models.models import db, Student, Subject, Result
from utils.grading import calculate_student_overall_result, get_grade_color, get_result_status_color
import os

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

def init_database():
    """Initialize database with tables and default subjects"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Add all subjects if they don't exist
        all_subjects = set()
        for subjects in CLASS_SUBJECTS.values():
            all_subjects.update(subjects)
        
        for subject_name in all_subjects:
            if not Subject.query.filter_by(name=subject_name).first():
                subject = Subject(name=subject_name)
                db.session.add(subject)
        
        try:
            db.session.commit()
            print("Database initialized successfully!")
        except Exception as e:
            print(f"Error initializing database: {e}")
            db.session.rollback()

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
            action = request.form.get('action_type', 'insert')
            
            # Validation
            if not all([name, roll_no, cls, section]):
                flash("All fields are required!", "error")
                return render_template('enter_result.html', 
                                     class_subjects=CLASS_SUBJECTS,
                                     prefill=request.form)
            
            # Check if student exists
            existing_student = Student.query.filter_by(roll_no=roll_no).first()
            
            if existing_student and action == 'insert':
                flash(f"Roll number {roll_no} already exists! Choose overwrite or delete.", "warning")
                return render_template('enter_result.html', 
                                     class_subjects=CLASS_SUBJECTS,
                                     existing_roll=roll_no, 
                                     prefill=request.form)
            
            # Handle different actions
            if existing_student:
                if action == 'delete':
                    delete_student(existing_student)
                    student = Student(name=name, roll_no=roll_no, cls=cls, section=section)
                    db.session.add(student)
                elif action == 'overwrite':
                    student = overwrite_student(existing_student, name, cls, section)
                else:
                    student = existing_student
            else:
                student = Student(name=name, roll_no=roll_no, cls=cls, section=section)
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
    
    if cls in CLASS_SUBJECTS:
        for subject_name in CLASS_SUBJECTS[cls]:
            marks_key = f"marks_{subject_name.lower().replace(' ', '_')}"
            marks = form_data.get(marks_key, '').strip()
            
            if marks:
                try:
                    marks_value = float(marks)
                    if 0 <= marks_value <= 100:
                        # Get or create subject
                        subject = Subject.query.filter_by(name=subject_name).first()
                        if not subject:
                            subject = Subject(name=subject_name)
                            db.session.add(subject)
                            db.session.flush()  # Get the ID
                        
                        # Add result
                        result = Result(
                            student_id=student.id,
                            subject_id=subject.id,
                            marks=marks_value,
                            term='Annual',  # Default term
                            session='2024-25'  # Default session
                        )
                        db.session.add(result)
                        marks_added += 1
                    else:
                        flash(f"⚠️ Marks for {subject_name} should be between 0-100", "warning")
                except ValueError:
                    flash(f"⚠️ Invalid marks for {subject_name}", "warning")
    
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
        
        # Create student object with results
        student_data = {
            'id': student.id,
            'name': student.name,
            'roll_no': student.roll_no,
            'cls': student.cls,
            'section': student.section,
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

if __name__ == '__main__':
    init_database()
    app.run(debug=True)
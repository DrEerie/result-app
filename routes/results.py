# routes/results.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, g
from auth.decorators import login_required, role_required
from middleware.subscription import feature_required, usage_tracked
from services.result_service import ResultService
from services.student_service import StudentService
from models.result import Result
from models.student import Student
import json

results_bp = Blueprint('results', __name__)

@results_bp.route('/enter', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher')
@usage_tracked('result_entry')
def enter_result():
    """Single result entry"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        result_data = {
            'student_id': data.get('student_id'),
            'class_name': data.get('class_name'),
            'exam_type': data.get('exam_type'),
            'exam_date': data.get('exam_date'),
            'subjects': json.loads(data.get('subjects', '[]'))
        }
        
        result = ResultService.create_result(result_data, g.organization_id)
        
        if result['success']:
            flash('Result entered successfully!', 'success')
            return redirect(url_for('results.view_results')) if not request.is_json else jsonify({'success': True, 'result_id': result['result'].id})
        else:
            flash(result['error'], 'error')
            return redirect(url_for('results.enter_result')) if not request.is_json else jsonify({'error': result['error']}), 400
    
    # Get students for dropdown
    students = StudentService.get_active_students(g.organization_id)
    return render_template('enter_result.html', students=students)

@results_bp.route('/bulk-entry', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher')
@feature_required('bulk_import')
@usage_tracked('bulk_entry')
def bulk_entry():
    """Bulk result import"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and file.filename.endswith(('.csv', '.xlsx')):
            result = ResultService.bulk_import_results(file, g.organization_id)
            
            if result['success']:
                flash(f'Successfully imported {result["count"]} results', 'success')
                return redirect(url_for('results.view_results'))
            else:
                flash(result['error'], 'error')
        else:
            flash('Please upload a CSV or Excel file', 'error')
    
    return render_template('bulk_entry.html')

@results_bp.route('/view')
@login_required
def view_results():
    """View all results"""
    page = request.args.get('page', 1, type=int)
    class_filter = request.args.get('class')
    exam_filter = request.args.get('exam')
    
    results = ResultService.get_results_paginated(
        g.organization_id, 
        page=page, 
        class_name=class_filter, 
        exam_type=exam_filter
    )
    
    return render_template('view_result.html', results=results)

@results_bp.route('/edit/<int:result_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher')
def edit_result(result_id):
    """Edit result"""
    result = Result.query.filter_by(id=result_id, organization_id=g.organization_id).first_or_404()
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        update_data = {
            'exam_type': data.get('exam_type'),
            'exam_date': data.get('exam_date'),
            'subjects': json.loads(data.get('subjects', '[]'))
        }
        
        updated_result = ResultService.update_result(result_id, update_data, g.organization_id)
        
        if updated_result['success']:
            flash('Result updated successfully!', 'success')
            return redirect(url_for('results.view_results')) if not request.is_json else jsonify({'success': True})
        else:
            flash(updated_result['error'], 'error')
    
    return render_template('edit_result.html', result=result)

@results_bp.route('/student/<int:student_id>')
@login_required
def student_detail(student_id):
    """Individual student result preview"""
    student = Student.query.filter_by(id=student_id, organization_id=g.organization_id).first_or_404()
    results = ResultService.get_student_results(student_id, g.organization_id)
    
    return render_template('student_detail.html', student=student, results=results)

# routes/student.py
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, g
from auth.decorators import login_required, role_required
from services.student_service import StudentService
from models.student import Student

student_bp = Blueprint('student', __name__)

@student_bp.route('/')
@login_required
def list_students():
    """List all students"""
    page = request.args.get('page', 1, type=int)
    class_filter = request.args.get('class')
    search = request.args.get('search')
    
    students = StudentService.get_students_paginated(
        g.organization_id, 
        page=page, 
        class_name=class_filter, 
        search=search
    )
    
    return render_template('students/list.html', students=students)

@student_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher')
def add_student():
    """Add new student"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        student_data = {
            'roll_number': data.get('roll_number'),
            'name': data.get('name'),
            'father_name': data.get('father_name'),
            'class_name': data.get('class_name'),
            'section': data.get('section'),
            'date_of_birth': data.get('date_of_birth'),
            'phone': data.get('phone'),
            'address': data.get('address')
        }
        
        result = StudentService.create_student(student_data, g.organization_id)
        
        if result['success']:
            flash('Student added successfully!', 'success')
            return redirect(url_for('student.list_students')) if not request.is_json else jsonify({'success': True})
        else:
            flash(result['error'], 'error')
    
    return render_template('students/add.html')

@student_bp.route('/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher')
def edit_student(student_id):
    """Edit student"""
    student = Student.query.filter_by(id=student_id, organization_id=g.organization_id).first_or_404()
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        update_data = {
            'name': data.get('name'),
            'father_name': data.get('father_name'),
            'class_name': data.get('class_name'),
            'section': data.get('section'),
            'date_of_birth': data.get('date_of_birth'),
            'phone': data.get('phone'),
            'address': data.get('address')
        }
        
        result = StudentService.update_student(student_id, update_data, g.organization_id)
        
        if result['success']:
            flash('Student updated successfully!', 'success')
            return redirect(url_for('student.list_students')) if not request.is_json else jsonify({'success': True})
        else:
            flash(result['error'], 'error')
    
    return render_template('students/edit.html', student=student)

@student_bp.route('/delete/<int:student_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_student(student_id):
    """Delete student"""
    result = StudentService.delete_student(student_id, g.organization_id)
    
    if result['success']:
        flash('Student deleted successfully!', 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('student.list_students')) if not request.is_json else jsonify(result)

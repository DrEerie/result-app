# routes/export.py
from flask import Blueprint, request, jsonify, send_file, g
from auth.decorators import login_required, role_required
from middleware.subscription import usage_tracked
from services.export_service import ExportService
import tempfile
import os

export_bp = Blueprint('export', __name__)

@export_bp.route('/marksheet/<int:student_id>')
@login_required
@usage_tracked('pdf_generation')
def export_marksheet(student_id):
    """Export individual marksheet"""
    exam_id = request.args.get('exam_id')
    
    result = ExportService.generate_marksheet(student_id, exam_id, g.organization_id)
    
    if result['success']:
        return send_file(
            result['file_path'],
            as_attachment=True,
            download_name=f"marksheet_{student_id}_{exam_id}.pdf",
            mimetype='application/pdf'
        )
    else:
        return jsonify({'error': result['error']}), 400

@export_bp.route('/class-result/<class_name>')
@login_required
@usage_tracked('pdf_generation')
def export_class_result(class_name):
    """Export class result sheet"""
    exam_type = request.args.get('exam_type')
    
    result = ExportService.generate_class_result(class_name, exam_type, g.organization_id)
    
    if result['success']:
        return send_file(
            result['file_path'],
            as_attachment=True,
            download_name=f"class_result_{class_name}_{exam_type}.pdf",
            mimetype='application/pdf'
        )
    else:
        return jsonify({'error': result['error']}), 400

@export_bp.route('/bulk-marksheets')
@login_required
@role_required('admin', 'teacher')
@usage_tracked('bulk_pdf_generation')
def export_bulk_marksheets():
    """Export multiple marksheets"""
    class_name = request.args.get('class')
    exam_type = request.args.get('exam')
    
    result = ExportService.generate_bulk_marksheets(class_name, exam_type, g.organization_id)
    
    if result['success']:
        return send_file(
            result['file_path'],
            as_attachment=True,
            download_name=f"bulk_marksheets_{class_name}_{exam_type}.zip",
            mimetype='application/zip'
        )
    else:
        return jsonify({'error': result['error']}), 400
@export_bp.route('/student-list')
@login_required
@role_required('admin', 'teacher')
@usage_tracked('student_list_export')
def export_student_list():
    """Export student list"""
    result = ExportService.generate_student_list(g.organization_id)

    if result['success']:
        return send_file(
            result['file_path'],
            as_attachment=True,
            download_name="student_list.csv",
            mimetype='text/csv'
        )
    else:
        return jsonify({'error': result['error']}), 400
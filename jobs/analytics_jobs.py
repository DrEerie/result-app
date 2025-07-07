import logging
from datetime import datetime
import os
from celery import shared_task

from services.student_analytics_service import StudentAnalyticsService
from services.pdf_service import PDFService
from models.student import Student
from models.base import db

logger = logging.getLogger(__name__)

@shared_task(name='calculate_student_analytics')
def calculate_student_analytics_task(student_id, organization_id, academic_year, term):
    """Background task to calculate analytics for a student
    
    Args:
        student_id (str): The ID of the student
        organization_id (str): The organization ID for tenant isolation
        academic_year (str): The academic year
        term (str): The term
        
    Returns:
        dict: The calculated analytics
    """
    try:
        logger.info(f"Starting analytics calculation for student {student_id}")
        analytics = StudentAnalyticsService.calculate_student_analytics(
            student_id, organization_id, academic_year, term
        )
        
        if analytics:
            logger.info(f"Successfully calculated analytics for student {student_id}")
            return analytics.to_dict() if hasattr(analytics, 'to_dict') else {'status': 'success'}
        else:
            logger.warning(f"No results found for student {student_id}")
            return {'status': 'no_results'}
    except Exception as e:
        logger.error(f"Error calculating analytics for student {student_id}: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@shared_task(name='calculate_all_student_analytics')
def calculate_all_student_analytics_task(organization_id, academic_year, term, class_name=None):
    """Background task to calculate analytics for all students
    
    Args:
        organization_id (str): The organization ID for tenant isolation
        academic_year (str): The academic year
        term (str): The term
        class_name (str, optional): Filter by class name
        
    Returns:
        dict: Summary of processed students
    """
    try:
        logger.info(f"Starting analytics calculation for all students in org {organization_id}")
        processed = StudentAnalyticsService.calculate_all_student_analytics(
            organization_id, academic_year, term, class_name
        )
        
        logger.info(f"Successfully calculated analytics for {processed} students")
        return {'status': 'success', 'processed': processed}
    except Exception as e:
        logger.error(f"Error calculating analytics for all students: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@shared_task(name='generate_student_report')
def generate_student_report_task(student_id, organization_id, academic_year, term):
    """Background task to generate a PDF report for student analytics
    
    Args:
        student_id (str): The ID of the student
        organization_id (str): The organization ID for tenant isolation
        academic_year (str): The academic year
        term (str): The term
        
    Returns:
        dict: Information about the generated report
    """
    try:
        logger.info(f"Starting PDF report generation for student {student_id}")
        
        # Ensure analytics are calculated and up-to-date
        analytics = StudentAnalyticsService.calculate_student_analytics(
            student_id, organization_id, academic_year, term
        )
        
        if not analytics:
            logger.warning(f"No analytics found for student {student_id}")
            return {'status': 'no_analytics'}
        
        # Get student details
        student = Student.query.filter_by(id=student_id, organization_id=organization_id).first()
        if not student:
            logger.warning(f"Student {student_id} not found")
            return {'status': 'student_not_found'}
        
        # Get comparison data
        comparison = StudentAnalyticsService.get_student_comparison(
            student_id, organization_id, academic_year, term
        )
        
        # Get performance trends
        trends = StudentAnalyticsService.get_student_performance_trends(
            student_id, organization_id, period='12months'
        )
        
        # Prepare data for PDF
        context = {
            'student': student,
            'analytics': analytics,
            'comparison': comparison,
            'trends': trends,
            'academic_year': academic_year,
            'term': term,
            'generated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'organization_id': organization_id
        }
        
        # Generate PDF
        pdf_service = PDFService()
        filename = f"student_report_{student.roll_no}_{academic_year}_{term}.pdf"
        file_path = pdf_service.generate_pdf('analytics_report.html', context, filename)
        
        # Update student analytics with report path
        analytics.report_path = file_path
        db.session.commit()
        
        logger.info(f"Successfully generated PDF report for student {student_id}: {file_path}")
        
        return {
            'status': 'success', 
            'file_path': file_path,
            'filename': os.path.basename(file_path)
        }
    except Exception as e:
        logger.error(f"Error generating PDF report for student {student_id}: {str(e)}")
        return {'status': 'error', 'message': str(e)}

@shared_task(name='schedule_analytics_calculations')
def schedule_analytics_calculations():
    """Scheduled task to trigger analytics calculations for all organizations
    
    This task is intended to be scheduled to run periodically (e.g., nightly)
    to ensure all analytics are up-to-date.
    
    Returns:
        dict: Summary of scheduled tasks
    """
    from models.organization import Organization
    from models.academic_year import AcademicYear
    
    try:
        logger.info("Starting scheduled analytics calculations")
        
        # Get all active organizations
        organizations = Organization.query.filter_by(is_active=True).all()
        scheduled_tasks = 0
        
        for org in organizations:
            # Get current academic year and term for the organization
            current_year = AcademicYear.query.filter_by(
                organization_id=org.id, is_current=True
            ).first()
            
            if not current_year:
                logger.warning(f"No current academic year found for organization {org.id}")
                continue
            
            # Schedule analytics calculation
            calculate_all_student_analytics_task.delay(
                org.id, current_year.name, current_year.current_term
            )
            
            scheduled_tasks += 1
            
        logger.info(f"Scheduled analytics calculations for {scheduled_tasks} organizations")
        return {'status': 'success', 'scheduled_tasks': scheduled_tasks}
    except Exception as e:
        logger.error(f"Error scheduling analytics calculations: {str(e)}")
        return {'status': 'error', 'message': str(e)}
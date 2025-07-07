from datetime import datetime, timedelta
from sqlalchemy import func
import logging

from models.student import Student
from models.result import Result
from models.student_analytics import StudentAnalytics
from models.base import db
from services.base_service import BaseService
from services.cache_service import CacheService
from flask import current_app

logger = logging.getLogger(__name__)
# Initialize cache service with a longer default timeout for analytics data
cache_service = CacheService(default_timeout=3600)  # 1 hour default timeout

class StudentAnalyticsService(BaseService):
    """Service for student-specific analytics and insights
    
    This service provides methods for calculating and retrieving analytics
    data for individual students, including performance metrics, trends,
    and personalized recommendations.
    """
    
    @staticmethod
    def calculate_student_analytics(student_id, organization_id, academic_year, term):
        """Calculate comprehensive analytics for a specific student
        
        Args:
            student_id (UUID): The ID of the student
            organization_id (UUID): The organization ID for tenant isolation
            academic_year (str): The academic year (e.g., "2023-2024")
            term (str): The term (e.g., "First Term", "Annual")
            
        Returns:
            StudentAnalytics: The calculated analytics object
        """
        # Use caching for expensive calculations
        cache_key = f"student_analytics:{organization_id}:{student_id}:{academic_year}:{term}"
        cached = cache_service.get(cache_key)
        if cached:
            logger.info(f"Retrieved student analytics from cache for {student_id}")
            return cached
            
        # Get student and results
        student = Student.query.filter_by(id=student_id, organization_id=organization_id).first_or_404()
        results = Result.query.filter_by(
            student_id=student_id, 
            organization_id=organization_id,
            academic_year=academic_year,
            term=term
        ).all()
        
        if not results:
            logger.warning(f"No results found for student {student_id} in {academic_year} {term}")
            return None
            
        # Calculate average marks
        avg_marks = sum(r.marks for r in results) / len(results) if results else 0
        
        # Calculate rank in class
        class_results = db.session.query(
            Student.id,
            func.avg(Result.marks).label('avg_marks')
        ).join(Result).filter(
            Student.class_name == student.class_name,
            Student.section == student.section,
            Student.organization_id == organization_id,
            Result.academic_year == academic_year,
            Result.term == term
        ).group_by(Student.id).order_by(func.avg(Result.marks).desc()).all()
        
        # Find student's rank
        rank = next((i+1 for i, r in enumerate(class_results) if r[0] == student_id), 0)
        
        # Calculate improvement from previous term
        prev_term = StudentAnalyticsService._get_previous_term(term)
        prev_year = academic_year
        if not prev_term:
            # If no previous term in current year, check previous year's annual results
            try:
                prev_year = str(int(academic_year) - 1)
            except ValueError:
                # Handle academic years like "2023-2024"
                if '-' in academic_year:
                    year = academic_year.split('-')[0]
                    prev_year = f"{int(year)-1}-{int(year)}"
            prev_term = 'Annual'
            
        prev_results = Result.query.filter_by(
            student_id=student_id, 
            organization_id=organization_id,
            academic_year=prev_year,
            term=prev_term
        ).all()
        
        prev_avg = sum(r.marks for r in prev_results) / len(prev_results) if prev_results else 0
        improvement = ((avg_marks - prev_avg) / prev_avg * 100) if prev_avg > 0 else 0
        
        # Identify strengths and weaknesses
        subject_scores = {}
        for r in results:
            subject = r.subject.name if hasattr(r, 'subject') and r.subject else f"Subject ID: {r.subject_id}"
            subject_scores[subject] = r.marks
            
        # Sort subjects by marks
        sorted_subjects = sorted(subject_scores.items(), key=lambda x: x[1], reverse=True)
        strengths = [s[0] for s in sorted_subjects[:3] if s[1] >= 60]  # Top 3 subjects with good marks
        weaknesses = [s[0] for s in sorted_subjects[-3:] if s[1] < 60]  # Bottom 3 subjects with poor marks
        
        # Generate recommendations
        recommendations = StudentAnalyticsService._generate_recommendations(
            student, sorted_subjects, improvement, student.total_attendance
        )
        
        # Create or update analytics record
        analytics = StudentAnalytics.query.filter_by(
            student_id=student_id,
            organization_id=organization_id,
            academic_year=academic_year,
            term=term
        ).first()
        
        if not analytics:
            analytics = StudentAnalytics(
                student_id=student_id,
                organization_id=organization_id,
                academic_year=academic_year,
                term=term
            )
            
        analytics.average_marks = avg_marks
        analytics.rank_in_class = rank
        analytics.attendance_percentage = student.total_attendance
        analytics.improvement_percentage = improvement
        analytics.strengths = strengths
        analytics.weaknesses = weaknesses
        analytics.recommendations = recommendations
        analytics.last_calculated = datetime.utcnow()
        
        try:
            db.session.add(analytics)
            db.session.commit()
            logger.info(f"Calculated and saved analytics for student {student_id}")
            
            # Cache the result
            cache_service.set(cache_key, analytics.to_dict(), timeout=3600)  # 1 hour cache
            
            return analytics
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving student analytics: {str(e)}")
            raise
    
    @staticmethod
    def _get_previous_term(term):
        """Get the previous term in sequence
        
        Args:
            term (str): The current term
            
        Returns:
            str: The previous term, or None if there is no previous term
        """
        terms = ['First Term', 'Second Term', 'Third Term', 'Annual']
        try:
            idx = terms.index(term)
            return terms[idx-1] if idx > 0 else None
        except ValueError:
            # Handle custom terms
            if term == 'Half Yearly':
                return 'First Term'
            return None
    
    @staticmethod
    def _generate_recommendations(student, sorted_subjects, improvement, attendance):
        """Generate personalized recommendations based on performance
        
        Args:
            student (Student): The student object
            sorted_subjects (list): List of (subject, marks) tuples sorted by marks
            improvement (float): Percentage improvement from previous term
            attendance (float): Attendance percentage
            
        Returns:
            str: Personalized recommendations
        """
        recommendations = []
        
        # Check for weak subjects
        weak_subjects = [s for s, m in sorted_subjects if m < 40]
        if weak_subjects:
            if len(weak_subjects) > 2:
                recommendations.append(f"Focus on improving {', '.join(weak_subjects[:3])}")
            else:
                recommendations.append(f"Focus on improving {', '.join(weak_subjects)}")
        
        # Check attendance
        if attendance < 75:
            recommendations.append("Improve attendance to enhance overall performance")
        
        # Check improvement
        if improvement < -5:
            recommendations.append("Performance has declined compared to previous term. Consider additional support.")
        elif improvement > 10:
            recommendations.append("Excellent improvement from previous term. Keep up the good work!")
        
        # Check overall performance
        avg_mark = sum(m for _, m in sorted_subjects) / len(sorted_subjects) if sorted_subjects else 0
        if avg_mark < 35:
            recommendations.append("Overall performance needs significant improvement across all subjects.")
        elif avg_mark > 85:
            recommendations.append("Outstanding performance! Consider participating in academic competitions.")
        
        # Add general recommendations
        if not recommendations:
            recommendations.append("Continue with consistent performance across all subjects")
        
        return "\n".join(recommendations)
    
    @staticmethod
    def get_student_performance_trends(student_id, organization_id, period='12months'):
        """Get performance trends for a student over time
        
        Args:
            student_id (UUID): The ID of the student
            organization_id (UUID): The organization ID for tenant isolation
            period (str): The period to analyze ('6months', '12months', 'all')
            
        Returns:
            list: List of trend data points
        """
        # Determine time period
        months = 12
        if period == '6months':
            months = 6
        elif period == '3months':
            months = 3
        elif period == 'all':
            months = 60  # 5 years should cover all data
            
        cutoff = datetime.utcnow() - timedelta(days=30*months)
        
        # Get results for the period
        results = Result.query.filter_by(
            student_id=student_id, 
            organization_id=organization_id
        ).filter(Result.created_at >= cutoff).all()
        
        if not results:
            logger.warning(f"No results found for student {student_id} in the specified period")
            return []
        
        # Group by month and subject
        trends = {}
        for r in results:
            month = r.created_at.strftime('%Y-%m')
            subject = r.subject.name if hasattr(r, 'subject') and r.subject else f"Subject ID: {r.subject_id}"
            
            if month not in trends:
                trends[month] = {}
                
            if subject not in trends[month]:
                trends[month][subject] = []
                
            trends[month][subject].append(r.marks)
        
        # Calculate averages
        trend_data = []
        for month in sorted(trends.keys()):
            month_data = {'month': month, 'subjects': {}}
            for subject, marks in trends[month].items():
                month_data['subjects'][subject] = sum(marks) / len(marks) if marks else 0
            
            # Calculate overall average for the month
            all_marks = [mark for subject_marks in trends[month].values() for mark in subject_marks]
            month_data['average'] = sum(all_marks) / len(all_marks) if all_marks else 0
            
            trend_data.append(month_data)
        
        return trend_data
    
    @staticmethod
    def get_student_comparison(student_id, organization_id, academic_year, term):
        """Compare student performance with class averages
        
        Args:
            student_id (UUID): The ID of the student
            organization_id (UUID): The organization ID for tenant isolation
            academic_year (str): The academic year
            term (str): The term
            
        Returns:
            dict: Comparison data
        """
        # Get student
        student = Student.query.filter_by(id=student_id, organization_id=organization_id).first_or_404()
        
        # Get student's results
        student_results = Result.query.filter_by(
            student_id=student_id, 
            organization_id=organization_id,
            academic_year=academic_year,
            term=term
        ).all()
        
        if not student_results:
            logger.warning(f"No results found for student {student_id} in {academic_year} {term}")
            return {}
        
        # Get class results
        class_results = Result.query.join(Student).filter(
            Student.class_name == student.class_name,
            Student.section == student.section,
            Student.organization_id == organization_id,
            Result.academic_year == academic_year,
            Result.term == term
        ).all()
        
        # Group results by subject
        comparison = {}
        for r in student_results:
            subject = r.subject.name if hasattr(r, 'subject') and r.subject else f"Subject ID: {r.subject_id}"
            
            # Get all class results for this subject
            subject_results = [cr for cr in class_results 
                              if (hasattr(cr, 'subject') and cr.subject and cr.subject.name == subject) 
                              or cr.subject_id == r.subject_id]
            
            # Calculate class average
            class_avg = sum(cr.marks for cr in subject_results) / len(subject_results) if subject_results else 0
            
            # Calculate percentile
            if subject_results:
                marks_sorted = sorted([cr.marks for cr in subject_results])
                rank = marks_sorted.index(r.marks) if r.marks in marks_sorted else 0
                percentile = (rank / len(marks_sorted)) * 100
            else:
                percentile = 0
            
            comparison[subject] = {
                'student_marks': r.marks,
                'class_average': class_avg,
                'percentile': percentile,
                'difference': r.marks - class_avg
            }
        
        # Calculate overall comparison
        student_avg = sum(r.marks for r in student_results) / len(student_results) if student_results else 0
        class_avg = sum(r.marks for r in class_results) / len(class_results) if class_results else 0
        
        comparison['overall'] = {
            'student_average': student_avg,
            'class_average': class_avg,
            'difference': student_avg - class_avg
        }
        
        return comparison
    
    @staticmethod
    def get_student_analytics_summary(student_id, organization_id):
        """Get a summary of student analytics across all terms
        
        Args:
            student_id (UUID): The ID of the student
            organization_id (UUID): The organization ID for tenant isolation
            
        Returns:
            dict: Summary data
        """
        # Get student
        student = Student.query.filter_by(id=student_id, organization_id=organization_id).first_or_404()
        
        # Get all analytics records for the student
        analytics = StudentAnalytics.query.filter_by(
            student_id=student_id,
            organization_id=organization_id
        ).order_by(StudentAnalytics.academic_year, StudentAnalytics.term).all()
        
        if not analytics:
            logger.warning(f"No analytics found for student {student_id}")
            return {
                'student': student.to_dict() if hasattr(student, 'to_dict') else {'id': str(student.id), 'name': student.name},
                'analytics': []
            }
        
        # Format analytics data
        analytics_data = [a.to_dict() for a in analytics]
        
        # Calculate improvement trend
        improvement_trend = [a.improvement_percentage for a in analytics if a.improvement_percentage is not None]
        avg_improvement = sum(improvement_trend) / len(improvement_trend) if improvement_trend else 0
        
        # Get consistent strengths and weaknesses
        all_strengths = [s for a in analytics if a.strengths for s in a.strengths]
        all_weaknesses = [w for a in analytics if a.weaknesses for w in a.weaknesses]
        
        # Count occurrences
        strength_counts = {}
        for s in all_strengths:
            strength_counts[s] = strength_counts.get(s, 0) + 1
            
        weakness_counts = {}
        for w in all_weaknesses:
            weakness_counts[w] = weakness_counts.get(w, 0) + 1
            
        # Get top consistent strengths and weaknesses
        consistent_strengths = sorted(strength_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        consistent_weaknesses = sorted(weakness_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            'student': student.to_dict() if hasattr(student, 'to_dict') else {'id': str(student.id), 'name': student.name},
            'analytics': analytics_data,
            'avg_improvement': avg_improvement,
            'consistent_strengths': [s[0] for s in consistent_strengths],
            'consistent_weaknesses': [w[0] for w in consistent_weaknesses],
            'latest': analytics[-1].to_dict() if analytics else None
        }
    
    @staticmethod
    def generate_student_report_pdf(student_id, organization_id, academic_year, term):
        """Generate a PDF report for student analytics
        
        This method queues a background job to generate the report asynchronously.
        
        Args:
            student_id (UUID): The ID of the student
            organization_id (UUID): The organization ID for tenant isolation
            academic_year (str): The academic year
            term (str): The term
            
        Returns:
            dict: Task information
        """
        # Import here to avoid circular imports
        from jobs.analytics_jobs import generate_student_report_task
        
        # Queue the task
        task = generate_student_report_task.delay(student_id, organization_id, academic_year, term)
        logger.info(f"Queued PDF report generation for student {student_id}, task ID: {task.id}")
        
        return {'task_id': str(task.id)}
    
    @staticmethod
    def calculate_all_student_analytics(organization_id, academic_year, term, class_name=None):
        """Calculate analytics for all students in an organization
        
        This method is intended to be run as a background job.
        
        Args:
            organization_id (UUID): The organization ID for tenant isolation
            academic_year (str): The academic year
            term (str): The term
            class_name (str, optional): Filter by class name
            
        Returns:
            int: Number of students processed
        """
        # Get all students
        query = Student.query.filter_by(organization_id=organization_id, is_active=True)
        if class_name:
            query = query.filter_by(class_name=class_name)
            
        students = query.all()
        processed = 0
        
        for student in students:
            try:
                StudentAnalyticsService.calculate_student_analytics(
                    student.id, organization_id, academic_year, term
                )
                processed += 1
            except Exception as e:
                logger.error(f"Error calculating analytics for student {student.id}: {str(e)}")
                continue
                
        logger.info(f"Processed analytics for {processed} students")
        return processed
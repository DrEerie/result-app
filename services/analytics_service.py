# services/analytics_service.py
from typing import Dict, Any, List, Optional
from sqlalchemy import func, case, and_, extract
from models.result import Result
from models.student import Student
from models.subject import Subject
from models.base import db
from services.base_service import BaseService
from datetime import datetime, timedelta

class AnalyticsService(BaseService):
    """Service for analytics and statistics aggregation"""

    @staticmethod
    def get_performance_summary(organization_id: int, class_name: Optional[str] = None, exam_type: Optional[str] = None) -> Dict[str, Any]:
        """Return class-wise average, pass/fail counts, and subject toppers"""
        query = db.session.query(Result).join(Student).filter(Student.organization_id == organization_id)
        if class_name:
            query = query.filter(Student.class_name == class_name)
        if exam_type:
            query = query.filter(Result.exam_type == exam_type)
        results = query.all()

        # Class average
        if results:
            avg_marks = sum(r.total_marks for r in results) / len(results)
        else:
            avg_marks = 0

        # Pass/fail counts
        pass_count = sum(1 for r in results if getattr(r, 'is_pass', False))
        fail_count = len(results) - pass_count

        # Subject toppers
        subject_toppers = []
        if results:
            # Group by subject
            subject_map = {}
            for r in results:
                for subj in r.subjects or []:
                    name = subj.get('name')
                    marks = subj.get('marks', 0)
                    if name not in subject_map or marks > subject_map[name]['marks']:
                        subject_map[name] = {'student': r.student.name, 'marks': marks, 'subject': name}
            subject_toppers = list(subject_map.values())

        return {
            'class_avg': avg_marks,
            'pass_count': pass_count,
            'fail_count': fail_count,
            'subject_toppers': subject_toppers
        }

    @staticmethod
    def get_grade_distribution(organization_id: int, class_name: Optional[str] = None, subject: Optional[str] = None) -> Dict[str, int]:
        """Return grade distribution for a class/subject"""
        query = db.session.query(Result).join(Student).filter(Student.organization_id == organization_id)
        if class_name:
            query = query.filter(Student.class_name == class_name)
        if subject:
            query = query.filter(Result.subjects.any(name=subject))
        results = query.all()
        grade_counts = {'A+': 0, 'A': 0, 'B+': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        for r in results:
            grade = getattr(r, 'grade', 'F')
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        return grade_counts

    @staticmethod
    def get_performance_trends(organization_id: int, class_name: Optional[str] = None, period: str = '6months') -> List[Dict[str, Any]]:
        """Return average marks trend over time (monthly)"""
        months = 6
        if period == '12months':
            months = 12
        cutoff = datetime.utcnow() - timedelta(days=30*months)
        query = db.session.query(Result).join(Student).filter(Student.organization_id == organization_id, Result.created_at >= cutoff)
        if class_name:
            query = query.filter(Student.class_name == class_name)
        results = query.all()
        # Group by month
        trends = {}
        for r in results:
            month = r.created_at.strftime('%Y-%m')
            if month not in trends:
                trends[month] = []
            trends[month].append(r.total_marks)
        trend_list = []
        for month in sorted(trends.keys()):
            avg = sum(trends[month]) / len(trends[month]) if trends[month] else 0
            trend_list.append({'month': month, 'average': avg})
        return trend_list

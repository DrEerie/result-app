import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from services.student_analytics_service import StudentAnalyticsService
from models.student_analytics import StudentAnalytics
from models.student import Student
from models.result import Result
from models.attendance import Attendance


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    session = MagicMock()
    return session


@pytest.fixture
def mock_cache_service():
    """Create a mock cache service"""
    cache_service = MagicMock()
    return cache_service


@pytest.fixture
def student_analytics_service(mock_db_session, mock_cache_service):
    """Create a StudentAnalyticsService instance with mock dependencies"""
    service = StudentAnalyticsService(db_session=mock_db_session, cache_service=mock_cache_service)
    return service


@pytest.fixture
def sample_student():
    """Create a sample student for testing"""
    student = Student(
        id=1,
        organization_id=1,
        roll_no="S001",
        name="Test Student",
        class_name="10",
        section="A",
        gender="Male",
        date_of_birth=datetime.now() - timedelta(days=365 * 15),  # 15 years old
        admission_date=datetime.now() - timedelta(days=365),
        guardian_name="Test Guardian",
        guardian_phone="1234567890",
        address="Test Address",
        is_active=True,
        student_id="TS001",
        created_by=1
    )
    return student


@pytest.fixture
def sample_results():
    """Create sample results for testing"""
    results = [
        Result(
            id=1,
            organization_id=1,
            student_id=1,
            subject_id=1,
            term="Term1",
            academic_year="2023-2024",
            marks=85,
            max_marks=100,
            grade="A",
            remarks="Good performance",
            exam_date=datetime.now() - timedelta(days=30),
            entered_by=1
        ),
        Result(
            id=2,
            organization_id=1,
            student_id=1,
            subject_id=2,
            term="Term1",
            academic_year="2023-2024",
            marks=75,
            max_marks=100,
            grade="B",
            remarks="Average performance",
            exam_date=datetime.now() - timedelta(days=30),
            entered_by=1
        ),
        Result(
            id=3,
            organization_id=1,
            student_id=1,
            subject_id=3,
            term="Term1",
            academic_year="2023-2024",
            marks=90,
            max_marks=100,
            grade="A+",
            remarks="Excellent performance",
            exam_date=datetime.now() - timedelta(days=30),
            entered_by=1
        ),
        # Previous term results for comparison
        Result(
            id=4,
            organization_id=1,
            student_id=1,
            subject_id=1,
            term="Term4",
            academic_year="2022-2023",
            marks=80,
            max_marks=100,
            grade="A",
            remarks="Good performance",
            exam_date=datetime.now() - timedelta(days=120),
            entered_by=1
        ),
    ]
    return results


@pytest.fixture
def sample_attendance():
    """Create sample attendance records for testing"""
    attendance_records = [
        Attendance(
            id=1,
            organization_id=1,
            student_id=1,
            date=datetime.now() - timedelta(days=1),
            status="present",
            remarks="",
            recorded_by=1
        ),
        Attendance(
            id=2,
            organization_id=1,
            student_id=1,
            date=datetime.now() - timedelta(days=2),
            status="present",
            remarks="",
            recorded_by=1
        ),
        Attendance(
            id=3,
            organization_id=1,
            student_id=1,
            date=datetime.now() - timedelta(days=3),
            status="absent",
            remarks="Sick leave",
            recorded_by=1
        ),
        Attendance(
            id=4,
            organization_id=1,
            student_id=1,
            date=datetime.now() - timedelta(days=4),
            status="present",
            remarks="",
            recorded_by=1
        ),
    ]
    return attendance_records


@pytest.fixture
def sample_class_results():
    """Create sample class results for testing"""
    class_results = [
        # Student 1 (our test student)
        Result(
            id=1,
            organization_id=1,
            student_id=1,
            subject_id=1,
            term="Term1",
            academic_year="2023-2024",
            marks=85,
            max_marks=100,
            grade="A",
            exam_date=datetime.now() - timedelta(days=30),
        ),
        # Student 2
        Result(
            id=5,
            organization_id=1,
            student_id=2,
            subject_id=1,
            term="Term1",
            academic_year="2023-2024",
            marks=90,
            max_marks=100,
            grade="A+",
            exam_date=datetime.now() - timedelta(days=30),
        ),
        # Student 3
        Result(
            id=6,
            organization_id=1,
            student_id=3,
            subject_id=1,
            term="Term1",
            academic_year="2023-2024",
            marks=70,
            max_marks=100,
            grade="B",
            exam_date=datetime.now() - timedelta(days=30),
        ),
    ]
    return class_results


@pytest.fixture
def sample_student_analytics():
    """Create a sample StudentAnalytics object"""
    analytics = StudentAnalytics(
        id=1,
        organization_id=1,
        student_id=1,
        academic_year="2023-2024",
        term="Term1",
        average_marks=83.33,
        rank_in_class=2,
        attendance_percentage=75.0,
        improvement_percentage=5.0,
        strengths=["Mathematics", "Science"],
        weaknesses=["History"],
        recommendations="Focus more on History. Continue good work in Mathematics and Science.",
        last_calculated=datetime.now()
    )
    return analytics


def test_calculate_student_analytics(student_analytics_service, sample_student, sample_results, sample_attendance, sample_class_results, mock_db_session):
    """Test the calculate_student_analytics method"""
    # Mock the database queries
    mock_db_session.query.return_value.filter.return_value.all.side_effect = [
        sample_results,  # Current term results
        [sample_results[3]],  # Previous term results
        sample_attendance,  # Attendance records
        sample_class_results,  # Class results for ranking
    ]
    
    # Mock the get_student method
    student_analytics_service.get_student = MagicMock(return_value=sample_student)
    
    # Call the method
    analytics = student_analytics_service.calculate_student_analytics(
        organization_id=1,
        student_id=1,
        academic_year="2023-2024",
        term="Term1"
    )
    
    # Assertions
    assert analytics is not None
    assert analytics.student_id == 1
    assert analytics.academic_year == "2023-2024"
    assert analytics.term == "Term1"
    assert round(analytics.average_marks, 2) == 83.33  # (85 + 75 + 90) / 3
    assert analytics.rank_in_class == 2  # Based on sample_class_results
    assert analytics.attendance_percentage == 75.0  # 3 present out of 4
    assert analytics.improvement_percentage > 0  # Current avg > previous avg
    assert len(analytics.strengths) > 0
    assert len(analytics.weaknesses) > 0
    assert analytics.recommendations is not None
    assert analytics.last_calculated is not None


def test_get_student_analytics(student_analytics_service, sample_student_analytics, mock_db_session, mock_cache_service):
    """Test the get_student_analytics method"""
    # Mock the cache service
    mock_cache_service.get.return_value = None
    
    # Mock the database query
    mock_db_session.query.return_value.filter.return_value.first.return_value = sample_student_analytics
    
    # Call the method
    analytics = student_analytics_service.get_student_analytics(
        organization_id=1,
        student_id=1,
        academic_year="2023-2024",
        term="Term1"
    )
    
    # Assertions
    assert analytics is not None
    assert analytics.student_id == 1
    assert analytics.academic_year == "2023-2024"
    assert analytics.term == "Term1"
    assert round(analytics.average_marks, 2) == 83.33
    assert analytics.rank_in_class == 2
    assert analytics.attendance_percentage == 75.0
    assert analytics.improvement_percentage == 5.0
    assert "Mathematics" in analytics.strengths
    assert "History" in analytics.weaknesses
    assert "Focus more on History" in analytics.recommendations
    
    # Verify cache was set
    mock_cache_service.set.assert_called_once()


def test_get_student_analytics_from_cache(student_analytics_service, sample_student_analytics, mock_cache_service):
    """Test retrieving student analytics from cache"""
    # Mock the cache service to return cached data
    mock_cache_service.get.return_value = sample_student_analytics.to_dict()
    
    # Call the method
    analytics = student_analytics_service.get_student_analytics(
        organization_id=1,
        student_id=1,
        academic_year="2023-2024",
        term="Term1"
    )
    
    # Assertions
    assert analytics is not None
    assert analytics.student_id == 1
    assert analytics.academic_year == "2023-2024"
    assert analytics.term == "Term1"
    assert round(analytics.average_marks, 2) == 83.33
    
    # Verify database was not queried
    student_analytics_service.db_session.query.assert_not_called()


def test_get_performance_trends(student_analytics_service, mock_db_session):
    """Test the get_performance_trends method"""
    # Mock data for trends
    trend_data = [
        {"month": "Jan", "average": 75.0},
        {"month": "Feb", "average": 78.0},
        {"month": "Mar", "average": 80.0},
        {"month": "Apr", "average": 83.0},
    ]
    
    # Mock the database query result
    mock_result = MagicMock()
    mock_result.label.return_value = "month"
    mock_result.scalar.return_value = "average"
    mock_db_session.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = trend_data
    
    # Call the method
    trends = student_analytics_service.get_performance_trends(
        organization_id=1,
        student_id=1,
        academic_year="2023-2024"
    )
    
    # Assertions
    assert trends is not None
    assert len(trends) == 4
    assert trends[0]["month"] == "Jan"
    assert trends[0]["average"] == 75.0
    assert trends[-1]["month"] == "Apr"
    assert trends[-1]["average"] == 83.0


def test_get_student_comparison(student_analytics_service, mock_db_session):
    """Test the get_student_comparison method"""
    # Mock data for student results
    student_results = [
        {"subject_name": "Mathematics", "marks": 85.0},
        {"subject_name": "Science", "marks": 90.0},
        {"subject_name": "History", "marks": 75.0},
    ]
    
    # Mock data for class averages
    class_averages = [
        {"subject_name": "Mathematics", "average": 80.0},
        {"subject_name": "Science", "average": 82.0},
        {"subject_name": "History", "average": 78.0},
    ]
    
    # Mock the database queries
    mock_db_session.query.return_value.join.return_value.filter.return_value.all.side_effect = [
        student_results,
        class_averages,
    ]
    
    # Call the method
    comparison = student_analytics_service.get_student_comparison(
        organization_id=1,
        student_id=1,
        class_name="10",
        section="A",
        academic_year="2023-2024",
        term="Term1"
    )
    
    # Assertions
    assert comparison is not None
    assert "Mathematics" in comparison
    assert comparison["Mathematics"]["student_marks"] == 85.0
    assert comparison["Mathematics"]["class_average"] == 80.0
    assert comparison["Mathematics"]["difference"] == 5.0
    
    assert "Science" in comparison
    assert comparison["Science"]["student_marks"] == 90.0
    assert comparison["Science"]["class_average"] == 82.0
    assert comparison["Science"]["difference"] == 8.0
    
    assert "History" in comparison
    assert comparison["History"]["student_marks"] == 75.0
    assert comparison["History"]["class_average"] == 78.0
    assert comparison["History"]["difference"] == -3.0
    
    assert "overall" in comparison
    assert comparison["overall"]["student_average"] == 83.33  # (85 + 90 + 75) / 3
    assert comparison["overall"]["class_average"] == 80.0  # (80 + 82 + 78) / 3
    assert comparison["overall"]["difference"] == 3.33


def test_get_analytics_summary(student_analytics_service, mock_db_session):
    """Test the get_analytics_summary method"""
    # Mock data for analytics summary
    analytics_data = [
        StudentAnalytics(
            id=1,
            organization_id=1,
            student_id=1,
            academic_year="2023-2024",
            term="Term1",
            average_marks=83.33,
            rank_in_class=2,
            attendance_percentage=75.0,
            improvement_percentage=5.0,
            strengths=["Mathematics", "Science"],
            weaknesses=["History"],
            recommendations="Focus more on History.",
            last_calculated=datetime.now()
        ),
        StudentAnalytics(
            id=2,
            organization_id=1,
            student_id=1,
            academic_year="2023-2024",
            term="Term2",
            average_marks=85.0,
            rank_in_class=1,
            attendance_percentage=80.0,
            improvement_percentage=2.0,
            strengths=["Mathematics", "Science", "History"],
            weaknesses=[],
            recommendations="Continue good work in all subjects.",
            last_calculated=datetime.now()
        ),
    ]
    
    # Mock the database query
    mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = analytics_data
    
    # Call the method
    summary = student_analytics_service.get_analytics_summary(
        organization_id=1,
        student_id=1,
        academic_year="2023-2024"
    )
    
    # Assertions
    assert summary is not None
    assert len(summary) == 2
    
    assert summary[0]["term"] == "Term1"
    assert round(summary[0]["average_marks"], 2) == 83.33
    assert summary[0]["rank_in_class"] == 2
    
    assert summary[1]["term"] == "Term2"
    assert summary[1]["average_marks"] == 85.0
    assert summary[1]["rank_in_class"] == 1
    assert summary[1]["improvement_percentage"] == 2.0


@patch('services.pdf_service.generate_pdf')
def test_generate_student_report(mock_generate_pdf, student_analytics_service, sample_student, sample_student_analytics, mock_db_session):
    """Test the generate_student_report method"""
    # Mock data
    mock_db_session.query.return_value.filter.return_value.first.side_effect = [
        sample_student,
        sample_student_analytics,
    ]
    
    # Mock the get_student_comparison method
    comparison_data = {
        "Mathematics": {"student_marks": 85.0, "class_average": 80.0, "difference": 5.0},
        "Science": {"student_marks": 90.0, "class_average": 82.0, "difference": 8.0},
        "History": {"student_marks": 75.0, "class_average": 78.0, "difference": -3.0},
        "overall": {"student_average": 83.33, "class_average": 80.0, "difference": 3.33, "total_students": 30},
    }
    student_analytics_service.get_student_comparison = MagicMock(return_value=comparison_data)
    
    # Mock the get_performance_trends method
    trends_data = [
        {"month": "Jan", "average": 75.0},
        {"month": "Feb", "average": 78.0},
        {"month": "Mar", "average": 80.0},
        {"month": "Apr", "average": 83.0},
    ]
    student_analytics_service.get_performance_trends = MagicMock(return_value=trends_data)
    
    # Mock the PDF generation
    mock_generate_pdf.return_value = "/tmp/student_report.pdf"
    
    # Call the method
    report_path = student_analytics_service.generate_student_report(
        organization_id=1,
        student_id=1,
        academic_year="2023-2024",
        term="Term1"
    )
    
    # Assertions
    assert report_path == "/tmp/student_report.pdf"
    mock_generate_pdf.assert_called_once()
    
    # Verify the template and context were correct
    template_name = mock_generate_pdf.call_args[0][0]
    context = mock_generate_pdf.call_args[0][1]
    
    assert template_name == "dashboard/analytics_report.html"
    assert context["student"] == sample_student
    assert context["analytics"] == sample_student_analytics
    assert context["comparison"] == comparison_data
    assert context["trends"] == trends_data
    assert context["academic_year"] == "2023-2024"
    assert context["term"] == "Term1"
    assert "generated_at" in context


def test_calculate_all_student_analytics(student_analytics_service, mock_db_session):
    """Test the calculate_all_student_analytics method"""
    # Mock data for students
    students = [
        Student(id=1, organization_id=1, name="Student 1"),
        Student(id=2, organization_id=1, name="Student 2"),
        Student(id=3, organization_id=1, name="Student 3"),
    ]
    
    # Mock the database query
    mock_db_session.query.return_value.filter.return_value.all.return_value = students
    
    # Mock the calculate_student_analytics method
    student_analytics_service.calculate_student_analytics = MagicMock()
    
    # Call the method
    student_analytics_service.calculate_all_student_analytics(
        organization_id=1,
        academic_year="2023-2024",
        term="Term1"
    )
    
    # Assertions
    assert student_analytics_service.calculate_student_analytics.call_count == 3
    
    # Verify the method was called with correct arguments for each student
    student_analytics_service.calculate_student_analytics.assert_any_call(
        organization_id=1,
        student_id=1,
        academic_year="2023-2024",
        term="Term1"
    )
    student_analytics_service.calculate_student_analytics.assert_any_call(
        organization_id=1,
        student_id=2,
        academic_year="2023-2024",
        term="Term1"
    )
    student_analytics_service.calculate_student_analytics.assert_any_call(
        organization_id=1,
        student_id=3,
        academic_year="2023-2024",
        term="Term1"
    )
# EduResult - School Result Management System (SaaS-Multi-Tenant)🎓

A scalable, modern, responsive web application for managing student results, analytics and academic records for multiple schools/organizations.

## Key Features 🚀

- **Modern UI/UX**: Responsive design with Tailwind CSS and gradient aesthetics

- **Multi-Tenancy**: Tenant isolation at the database and application level (organization-based data separation)

- **Role-Based Access Control (RBAC)**: Super admin, admin, teacher, and student roles

- **Subscription Management**: Free, Premium and enterprise tiers with feature gating

- **Result Management**:
  - Single result entry with real-time validation
  - Bulk result entry functionality with real-time validation
  - Roll number conflict handling
  - Days present (Attendeance) tracking
  
- **Dynamic System - Customizable**:
  - Class-specific subject customization
  - Automatic subject loading per class
  - Customizable maximum marks
  - Customizable maximum attendance
  - Customiable grading and marks

- **Analytics & Reports**:
  - Grade calculation
  - Performance analytics
  - PDF report generation
  - Excel export functionality

- **Interactive Components**:
  - Real-time flash messages
  - Mobile-responsive navigation
  - Interactive form elements
  - Secure data validation


## Upcoming Features 🔮

1. **Enhanced Analytics**:
   - Advanced statistical analysis
   - Performance trend visualization
   - Class-wise comparison charts

2. **Extended Functionality**:
   - Student attendance tracking
   - Parent portal access
   - Teacher dashboard
   - Multiple session support

3. **Additional Features**:
   - Result card customization
   - Batch processing improvements
   - API integration capabilities
   - Enhanced data export options

4. **Security Enhancements**:
   - User role management
   - Data backup system
   - Audit logging
   - Enhanced validation

## Project folder structure: :folder:

```
result-app/
├─ app/
│  └─ __init__.py           # App factory (configure extensions, blueprints)
│  └─ config.py             # App configuration
├─ auth/
│  └─ __init__.py
│  └─ models.py             # User, Organization, Subscription models
│  └─ views.py              # Auth endpoints
│  └─ decorators.py         # Role-based accessed controls (RBAC) (@login_required, @premium_only)
├─ middleware/
│  └─ __init__.py
│  └─ tenant.py             # Tenanat-based request filtering       
│  └─ subscription.py       # Subscription and features gating logic
├─ models/
│  └─ __init__.py           # Export data
│  └─ base.py               # Base model (id, timestamps, organization_id), for multi-tenancy
│  └─ organization.py       # Organization model
│  └─ student.py            # Student model
│  └─ result.py             # Result model
│  └─ subject.py            # Subject model
|  └─ audit_logger.py       # Audit Logger model
|  └─ usage_tracker.py      # Usage Tracker model
│  └─ class_settings.py     # ClassSettings model
├─ services/
|  └─ __init__.py
│  └─ base_service.py         # Common logics for all services 
│  └─ result_service.py       # Business logic related to result
│  └─ student_service.py      # Business logic related to students
│  └─ analytics_service.py    # Business logic related to analytics
│  └─ export_service.py       # Logic related to PDF/Excel generation 
│  └─ settings_service.py     # Logic related to class settings, subject
│  └─ auth_service.py         #  Registration, login, role assignment
├─ utils/
│  └─ class_result_pdf.py     # Class-Sheet Generation Logic
│  └─ marksheet_pdf.py        # Marksheet Generation Logic
│  └─ grading.py              # Logic for calculations like grading, ranking
│  └─ error_handlers.py       # Common error handlers
│  └─ validations.py          # Common Validations
├─ routes/
│  └─ __init__.py             # Import all Blueprints
│  └─ admin_routes.py         # ?
│  └─ api_routes.py           # ?
│  └─ results.py              # All result entry/edit/view logic
│  └─ analytics.py            # All analytics endpoints
│  └─ settings.py             # All settings, subjects/class settings
│  └─ student.py              # All student-related endpoints
│  └─ export.py               # Export endpoints
│  └─ main_routes.py          # Route endpoints for user and organization auth
│  └─ auth.py                
├── templates/
│   ├── _header.html                # Global header component
│   ├── _footer.html                # Global footer component
│   ├── home.html                   # Landing page
│   ├── enter_result.html           # Single result entry
│   ├── bulk_entry.html             # Bulk result import
│   ├── view_result.html            # Result viewing interface
│   ├── customization.html          # Customization (was Subject Management)
│   ├── customize_result.html       # Marksheet (individual result pdf) customization
│   ├── customizae_class_result.html    # Class ResultSheet pdf customization
│   ├── edit_result.html            # Edit result for changes in DB
│   ├── privacy.html                # Telling about Privacy Policies
│   ├── terms.html                  # Telling terms of usage etc.
│   ├── cookies.html                # Telling cookies polices.
│   ├── student_detail.html         # Individual Student Result Preview
│   └── analytics.html              # Analytics dashboard
├── static/
│   ├── css/       # Custom styling (using Tailwind CDN) so empty.
│   ├── pdfs/      # auto-generated result pdfs by users.
│   └── js/     # JavaScript functionality (empty since all in files)
├── database/
|   ├─ supabase_schema.sql      # Supabase DB schema with
│   └── result.db               # SQLite database
├── images/
│   └── #empty   # May be include related like logo, favicon etc. in future.
├── tests/        # Unit tests for services/models
│   ├── test_auth.py/       
│   └── test_services.py               
├─ migrations/
│  └─ ...                     # Alembic migration scripts
├─ app.py                     # Will import app factory
├─ wsgi.py                    # Entry point for production
├─ .env                      # Environment settings (SECRET_KEY, DB_URL, etc.)
├─ requirements.txt
```



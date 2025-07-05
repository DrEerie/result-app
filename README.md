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
│  ├─ __init__.py           # App factory (configure extensions, blueprints, loads .env)
│  ├─ config.py             # App configuration (Flask, DB, Redis, Supabase)
├─ auth/
│  ├─ __init__.py
│  ├─ models.py             # User, Organization, Subscription models
│  ├─ views.py              # Auth endpoints (register, login, logout, password reset)
│  ├─ decorators.py         # Role-based access controls (RBAC) (@login_required, @admin_required, etc.)
├─ middleware/
│  ├─ __init__.py
│  ├─ tenant.py             # Tenant-based request filtering (multi-tenancy)
│  ├─ subscription.py       # Subscription and feature gating logic
│  ├─ request_validation.py # Request validation and sanitization
├─ models/
│  ├─ __init__.py           # Export data
│  ├─ base.py               # Base model (id, timestamps, organization_id)
│  ├─ organization.py       # Organization model
│  ├─ student.py            # Student model
│  ├─ result.py             # Result model
│  ├─ subject.py            # Subject model
│  ├─ audit_logger.py       # Audit Logger model
│  ├─ usage_tracker.py      # Usage Tracker model
│  ├─ class_settings.py     # ClassSettings model
├─ services/
│  ├─ __init__.py
│  ├─ base_service.py         # Common logic for all services
│  ├─ result_service.py       # Business logic related to results
│  ├─ student_service.py      # Business logic related to students
│  ├─ analytics_service.py    # Business logic related to analytics
│  ├─ export_service.py       # PDF/Excel export logic
│  ├─ settings_service.py     # Class/subject settings logic
│  ├─ auth_service.py         # Registration, login, role assignment
│  ├─ pdf_service.py          # PDF generation helpers
│  ├─ supabase_client.py      # Supabase client integration
├─ utils/
│  ├─ __init__.py
│  ├─ class_result_pdf.py     # Class-Sheet PDF Generation
│  ├─ marksheet_pdf.py        # Marksheet PDF Generation
│  ├─ grading.py              # Grading, ranking logic
│  ├─ error_handlers.py       # Common error handlers
│  ├─ validations.py          # Common validations
│  ├─ certificate_pdf.py      # Certificate PDF Generation
├─ routes/
│  ├─ __init__.py             # Import all Blueprints
│  ├─ admin_routes.py         # Admin dashboard, user management, subscription, audit logs
│  ├─ api_routes.py           # API endpoints
│  ├─ results.py              # All result entry/edit/view logic
│  ├─ analytics.py            # Analytics endpoints
│  ├─ settings.py             # Settings, subjects/class settings
│  ├─ student.py              # Student-related endpoints
│  ├─ export.py               # Export endpoints
│  ├─ main_routes.py          # Public/marketing, pricing, features, legal, error pages
│  ├─ auth.py                 # Auth endpoints (register, login, logout)
│  ├─ dashboard.py            # Dashboard endpoints
├─ templates/
│  ├─ public/                 # PUBLIC PAGES (not logged in)
│  │   ├─ index.html              # Marketing landing page
│  │   ├─ login.html              # Login page
│  │   ├─ register.html           # Registration page
│  │   ├─ forgot_password.html    # Password reset
│  │   ├─ _public_header.html     # Header for public routes
│  │   ├─ _public_footer.html     # Footer for public routes
│  ├─ dashboard/              # AUTHENTICATED PAGES
│  │   ├─ _dashboard_header.html  # Internal nav bar
│  │   ├─ _dashboard_footer.html  # Internal footer
│  │   ├─ home.html               # Authenticated landing
│  │   ├─ enter_result.html       # Single result entry
│  │   ├─ bulk_entry.html         # Bulk result import
│  │   ├─ view_result.html        # View results
│  │   ├─ customization.html      # Customization options
│  │   ├─ customize_result.html   # Marksheet customization
│  │   ├─ customize_class_result.html  # Class sheet customization
│  │   ├─ edit_result.html        # Edit functionality
│  │   ├─ student_detail.html     # Student preview
│  │   ├─ analytics.html          # Analytics dashboard
│  ├─ shared/                    # GLOBAL REUSABLE COMPONENTS
│  │   ├─ privacy.html           # Legal page
│  │   ├─ terms.html             # Legal page
│  │   ├─ cookies.html           # Legal page
│  │   ├─ 404.html               # Not found errors
│  │   ├─ 500.html               # Server-side errors
├─ static/
│  ├─ css/
│  ├─ js/
│  ├─ images/                   # Logos, favicons, etc.
├─ database/
│  ├─ supabase_schema.sql       # Supabase DB schema (Postgres, RLS, triggers)
│  ├─ result.db                 # SQLite database (for local/dev)
├─ tests/                       # Unit tests for services/models
│  ├─ __init__.py
│  ├─ conftest.py
│  ├─ test_auth.py
│  ├─ test_services.py
├─ migrations/                  # Alembic migration scripts
├─ wsgi.py                      # Entry point for production (WSGI server)
├─ .env                         # Environment settings (Supabase_URL, keys, DB, Redis)
├─ requirements.txt             # Python dependencies
├─ README.md
```



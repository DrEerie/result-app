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
EveClus/
├─ app/
│  ├─ __init__.py           # App factory (configure extensions, blueprints, loads .env)
│  ├─ config.py             # App configuration (Flask, DB, Redis, Supabase)
│  ├─ extensions.py         # Initialize extensions (SQLAlchemy, Redis, Celery, etc.)
│
├─ auth/
│  ├─ __init__.py
│  ├─ models.py             # User, Organization, Subscription models
│  ├─ views.py              # Auth endpoints (register, login, logout, password reset)
│  ├─ decorators.py         # Role-based access controls (RBAC)
│
├─ superadmin/              # SUPERADMIN MODULE
│  ├─ __init__.py
│  ├─ models.py             # SuperAdmin, SystemSettings, GlobalAudit models
│  ├─ views.py              # SuperAdmin dashboard, tenant management
│  ├─ decorators.py         # @superadmin_required decorator
│  ├─ tenant_manager.py     # Tenant creation, schema provisioning
│  ├─ system_monitor.py     # Health checks, system metrics
│  ├─ billing_manager.py    # Global billing overview, disputes
│
├─ tenants/                 # TENANT MANAGEMENT
│  ├─ __init__.py
│  ├─ models.py             # Tenant, TenantSchema, TenantSettings models
│  ├─ schema_manager.py     # Schema creation, migration per tenant
│  ├─ tenant_context.py     # Tenant context switching
│  ├─ provisioning.py       # Auto-provisioning new tenants
│
├─ middleware/
│  ├─ __init__.py
│  ├─ tenant.py             # Tenant-based request filtering
│  ├─ subscription.py       # Subscription and feature gating logic
│  ├─ request_validation.py # Request validation and sanitization
│  ├─ cache_middleware.py   # Cache management
│
├─ models/
│  ├─ __init__.py
│  ├─ base.py               # Base model (id, timestamps, tenant_id)
│  ├─ organization.py       # Organization model
│  ├─ student.py            # Student model
│  ├─ result.py             # Result model
│  ├─ subject.py            # Subject model
│  ├─ audit_logger.py       # Audit Logger model
│  ├─ usage_tracker.py      # Usage Tracker model
│  ├─ class_settings.py     # ClassSettings model
│
├─ services/
│  ├─ __init__.py
│  ├─ base_service.py       # Common logic for all services
│  ├─ result_service.py     # Business logic related to results
│  ├─ student_service.py    # Business logic related to students
│  ├─ analytics_service.py  # Business logic related to analytics
│  ├─ export_service.py     # PDF/Excel export logic
│  ├─ settings_service.py   # Class/subject settings logic
│  ├─ auth_service.py       # Registration, login, role assignment
│  ├─ pdf_service.py        # PDF generation helpers
│  ├─ supabase_client.py    # Supabase client integration
│  ├─ email_service.py      #  ThirdParty Email service wrapper
│  ├─ cache_service.py      # Redis caching service
│
├─ jobs/                    # BACKGROUND JOBS
│  ├─ __init__.py
│  ├─ celery_app.py         # Celery configuration
│  ├─ email_jobs.py         # Email sending jobs
│  ├─ report_jobs.py        # Background report generation
│
├─ monitoring/              # SYSTEM MONITORING
│  ├─ __init__.py
│  ├─ health_checks.py      # System health endpoints
│  ├─ metrics.py            # Performance metrics collection
│  ├─ alerts.py             # Alert system for critical issues
│
├─ utils/
│  ├─ __init__.py
│  ├─ class_result_pdf.py   # Class-Sheet PDF Generation
│  ├─ marksheet_pdf.py      # Marksheet PDF Generation
│  ├─ grading.py            # Grading, ranking logic
│  ├─ error_handlers.py     # Common error handlers
│  ├─ validations.py        # Common validations
│  ├─ certificate_pdf.py    # Certificate PDF Generation
│  ├─ helpers.py            # Common helper functions
│  ├─ constants.py          # Application constants
│
├─ routes/
│  ├─ __init__.py
│  ├─ admin_routes.py       # Admin dashboard, user management
│  ├─ superadmin_routes.py  # SuperAdmin routes
│  ├─ api_routes.py         # API endpoints
│  ├─ results.py            # All result entry/edit/view logic
│  ├─ analytics.py          # Analytics endpoints
│  ├─ settings.py           # Settings, subjects/class settings
│  ├─ student.py            # Student-related endpoints
│  ├─ export.py             # Export endpoints
│  ├─ main_routes.py        # Public/marketing, pricing, features
│  ├─ auth.py               # Auth endpoints
│  ├─ dashboard.py          # Dashboard endpoints
│  ├─ billing_routes.py     # Billing and subscription routes
│  ├─ health_routes.py      # Health check routes
│
├─ templates/
│  ├─ public/               # PUBLIC PAGES
│  │   ├─ index.html
│  │   ├─ login.html
│  │   ├─ register.html
│  │   ├─ forgot_password.html
│  │   ├─ _public_header.html
│  │   ├─ _public_footer.html
│  ├─ dashboard/            # AUTHENTICATED PAGES
│  │   ├─ _dashboard_header.html
│  │   ├─ _dashboard_footer.html
│  │   ├─ home.html
│  │   ├─ enter_result.html
│  │   ├─ bulk_entry.html
│  │   ├─ view_result.html
│  │   ├─ customization.html
│  │   ├─ customize_result.html
│  │   ├─ customize_class_result.html
│  │   ├─ edit_result.html
│  │   ├─ student_detail.html
│  │   ├─ analytics.html
│  ├─ superadmin/           #  SUPERADMIN TEMPLATES
│  │   ├─ dashboard.html
│  │   ├─ tenants.html
│  │   ├─ billing_overview.html
│  │   ├─ system_health.html
│  │   ├─ audit_logs.html
│  ├─ shared/               # GLOBAL REUSABLE COMPONENTS
│  │   ├─ privacy.html
│  │   ├─ terms.html
│  │   ├─ cookies.html
│  │   ├─ 404.html
│  │   ├─ 500.html
│  │   ├─ emails/           # Email templates (for third party service - resend)
│  │   │   ├─ welcome.html
│  │   │   ├─ invoice.html
│  │   │   ├─ password_reset.html
│
├─ static/
│  ├─ css/
│  ├─ js/
│  ├─ images/
│
├─ database/
│  ├─ supabase_schema.sql   # Main schema
│  ├─ tenant_schema.sql     # Per-tenant schema template
│
├─ tests/
│  ├─ __init__.py
│  ├─ conftest.py
│
├─ migrations/              # Alembic migration scripts
├─ wsgi.py
├─ test_app.py
├─ .env
├─ requirements.txt
├─ README.md
```

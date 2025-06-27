# routes/__init__.py
from flask import Blueprint

def register_blueprints(app):
    """Register all blueprints"""
    from .auth import auth_bp
    from .main_routes import main_bp
    from .results import results_bp
    from .student import student_bp
    from .settings import settings_bp
    from .analytics import analytics_bp
    from .export import export_bp
    from .admin_routes import admin_bp
    from .api_routes import api_bp
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(results_bp, url_prefix='/results')
    app.register_blueprint(student_bp, url_prefix='/students')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(export_bp, url_prefix='/export')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
# app/__init__.py
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_cors import CORS
import redis
import logging
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Import configurations
from .config import config

# Import database
from models.base import db

# Import services
from services.supabase_client import supabase_client

# Import middleware
from middleware.tenant import TenantMiddleware
from middleware.subscription import SubscriptionMiddleware

# Extensions
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()
cors = CORS()

def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    init_extensions(app)
    
    # Initialize services
    init_services(app)
    
    # Initialize middleware
    init_middleware(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Setup logging
    setup_logging(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

def init_extensions(app):
    """Initialize Flask extensions"""
    # Database
    db.init_app(app)
    
    # Migrations
    migrate.init_app(app, db)
    
    # Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Register user_loader and request_loader using decorators
    from services.auth_service import load_user, request_loader
    
    @login_manager.user_loader
    def user_loader_callback(user_id):
        return load_user(user_id)
    
    @login_manager.request_loader
    def request_loader_callback(request):
        return request_loader(request)
    
    # Mail
    mail.init_app(app)
    
    # CORS
    cors.init_app(app, origins=["http://127.0.0.1:5000", "https://yourdomain.com"])
    
    # Redis (optional)
    
    app.config['REDIS_URL'] = os.getenv("REDIS_URL")

    try:
        app.redis = redis.from_url(app.config['REDIS_URL'])
        app.redis.ping()
    except:
        app.redis = None
        app.logger.warning("Redis not available, caching disabled")

def init_services(app):
    """Initialize application services"""
    # Supabase client
    supabase_client.init_app(app)

def init_middleware(app):
    """Initialize custom middleware"""
    TenantMiddleware(app)
    SubscriptionMiddleware(app)

def register_blueprints(app):
    """Register application blueprints"""
    from routes.auth import auth_bp
    from routes.main_routes import main_bp
    from routes.api_routes import api_bp
    from routes.admin_routes import admin_bp
    from routes.analytics import analytics_bp
    from routes.settings import settings_bp
    from routes.export import export_bp
    from routes.dashboard import dashboard_bp
    from routes.results import results_bp
    from routes.student import student

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(export_bp, url_prefix='/export')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(results_bp, url_prefix='/results')
    app.register_blueprint(student, url_prefix='/student')
    
def setup_logging(app):
    """Setup application logging"""
    if not app.debug and not app.testing:
        # Production logging
        import logging
        from logging.handlers import RotatingFileHandler
        import os
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler('logs/result_app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('EveClus startup')
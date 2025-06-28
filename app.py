from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_compress import Compress
from flask_talisman import Talisman
from app.config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
cache = Cache()
compress = Compress()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_class=Config):
    """Application factory function"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    cache.init_app(app)
    compress.init_app(app)
    limiter.init_app(app)
    
    # Initialize Talisman with CSP
    Talisman(app, content_security_policy=app.config['CONTENT_SECURITY_POLICY'])

    # Configure login
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Register blueprints
    from routes.main_routes import main_bp
    from routes.auth import auth
    from routes.admin_routes import admin_bp
    from routes.api_routes import api_bp
    from routes.results import results_bp
    from routes.analytics import analytics_bp
    from routes.settings import settings_bp
    from routes.student import student
    from routes.export import export_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(results_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(student)
    app.register_blueprint(export_bp)

    # Register error handlers
    from utils.error_handlers import register_error_handlers
    register_error_handlers(app)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

import pytest
from app import create_app
from app.config import Config
from models import db as _db
import os

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost.localdomain'
    PRESERVE_CONTEXT_ON_EXCEPTION = False

@pytest.fixture(scope='session')
def app():
    """Create application for the tests."""
    _app = create_app(TestConfig)
    
    # Establish an application context
    ctx = _app.app_context()
    ctx.push()
    
    yield _app
    
    ctx.pop()

@pytest.fixture(scope='session')
def db(app):
    """Create database for the tests."""
    _db.app = app
    _db.create_all()
    
    yield _db
    
    _db.drop_all()

@pytest.fixture(scope='function')
def session(db):
    """Create a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()
    
    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)
    
    db.session = session
    
    yield session
    
    transaction.rollback()
    connection.close()
    session.remove()

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test runner for the app's Click commands."""
    return app.test_cli_runner() 
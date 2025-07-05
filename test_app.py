#!/usr/bin/env python3
"""
Simple test script to verify the application can start without import errors
"""

try:
    from app import create_app
    print("✓ Successfully imported create_app")
    
    # Test creating the app
    app = create_app('development')
    print("✓ Successfully created Flask app")
    
    # Test app context
    with app.app_context():
        print("✓ App context works")
        
        # Test database import
        from models.base import db
        print("✓ Database import successful")
        
        # Test blueprint imports
        from routes.auth import auth_bp
        from routes.main_routes import main_bp
        from routes.results import results_bp
        print("✓ Blueprint imports successful")
        
    print("\n🎉 All basic tests passed! The application should start correctly.")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
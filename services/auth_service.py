# services/auth_service.py
from flask import session, request, current_app
from flask_login import UserMixin, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash
from models.organization import Organization
from models.base import User, Subscription, db
from services.supabase_client import supabase_client
import uuid
import logging

logger = logging.getLogger(__name__)

class AuthService:
    
    @staticmethod
    def register_organization(org_data, admin_data):
        """Register new organization with admin user"""
        try:
            # Create organization
            org = Organization(
                name=org_data['name'],
                slug=org_data['slug'],
                email=org_data['email'],
                phone=org_data.get('phone'),
                address=org_data.get('address')
            )
            db.session.add(org)
            db.session.flush()  # Get org.id
            
            # Create Supabase auth user
            auth_response = supabase_client.get_client(service_role=True).auth.admin.create_user({
                "email": admin_data['email'],
                "password": admin_data['password'],
                "email_confirm": True,
                "user_metadata": {
                    "full_name": admin_data['full_name'],
                    "organization_id": str(org.id),
                    "role": "admin"
                }
            })
            
            if auth_response.user:
                # Create user record
                user = User(
                    id=auth_response.user.id,
                    organization_id=org.id,
                    email=admin_data['email'],
                    full_name=admin_data['full_name'],
                    role='admin',
                    phone=admin_data.get('phone')
                )
                db.session.add(user)
                
                # Create default subscription
                subscription = Subscription(
                    organization_id=org.id,
                    tier='free',
                    status='active'
                )
                db.session.add(subscription)
                
                db.session.commit()
                
                logger.info(f"Organization {org.name} registered successfully")
                return {"success": True, "organization": org, "user": user}
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def login_user_with_supabase(email, password):
        """Login user using Supabase auth"""
        try:
            # Authenticate with Supabase
            auth_response = supabase_client.get_client().auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user:
                # Get user from database
                user = User.query.filter_by(id=auth_response.user.id).first()
                if user and user.is_active:
                    # Store auth session
                    session['supabase_session'] = auth_response.session.model_dump()
                    session['user_id'] = str(user.id)
                    session['organization_id'] = str(user.organization_id)
                    
                    # Update last login
                    user.last_login = db.datetime.utcnow()
                    db.session.commit()
                    
                    return {"success": True, "user": user}
                else:
                    return {"success": False, "error": "User not found or inactive"}
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def logout_user():
        """Logout user from Supabase and Flask session"""
        try:
            # Sign out from Supabase
            supabase_client.get_client().auth.sign_out()
            
            # Clear Flask session
            session.clear()
            
            return {"success": True}
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_current_user():
        """Get current authenticated user"""
        user_id = session.get('user_id')
        if user_id:
            return User.query.filter_by(id=user_id).first()
        return None
    
    @staticmethod
    def create_user(user_data, organization_id):
        """Create new user in organization"""
        try:
            # Create Supabase auth user
            auth_response = supabase_client.get_client(service_role=True).auth.admin.create_user({
                "email": user_data['email'],
                "password": user_data['password'],
                "email_confirm": True,
                "user_metadata": {
                    "full_name": user_data['full_name'],
                    "organization_id": str(organization_id),
                    "role": user_data['role']
                }
            })
            
            if auth_response.user:
                # Create user record
                user = User(
                    id=auth_response.user.id,
                    organization_id=organization_id,
                    email=user_data['email'],
                    full_name=user_data['full_name'],
                    role=user_data['role'],
                    phone=user_data.get('phone'),
                    employee_id=user_data.get('employee_id'),
                    department=user_data.get('department')
                )
                db.session.add(user)
                db.session.commit()
                
                return {"success": True, "user": user}
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"User creation failed: {str(e)}")
            return {"success": False, "error": str(e)}

# Flask-Login integration
class AuthUser(UserMixin):
    def __init__(self, user_id):
        self.id = user_id
        self._user = None
    
    @property
    def user(self):
        if not self._user:
            self._user = User.query.filter_by(id=self.id).first()
        return self._user
    
    def get_id(self):
        return str(self.id)
    
    @property
    def is_active(self):
        return self.user.is_active if self.user else False
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False

def load_user(user_id):
    """Load user for Flask-Login"""
    user = User.query.filter_by(id=user_id).first()
    if user:
        return AuthUser(user.id)
    return None

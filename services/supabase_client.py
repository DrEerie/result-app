# services/supabase_client.py
from supabase import create_client, Client
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    def __init__(self):
        self.client: Client = None
        self.service_client: Client = None
    
    def init_app(self, app):
        """Initialize Supabase clients with Flask app"""
        self.client = create_client(
            app.config['SUPABASE_URL'],
            app.config['SUPABASE_ANON_KEY']
        )
        
        self.service_client = create_client(
            app.config['SUPABASE_URL'],
            app.config['SUPABASE_SERVICE_ROLE_KEY']
        )
        
        app.supabase = self
        logger.info("Supabase client initialized")
    
    def get_client(self, service_role=False):
        """Get Supabase client (anon or service role)"""
        return self.service_client if service_role else self.client

# Initialize global instance
supabase_client = SupabaseClient()

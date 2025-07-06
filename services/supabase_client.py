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
        supabase_url = app.config['SUPABASE_URL']
        supabase_anon_key = app.config['SUPABASE_ANON_KEY']
        supabase_service_key = app.config.get('SUPABASE_SERVICE_ROLE_KEY')
        
        print(f'DEBUG: SUPABASE_URL = {repr(supabase_url)}')
        print(f'DEBUG: SUPABASE_ANON_KEY = {repr(supabase_anon_key)}')
        print(f'DEBUG: SUPABASE_SERVICE_ROLE_KEY = {repr(supabase_service_key)}')
        
        # Validate required configuration
        if not supabase_url:
            raise ValueError("SUPABASE_URL is required")
        if not supabase_anon_key:
            raise ValueError("SUPABASE_ANON_KEY is required")
        
        # Initialize anon client
        self.client = create_client(supabase_url, supabase_anon_key)
        
        # Initialize service client only if service role key is available
        if supabase_service_key:
            self.service_client = create_client(supabase_url, supabase_service_key)
            logger.info("Supabase service client initialized")
        else:
            logger.warning("SUPABASE_SERVICE_ROLE_KEY not provided - service client unavailable")
            self.service_client = None
        
        app.supabase = self
        logger.info("Supabase client initialized")
    
    def get_client(self, service_role=False):
        """Get Supabase client (anon or service role)"""
        if service_role:
            if self.service_client is None:
                logger.warning("Service role client requested but not available, falling back to anon client")
                return self.client
            return self.service_client
        return self.client

# Initialize global instance
supabase_client = SupabaseClient()
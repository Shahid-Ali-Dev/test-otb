import json
from flask import current_app, url_for, session
from authlib.integrations.requests_client import OAuth2Session
import requests
from urllib.parse import urlencode

class GoogleOAuth:
    def __init__(self, app=None):
        self.client_id = None
        self.client_secret = None
        self.discovery_url = "https://accounts.google.com/.well-known/openid-configuration"
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.client_id = app.config.get('GOOGLE_CLIENT_ID')
        self.client_secret = app.config.get('GOOGLE_CLIENT_SECRET')
        
    def get_oauth_client(self, **kwargs):
        """Create OAuth2 session"""
        if not self.client_id or not self.client_secret:
            raise RuntimeError("Google OAuth not properly initialized")
            
        return OAuth2Session(
            self.client_id,
            self.client_secret,
            scope='openid email profile',
            redirect_uri=url_for('google_callback', _external=True),
            **kwargs
        )
    
    def get_authorization_url(self):
        """Get Google authorization URL"""
        try:
            # Discover OAuth endpoints
            response = requests.get(self.discovery_url)
            auth_endpoint = response.json()['authorization_endpoint']
            
            client = self.get_oauth_client()
            authorization_url, state = client.create_authorization_url(
                auth_endpoint,
                access_type='offline',
                prompt='select_account'
            )
            
            return authorization_url, state
        except Exception as e:
            current_app.logger.error(f"Error getting authorization URL: {str(e)}")
            return None, None
    
    def fetch_token(self, authorization_response):
        """Exchange authorization code for tokens"""
        try:
            response = requests.get(self.discovery_url)
            token_endpoint = response.json()['token_endpoint']
            
            client = self.get_oauth_client()
            token = client.fetch_token(
                token_endpoint,
                authorization_response=authorization_response
            )
            return token
        except Exception as e:
            current_app.logger.error(f"Error fetching token: {str(e)}")
            return None
    
    def get_user_info(self, token):
        """Get user info from Google"""
        try:
            response = requests.get(self.discovery_url)
            userinfo_endpoint = response.json()['userinfo_endpoint']
            
            client = self.get_oauth_client(token=token)
            userinfo = client.get(userinfo_endpoint).json()
            return userinfo
        except Exception as e:
            current_app.logger.error(f"Error getting user info: {str(e)}")
            return None

# Create instance but don't initialize it here
google_oauth = GoogleOAuth()

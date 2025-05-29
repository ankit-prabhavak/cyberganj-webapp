import os

class Config:
    """Configuration settings for the CyberGanj application."""
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-cybersecurity-project'
    DEBUG = os.environ.get('FLASK_DEBUG') or True
    
    # Application settings
    APP_NAME = 'CyberGanj'
    APP_DESCRIPTION = 'Your go-to resource for cybersecurity awareness and education'
    
    # Content settings
    ARTICLES_PER_PAGE = 6



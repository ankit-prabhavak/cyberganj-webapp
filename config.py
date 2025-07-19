import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-cybersecurity-project')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1', 'yes']
    
    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if DATABASE_URL:
        # Production: Use PostgreSQL from Render
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
        # Fix: Handle Render's postgres:// vs postgresql:// issue
        if DATABASE_URL.startswith("postgres://"):
            SQLALCHEMY_DATABASE_URI = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    else:
        # Development: Use SQLite locally
        basedir = os.path.abspath(os.path.dirname(__file__))
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'instance', 'users.db')}"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }

    APP_NAME = 'CyberGanj'
    APP_DESCRIPTION = 'Your go-to resource for cybersecurity awareness and education'
    ARTICLES_PER_PAGE = 6
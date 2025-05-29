import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-cybersecurity-project'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True') == 'True'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')  # Use PostgreSQL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    APP_NAME = 'CyberGanj'
    APP_DESCRIPTION = 'Your go-to resource for cybersecurity awareness and education'
    ARTICLES_PER_PAGE = 6

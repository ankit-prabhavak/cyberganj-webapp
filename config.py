import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-cybersecurity-project')
    DEBUG = os.environ.get('FLASK_DEBUG', True)

    SQLALCHEMY_DATABASE_URI = os.environ.get('postgresql://cyberganj_db_7jfy_user:yHWzRX0z1sLg3cTQRUUw5zFrU57VhnAj@dpg-d1tmpt3uibrs73flrcv0-a/cyberganj_db_7jfy', 'sqlite:///instance/users.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    APP_NAME = 'CyberGanj'
    APP_DESCRIPTION = 'Your go-to resource for cybersecurity awareness and education'
    ARTICLES_PER_PAGE = 6

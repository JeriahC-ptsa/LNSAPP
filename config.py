# import os

# basedir = os.path.abspath(os.path.dirname(__file__))

# class Config:
#     SECRET_KEY = os.environ.get('SECRET_KEY', 'replace-this-secret')
#     SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'database.db')
#     SQLALCHEMY_TRACK_MODIFICATIONS = False




import os

# Get the base directory
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "my_super_secret_key_1234")
    
    # Database configuration with PostgreSQL support
    # Render uses "postgres://" but SQLAlchemy 1.4+ requires "postgresql://"
    database_url = os.environ.get("DATABASE_URL", 
                                  'sqlite:///' + os.path.join(basedir, 'instance', 'app.db'))
    
    # Fix for Render PostgreSQL URL format
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Production settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,  # Verify connections before using
        "pool_recycle": 300,     # Recycle connections after 5 minutes
    }



"""
Initialize the database with all tables
"""
from app import app, db
from models import *
from auth_models import *

with app.app_context():
    print("Creating all database tables...")
    db.create_all()
    print("✅ Database tables created successfully!")
    
    # Verify tables
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"\n📋 Created {len(tables)} tables:")
    for table in sorted(tables):
        print(f"  - {table}")

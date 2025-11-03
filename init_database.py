"""
Initialize database tables for production deployment
Run this after deploying to create all tables
"""
from app import app, db

print("Initializing database...")
print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")

with app.app_context():
    # Create all tables
    db.create_all()
    print("\nOK All tables created successfully!")
    
    # List all tables
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    print(f"\nCreated {len(tables)} tables:")
    for table in sorted(tables):
        print(f"  - {table}")
    
    print("\nNext steps:")
    print("1. Run: python setup_auth_original_db.py")
    print("2. This will create the admin user (admin/admin123)")
    print("3. Login and start using the application!")

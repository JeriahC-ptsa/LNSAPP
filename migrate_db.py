"""
Database Migration Script
Adds new tables: attempts and student_module_progress
"""

from app import app, db
from models import Attempt, StudentModuleProgress

def migrate():
    """Create new tables"""
    with app.app_context():
        print("Starting database migration...")
        print("-" * 50)
        
        try:
            # Create all tables (will only create missing ones)
            db.create_all()
            
            print("✓ Tables created successfully!")
            print("\nNew tables added:")
            print("  1. attempts - Stores unlimited mini-task attempts")
            print("  2. student_module_progress - Tracks module-level progress")
            print("-" * 50)
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"✗ Error during migration: {str(e)}")
            print("Migration failed!")
            return False
        
        return True

if __name__ == "__main__":
    success = migrate()
    if success:
        print("\n✓ Database is ready to use!")
    else:
        print("\n✗ Please check the error and try again.")

"""
Add last_updated column to attempts and student_module_progress tables
"""

from app import app, db
from sqlalchemy import text

def migrate_editable_attempts():
    """Add last_updated columns"""
    with app.app_context():
        print("=" * 80)
        print("MIGRATING TABLES - ADDING EDITABLE TIMESTAMPS")
        print("=" * 80)
        
        try:
            inspector = db.inspect(db.engine)
            
            # Check attempts table
            attempts_columns = [col['name'] for col in inspector.get_columns('attempts')]
            if 'last_updated' not in attempts_columns:
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE attempts ADD COLUMN last_updated DATETIME"))
                    conn.commit()
                print("  ✓ ADDED: Column 'last_updated' to attempts table")
            else:
                print("  ⊘ SKIP: Column 'last_updated' already exists in attempts")
            
            # Check student_module_progress table
            progress_columns = [col['name'] for col in inspector.get_columns('student_module_progress')]
            if 'last_updated' not in progress_columns:
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE student_module_progress ADD COLUMN last_updated DATETIME"))
                    conn.commit()
                print("  ✓ ADDED: Column 'last_updated' to student_module_progress table")
            else:
                print("  ⊘ SKIP: Column 'last_updated' already exists in student_module_progress")
            
            print("\n" + "=" * 80)
            print("✓ MIGRATION COMPLETE!")
            print("=" * 80)
            print("\nAttempts are now fully editable:")
            print("  - Attempt dates can be changed to any date")
            print("  - Results can be updated")
            print("  - Last updated timestamp tracks changes")
            print("  - No restrictions based on schedule dates")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n✗ ERROR: {str(e)}")
            return False
        
        return True

if __name__ == "__main__":
    migrate_editable_attempts()

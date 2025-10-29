"""
Migration script to add student_number column and split existing student_name data
"""
from app import app, db
from models import Student
from sqlalchemy import text

def migrate_student_number():
    """Add student_number column and migrate existing data"""
    with app.app_context():
        print("Starting migration: Add student_number column...")
        
        # Step 1: Add the column if it doesn't exist
        try:
            with db.engine.connect() as conn:
                # Check if column exists
                result = conn.execute(text("PRAGMA table_info(students)"))
                columns = [row[1] for row in result]
                
                if 'student_number' not in columns:
                    print("Adding student_number column...")
                    conn.execute(text("ALTER TABLE students ADD COLUMN student_number VARCHAR(50)"))
                    conn.commit()
                    print("✓ Column added successfully")
                else:
                    print("✓ Column already exists")
        except Exception as e:
            print(f"Error adding column: {e}")
            return
        
        # Step 2: Migrate existing data
        print("\nMigrating existing student data...")
        students = Student.query.all()
        updated_count = 0
        
        for student in students:
            # Split student_name on first space
            parts = student.student_name.split(' ', 1)
            
            if len(parts) > 1:
                # Has both student number and name
                student.student_number = parts[0]
                student.student_name = parts[1]
                updated_count += 1
                print(f"  Updated: {parts[0]} -> {parts[1]}")
            else:
                # No space, keep as is (name only)
                student.student_number = None
                print(f"  Kept as is: {student.student_name}")
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n✓ Migration completed successfully!")
            print(f"  - Updated {updated_count} students")
            print(f"  - Total students: {len(students)}")
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Error during migration: {e}")

if __name__ == "__main__":
    migrate_student_number()

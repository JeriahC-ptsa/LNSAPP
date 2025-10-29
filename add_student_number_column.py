"""
Simple migration to add student_number column to students table
"""
import sqlite3
import os

# Database path
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'app.db')

if not os.path.exists(db_path):
    print(f"Error: Database not found at {db_path}")
    exit(1)

print(f"Connecting to database: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if column already exists
    cursor.execute("PRAGMA table_info(students)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'student_number' in columns:
        print("✓ Column 'student_number' already exists!")
    else:
        print("Adding 'student_number' column...")
        cursor.execute("ALTER TABLE students ADD COLUMN student_number VARCHAR(50)")
        conn.commit()
        print("✓ Column added successfully!")
    
    # Now migrate the data
    print("\nMigrating existing student data...")
    cursor.execute("SELECT id, student_name FROM students")
    students = cursor.fetchall()
    
    updated_count = 0
    for student_id, student_name in students:
        if ' ' in student_name:
            # Split on first space
            parts = student_name.split(' ', 1)
            student_number = parts[0]
            new_name = parts[1]
            
            cursor.execute(
                "UPDATE students SET student_number = ?, student_name = ? WHERE id = ?",
                (student_number, new_name, student_id)
            )
            updated_count += 1
            print(f"  Updated ID {student_id}: {student_number} -> {new_name}")
        else:
            print(f"  Kept ID {student_id}: {student_name} (no space found)")
    
    conn.commit()
    print(f"\n✓ Migration completed successfully!")
    print(f"  - Updated {updated_count} students")
    print(f"  - Total students: {len(students)}")
    
except Exception as e:
    print(f"\n✗ Error during migration: {e}")
    conn.rollback()
finally:
    conn.close()
    print("\nDatabase connection closed.")

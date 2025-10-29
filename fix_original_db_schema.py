"""
Add missing columns to groups table in instance/app.db
"""
import sqlite3
import os

db_path = os.path.join('instance', 'app.db')

if not os.path.exists(db_path):
    print(f"❌ Database not found: {db_path}")
    exit(1)

print(f"Fixing schema in {db_path}...")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check current columns
    cursor.execute("PRAGMA table_info(groups)")
    columns = [col[1] for col in cursor.fetchall()]
    
    print(f"\nCurrent columns: {columns}")
    
    # Add site_id if missing
    if 'site_id' not in columns:
        print("Adding site_id...")
        cursor.execute("ALTER TABLE groups ADD COLUMN site_id INTEGER")
        print("✓ Added site_id")
    
    # Add date_added if missing
    if 'date_added' not in columns:
        print("Adding date_added...")
        cursor.execute("ALTER TABLE groups ADD COLUMN date_added DATETIME")
        print("✓ Added date_added")
    
    # Add province if missing
    if 'province' not in columns:
        print("Adding province...")
        cursor.execute("ALTER TABLE groups ADD COLUMN province VARCHAR(100)")
        print("✓ Added province")
    
    conn.commit()
    
    # Verify
    cursor.execute("PRAGMA table_info(groups)")
    new_columns = [col[1] for col in cursor.fetchall()]
    print(f"\nUpdated columns: {new_columns}")
    
    # Show data counts
    cursor.execute("SELECT COUNT(*) FROM groups")
    group_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM students")
    student_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM machines")
    machine_count = cursor.fetchone()[0]
    
    print(f"\n✅ Schema fixed!")
    print(f"\n📊 Data preserved:")
    print(f"  Groups: {group_count}")
    print(f"  Students: {student_count}")
    print(f"  Machines: {machine_count}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    conn.rollback()
finally:
    conn.close()

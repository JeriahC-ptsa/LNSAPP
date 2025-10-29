"""
Quick fix to add missing columns to groups table
"""
import sqlite3
from datetime import datetime

# Connect to the database
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

try:
    # Check if columns exist
    cursor.execute("PRAGMA table_info(groups)")
    columns = [col[1] for col in cursor.fetchall()]
    
    print("Current columns in 'groups' table:", columns)
    
    # Add date_added column if missing
    if 'date_added' not in columns:
        print("\nAdding 'date_added' column...")
        cursor.execute("""
            ALTER TABLE groups 
            ADD COLUMN date_added DATETIME DEFAULT CURRENT_TIMESTAMP
        """)
        print("✓ Added 'date_added' column")
    else:
        print("\n✓ 'date_added' column already exists")
    
    # Add province column if missing
    if 'province' not in columns:
        print("\nAdding 'province' column...")
        cursor.execute("""
            ALTER TABLE groups 
            ADD COLUMN province VARCHAR(100)
        """)
        print("✓ Added 'province' column")
    else:
        print("\n✓ 'province' column already exists")
    
    # Commit the changes
    conn.commit()
    print("\n✅ Database schema updated successfully!")
    
    # Verify
    cursor.execute("PRAGMA table_info(groups)")
    columns = [col[1] for col in cursor.fetchall()]
    print("\nUpdated columns in 'groups' table:", columns)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    conn.rollback()
finally:
    conn.close()

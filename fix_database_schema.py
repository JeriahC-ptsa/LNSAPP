"""
Fix database.db schema - add missing columns to groups table
"""
import sqlite3

# Connect to the actual database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

try:
    # Check current columns
    cursor.execute("PRAGMA table_info(groups)")
    columns = [col[1] for col in cursor.fetchall()]
    
    print("Current columns in 'groups' table:", columns)
    print()
    
    # Add site_id column if missing
    if 'site_id' not in columns:
        print("Adding 'site_id' column...")
        cursor.execute("""
            ALTER TABLE groups 
            ADD COLUMN site_id INTEGER
        """)
        print("✓ Added 'site_id' column")
    else:
        print("✓ 'site_id' column already exists")
    
    # Add date_added column if missing
    if 'date_added' not in columns:
        print("Adding 'date_added' column...")
        cursor.execute("""
            ALTER TABLE groups 
            ADD COLUMN date_added DATETIME DEFAULT CURRENT_TIMESTAMP
        """)
        print("✓ Added 'date_added' column")
    else:
        print("✓ 'date_added' column already exists")
    
    # Add province column if missing
    if 'province' not in columns:
        print("Adding 'province' column...")
        cursor.execute("""
            ALTER TABLE groups 
            ADD COLUMN province VARCHAR(100)
        """)
        print("✓ Added 'province' column")
    else:
        print("✓ 'province' column already exists")
    
    # Commit the changes
    conn.commit()
    print("\n✅ Database schema updated successfully!")
    
    # Verify
    cursor.execute("PRAGMA table_info(groups)")
    columns_after = cursor.fetchall()
    print("\nUpdated columns in 'groups' table:")
    for col in columns_after:
        print(f"  - {col[1]} ({col[2]})")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    conn.rollback()
finally:
    conn.close()

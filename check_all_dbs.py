"""
Check all database files to find which one has the groups table
"""
import sqlite3
import os

db_files = ['app.db', 'database.db', 'lns_app.db']

for db_file in db_files:
    if os.path.exists(db_file):
        print(f"\n{'='*60}")
        print(f"Checking: {db_file}")
        print(f"Size: {os.path.getsize(db_file)} bytes")
        print('='*60)
        
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Tables: {len(tables)}")
            
            # Check if groups table exists
            if any('groups' in table for table in tables):
                cursor.execute("PRAGMA table_info(groups)")
                columns = cursor.fetchall()
                print(f"\n✓ Groups table found with {len(columns)} columns:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
            else:
                print("\n✗ No groups table found")
            
            conn.close()
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"\n{db_file} does not exist")

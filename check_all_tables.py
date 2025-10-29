"""
Check which database file has the auth tables
"""
import sqlite3
import os

db_files = ['database.db', 'app.db', 'lns_app.db']

for db_file in db_files:
    if os.path.exists(db_file):
        print(f"\n{'='*60}")
        print(f"Database: {db_file}")
        print(f"Size: {os.path.getsize(db_file)} bytes")
        print('='*60)
        
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            
            print(f"Tables ({len(tables)}):")
            for table in tables:
                print(f"  - {table}")
            
            # Check specifically for auth tables
            auth_tables = ['users', 'roles', 'permissions', 'user_roles']
            found_auth = [t for t in auth_tables if t in tables]
            
            if found_auth:
                print(f"\n✓ Found auth tables: {found_auth}")
                
                # Check users
                if 'users' in tables:
                    cursor.execute("SELECT COUNT(*) FROM users")
                    user_count = cursor.fetchone()[0]
                    print(f"  Users count: {user_count}")
            
            conn.close()
        except Exception as e:
            print(f"Error: {e}")

"""
Check existing users and create super admin if needed
"""
import sqlite3

# Connect to the database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

try:
    # Check if users table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        print("❌ Users table doesn't exist yet!")
        print("Run init_db.py first to create all tables.")
    else:
        # Check existing users
        cursor.execute("SELECT id, username, email, is_active FROM users")
        users = cursor.fetchall()
        
        if users:
            print(f"Found {len(users)} user(s) in database:")
            print("-" * 60)
            for user in users:
                print(f"ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Active: {user[3]}")
        else:
            print("No users found in database.")
        
        # Check roles table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='roles'")
        if cursor.fetchone():
            cursor.execute("SELECT id, name, description FROM roles")
            roles = cursor.fetchall()
            print(f"\nFound {len(roles)} role(s):")
            print("-" * 60)
            for role in roles:
                print(f"ID: {role[0]}, Name: {role[1]}, Description: {role[2]}")
        
        # Check sites table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sites'")
        if cursor.fetchone():
            cursor.execute("SELECT id, name, code FROM sites")
            sites = cursor.fetchall()
            print(f"\nFound {len(sites)} site(s):")
            print("-" * 60)
            for site in sites:
                print(f"ID: {site[0]}, Name: {site[1]}, Code: {site[2]}")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()

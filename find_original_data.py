"""
Search all database files including instance folder for original data
"""
import sqlite3
import os

db_paths = [
    'database.db',
    'app.db',
    'lns_app.db',
    'instance/database.db',
    'instance/app.db',
    'instance/app.backup.db'
]

print("Searching for your original data...\n")

for db_path in db_paths:
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"{'='*70}")
        print(f"📁 {db_path}")
        print(f"Size: {size:,} bytes")
        print('='*70)
        
        if size == 0:
            print("  Empty file (0 bytes)\n")
            continue
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check for data in key tables
            data_found = False
            
            tables_to_check = [
                ('groups', 'SELECT COUNT(*) FROM groups'),
                ('students', 'SELECT COUNT(*) FROM students'),
                ('machines', 'SELECT COUNT(*) FROM machines'),
                ('modules', 'SELECT COUNT(*) FROM modules'),
                ('lecturers', 'SELECT COUNT(*) FROM lecturers'),
                ('sites', 'SELECT COUNT(*) FROM sites'),
                ('users', 'SELECT COUNT(*) FROM users'),
                ('schedule', 'SELECT COUNT(*) FROM schedule')
            ]
            
            for table, query in tables_to_check:
                try:
                    cursor.execute(query)
                    count = cursor.fetchone()[0]
                    if count > 0:
                        print(f"  ✅ {table}: {count} records")
                        data_found = True
                    else:
                        print(f"     {table}: 0 records")
                except:
                    pass
            
            if data_found:
                print(f"\n  🎯 ** FOUND ORIGINAL DATA IN THIS FILE! **")
                
                # Show sample data
                try:
                    cursor.execute("SELECT id, name FROM sites LIMIT 10")
                    sites = cursor.fetchall()
                    if sites:
                        print(f"\n  Sites found:")
                        for site in sites:
                            print(f"    - ID {site[0]}: {site[1]}")
                except:
                    pass
                
                try:
                    cursor.execute("SELECT id, student_name FROM students LIMIT 10")
                    students = cursor.fetchall()
                    if students:
                        print(f"\n  Sample students:")
                        for student in students:
                            print(f"    - ID {student[0]}: {student[1]}")
                except:
                    pass
                
                try:
                    cursor.execute("SELECT id, name FROM groups LIMIT 10")
                    groups = cursor.fetchall()
                    if groups:
                        print(f"\n  Groups:")
                        for group in groups:
                            print(f"    - ID {group[0]}: {group[1]}")
                except:
                    pass
            
            conn.close()
            print()
            
        except Exception as e:
            print(f"  Error: {e}\n")
    else:
        print(f"❌ {db_path} - File not found\n")

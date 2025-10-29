"""
Find which database has the actual data
"""
import sqlite3
import os

db_files = ['database.db', 'app.db', 'lns_app.db']

print("Searching for your data across all database files...\n")

for db_file in db_files:
    if os.path.exists(db_file):
        print(f"{'='*60}")
        print(f"📁 {db_file} ({os.path.getsize(db_file)} bytes)")
        print('='*60)
        
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Check for data in key tables
            tables_to_check = {
                'groups': 'SELECT COUNT(*) FROM groups',
                'students': 'SELECT COUNT(*) FROM students',
                'machines': 'SELECT COUNT(*) FROM machines',
                'modules': 'SELECT COUNT(*) FROM modules',
                'lecturers': 'SELECT COUNT(*) FROM lecturers',
                'sites': 'SELECT COUNT(*) FROM sites',
                'users': 'SELECT COUNT(*) FROM users'
            }
            
            has_data = False
            for table, query in tables_to_check.items():
                try:
                    cursor.execute(query)
                    count = cursor.fetchone()[0]
                    if count > 0:
                        print(f"  ✓ {table}: {count} records")
                        has_data = True
                    else:
                        print(f"    {table}: 0 records")
                except:
                    print(f"    {table}: table not found")
            
            if has_data:
                print(f"\n🎯 FOUND DATA IN THIS DATABASE!")
                
                # Show some sample data
                try:
                    cursor.execute("SELECT id, name FROM sites LIMIT 5")
                    sites = cursor.fetchall()
                    if sites:
                        print(f"\n  Sites in this database:")
                        for site in sites:
                            print(f"    - ID {site[0]}: {site[1]}")
                except:
                    pass
                
                try:
                    cursor.execute("SELECT id, student_name FROM students LIMIT 5")
                    students = cursor.fetchall()
                    if students:
                        print(f"\n  Sample students:")
                        for student in students:
                            print(f"    - ID {student[0]}: {student[1]}")
                except:
                    pass
            
            conn.close()
            print()
            
        except Exception as e:
            print(f"  Error: {e}\n")

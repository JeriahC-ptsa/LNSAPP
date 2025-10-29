"""
Verify Migration Script
Checks if new tables exist and shows their structure
"""

from app import app, db
from sqlalchemy import inspect

def verify_migration():
    """Verify new tables were created"""
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print("=" * 60)
        print("DATABASE VERIFICATION")
        print("=" * 60)
        
        # Check for new tables
        new_tables = ['attempts', 'student_module_progress']
        
        for table_name in new_tables:
            if table_name in tables:
                print(f"\n✓ Table '{table_name}' exists")
                print("-" * 60)
                
                # Get columns
                columns = inspector.get_columns(table_name)
                print(f"  Columns ({len(columns)}):")
                for col in columns:
                    col_type = str(col['type'])
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    print(f"    - {col['name']:<20} {col_type:<15} {nullable}")
                
                # Get foreign keys
                fks = inspector.get_foreign_keys(table_name)
                if fks:
                    print(f"\n  Foreign Keys ({len(fks)}):")
                    for fk in fks:
                        print(f"    - {fk['constrained_columns']} → {fk['referred_table']}.{fk['referred_columns']}")
            else:
                print(f"\n✗ Table '{table_name}' NOT FOUND")
        
        print("\n" + "=" * 60)
        print("All existing tables:")
        print("=" * 60)
        for table in sorted(tables):
            print(f"  - {table}")
        
        print("\n" + "=" * 60)
        print("VERIFICATION COMPLETE")
        print("=" * 60)

if __name__ == "__main__":
    verify_migration()

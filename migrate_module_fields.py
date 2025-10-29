"""
Add new fields to Module table
- code
- category
- status_type
- credits
"""

from app import app, db
from sqlalchemy import text

def migrate_module_fields():
    """Add new columns to modules table"""
    with app.app_context():
        print("=" * 80)
        print("MIGRATING MODULE TABLE - ADDING NEW FIELDS")
        print("=" * 80)
        
        try:
            # Check if columns already exist
            inspector = db.inspect(db.engine)
            existing_columns = [col['name'] for col in inspector.get_columns('modules')]
            
            new_columns = {
                'code': 'VARCHAR(100)',
                'category': 'VARCHAR(100)',
                'status_type': 'VARCHAR(20)',
                'credits': 'VARCHAR(20)'
            }
            
            for column_name, column_type in new_columns.items():
                if column_name in existing_columns:
                    print(f"  ⊘ SKIP: Column '{column_name}' already exists")
                else:
                    # Add the column
                    with db.engine.connect() as conn:
                        conn.execute(text(f"ALTER TABLE modules ADD COLUMN {column_name} {column_type}"))
                        conn.commit()
                    print(f"  ✓ ADDED: Column '{column_name}' ({column_type})")
            
            print("\n" + "=" * 80)
            print("✓ MIGRATION COMPLETE!")
            print("=" * 80)
            print("\nNew Module fields:")
            print("  - code: Module code (e.g., 652201-000-01-00-KM-01)")
            print("  - category: FUNDAMENTALS, TOOLING U, THEORY MODULES, PRACTICAL MODULES")
            print("  - status_type: P/NYP (Pass/Not Yet Passed) or C/NYC (Complete/Not Yet Complete)")
            print("  - credits: Percentage credits (e.g., 75%, 60%)")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n✗ ERROR: {str(e)}")
            return False
        
        return True

if __name__ == "__main__":
    migrate_module_fields()

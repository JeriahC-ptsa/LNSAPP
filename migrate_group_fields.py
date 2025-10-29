"""
Migration script to add date_added and province columns to the groups table
"""
from app import app, db
from models import Group
from sqlalchemy import text
from datetime import datetime

def migrate_group_fields():
    """Add date_added and province columns to groups table"""
    with app.app_context():
        print("Starting migration: Add date_added and province columns to groups...")
        
        # Step 1: Add the columns if they don't exist
        try:
            with db.engine.connect() as conn:
                # Check if columns exist
                result = conn.execute(text("PRAGMA table_info(groups)"))
                columns = [row[1] for row in result]
                
                # Add date_added column
                if 'date_added' not in columns:
                    print("Adding date_added column...")
                    conn.execute(text("ALTER TABLE groups ADD COLUMN date_added DATETIME"))
                    conn.commit()
                    print("✓ date_added column added successfully")
                else:
                    print("✓ date_added column already exists")
                
                # Add province column
                if 'province' not in columns:
                    print("Adding province column...")
                    conn.execute(text("ALTER TABLE groups ADD COLUMN province VARCHAR(100)"))
                    conn.commit()
                    print("✓ province column added successfully")
                else:
                    print("✓ province column already exists")
                    
        except Exception as e:
            print(f"Error adding columns: {e}")
            return
        
        # Step 2: Set default date_added for existing groups
        print("\nSetting default date_added for existing groups...")
        groups = Group.query.filter(Group.date_added.is_(None)).all()
        
        if groups:
            updated_count = 0
            default_date = datetime.utcnow()
            
            for group in groups:
                group.date_added = default_date
                updated_count += 1
                print(f"  Updated group: {group.name} - set date_added to {default_date.strftime('%Y-%m-%d')}")
            
            # Commit all changes
            try:
                db.session.commit()
                print(f"\n✓ Migration completed successfully!")
                print(f"  - Updated {updated_count} groups with default date_added")
                print(f"  - Total groups: {Group.query.count()}")
            except Exception as e:
                db.session.rollback()
                print(f"\n✗ Error during migration: {e}")
        else:
            print("  No groups need updating")
            print(f"\n✓ Migration completed successfully!")
            print(f"  - Total groups: {Group.query.count()}")

if __name__ == "__main__":
    migrate_group_fields()

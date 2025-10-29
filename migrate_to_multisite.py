"""
Multi-Site Migration Script
===========================
This script helps migrate your existing single-site data to multi-site structure.

WARNING: Backup your database before running this script!

Usage:
    python migrate_to_multisite.py
"""

from app import app
from models import db, Site, Group, Student, Lecturer, Machine, Module, Inventory
from models import InventoryUsage, Schedule, OverheadCost, MachineMaintenance, MacroPlan
from auth_models import User
from datetime import datetime
import sys

def create_default_site():
    """Create the default site if it doesn't exist"""
    print("\n" + "="*60)
    print("STEP 1: Creating Default Site")
    print("="*60)
    
    # Check if site already exists
    existing_site = Site.query.first()
    if existing_site:
        print(f"✓ Site already exists: {existing_site.name} (ID: {existing_site.id})")
        return existing_site
    
    # Get site details from user
    print("\nPlease provide details for your default site:")
    name = input("Site Name (e.g., 'Main Campus'): ").strip() or "Main Campus"
    code = input("Site Code (e.g., 'MAIN'): ").strip().upper() or "MAIN"
    location = input("Location (e.g., 'Johannesburg'): ").strip() or "Johannesburg"
    address = input("Address (optional): ").strip() or ""
    phone = input("Phone (optional): ").strip() or ""
    email = input("Email (optional): ").strip() or ""
    
    # Create site
    default_site = Site(
        name=name,
        code=code,
        location=location,
        address=address,
        phone=phone,
        email=email,
        is_active=True,
        created_date=datetime.utcnow()
    )
    
    try:
        db.session.add(default_site)
        db.session.commit()
        print(f"\n✓ Created site: {default_site.name} (ID: {default_site.id})")
        return default_site
    except Exception as e:
        db.session.rollback()
        print(f"\n✗ Error creating site: {e}")
        sys.exit(1)

def assign_data_to_site(site_id):
    """Assign all existing data to the default site"""
    print("\n" + "="*60)
    print("STEP 2: Assigning Existing Data to Site")
    print("="*60)
    
    models_to_update = [
        ('Groups', Group),
        ('Students', Student),
        ('Lecturers', Lecturer),
        ('Machines', Machine),
        ('Modules', Module),
        ('Inventory', Inventory),
        ('Inventory Usage', InventoryUsage),
        ('Schedules', Schedule),
        ('Overhead Costs', OverheadCost),
        ('Machine Maintenance', MachineMaintenance),
        ('Macro Plans', MacroPlan),
    ]
    
    total_updated = 0
    
    for model_name, model_class in models_to_update:
        try:
            # Count records without site_id
            count = model_class.query.filter(
                (model_class.site_id == None) | (model_class.site_id == 0)
            ).count()
            
            if count > 0:
                # Update all records
                model_class.query.filter(
                    (model_class.site_id == None) | (model_class.site_id == 0)
                ).update({model_class.site_id: site_id})
                
                db.session.commit()
                print(f"✓ Updated {count:4d} {model_name}")
                total_updated += count
            else:
                print(f"  Skipped       {model_name} (already assigned)")
                
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error updating {model_name}: {e}")
    
    print(f"\n✓ Total records updated: {total_updated}")

def assign_users_to_site(site_id):
    """Assign all users to the default site"""
    print("\n" + "="*60)
    print("STEP 3: Assigning Users to Site")
    print("="*60)
    
    site = Site.query.get(site_id)
    users = User.query.all()
    
    assigned_count = 0
    already_assigned = 0
    
    for user in users:
        if site not in user.sites:
            user.sites.append(site)
            assigned_count += 1
        else:
            already_assigned += 1
    
    try:
        db.session.commit()
        print(f"✓ Assigned {assigned_count} users to site")
        if already_assigned > 0:
            print(f"  {already_assigned} users already assigned")
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error assigning users: {e}")

def verify_migration(site_id):
    """Verify that migration was successful"""
    print("\n" + "="*60)
    print("STEP 4: Verification")
    print("="*60)
    
    site = Site.query.get(site_id)
    print(f"\n✓ Site: {site.name} (ID: {site.id})")
    
    # Count records per model
    counts = {
        'Groups': Group.query.filter_by(site_id=site_id).count(),
        'Students': Student.query.filter_by(site_id=site_id).count(),
        'Lecturers': Lecturer.query.filter_by(site_id=site_id).count(),
        'Machines': Machine.query.filter_by(site_id=site_id).count(),
        'Modules': Module.query.filter_by(site_id=site_id).count(),
        'Inventory': Inventory.query.filter_by(site_id=site_id).count(),
        'Schedules': Schedule.query.filter_by(site_id=site_id).count(),
    }
    
    print("\nData assigned to site:")
    for model_name, count in counts.items():
        print(f"  - {model_name:20s}: {count:4d} records")
    
    # Check users
    users_with_site = len([u for u in User.query.all() if site in u.sites])
    total_users = User.query.count()
    print(f"\n  - Users with access   : {users_with_site}/{total_users}")
    
    # Check for orphaned records
    print("\nChecking for orphaned records:")
    orphaned = False
    for model_name, count in counts.items():
        model_class = globals()[model_name.replace(' ', '').rstrip('s')]
        orphan_count = model_class.query.filter(
            (model_class.site_id == None) | (model_class.site_id == 0)
        ).count()
        if orphan_count > 0:
            print(f"  ⚠ {model_name}: {orphan_count} orphaned records")
            orphaned = True
    
    if not orphaned:
        print("  ✓ No orphaned records found")
    
    print("\n" + "="*60)
    print("Migration Complete!")
    print("="*60)
    print("\nNext Steps:")
    print("1. Restart your Flask application")
    print("2. Log in and verify data appears correctly")
    print("3. Test creating new records")
    print("4. Review MULTI_SITE_IMPLEMENTATION.md for code updates")
    print("\n")

def main():
    """Main migration function"""
    print("\n" + "="*60)
    print("MULTI-SITE MIGRATION TOOL")
    print("="*60)
    print("\n⚠️  WARNING: This will modify your database!")
    print("Make sure you have a backup before proceeding.")
    
    response = input("\nDo you want to continue? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Migration cancelled.")
        sys.exit(0)
    
    with app.app_context():
        try:
            # Step 1: Create default site
            default_site = create_default_site()
            
            # Step 2: Assign data to site
            assign_data_to_site(default_site.id)
            
            # Step 3: Assign users to site
            assign_users_to_site(default_site.id)
            
            # Step 4: Verify migration
            verify_migration(default_site.id)
            
        except KeyboardInterrupt:
            print("\n\nMigration interrupted by user.")
            db.session.rollback()
            sys.exit(1)
        except Exception as e:
            print(f"\n\n✗ Migration failed: {e}")
            db.session.rollback()
            sys.exit(1)

if __name__ == '__main__':
    main()

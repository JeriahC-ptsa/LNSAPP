"""
Check admin user's access and fix if needed
"""
from app import app, db
from auth_models import User, Role
from models import Site, Group, Student, Machine

with app.app_context():
    # Check admin user
    admin = User.query.filter_by(username='admin').first()
    
    if not admin:
        print("❌ Admin user not found!")
    else:
        print("✓ Admin user found")
        print(f"  Username: {admin.username}")
        print(f"  Email: {admin.email}")
        print(f"  Active: {admin.active}")
        print(f"  Roles: {[role.name for role in admin.roles]}")
        print(f"  Is Super Admin: {admin.is_super_admin()}")
        print(f"  Sites assigned: {len(admin.sites)}")
        
        if admin.sites:
            print("  Sites:")
            for site in admin.sites:
                print(f"    - {site.name} ({site.code})")
        else:
            print("  ⚠️  No sites assigned to admin!")
        
        # Check all available sites
        all_sites = Site.query.all()
        print(f"\n📍 Total sites in database: {len(all_sites)}")
        for site in all_sites:
            print(f"  - {site.name} ({site.code}) - Active: {site.is_active}")
        
        # Check data counts
        print(f"\n📊 Data in database:")
        print(f"  Groups: {Group.query.count()}")
        print(f"  Students: {Student.query.count()}")
        print(f"  Machines: {Machine.query.count()}")
        
        # Assign admin to all sites if not already assigned
        if not admin.sites and all_sites:
            print("\n🔧 Fixing: Assigning admin to all sites...")
            for site in all_sites:
                if site not in admin.sites:
                    admin.sites.append(site)
            db.session.commit()
            print("✅ Admin now has access to all sites")
        
        # Check permissions
        print(f"\n🔑 Permissions check:")
        if admin.roles:
            for role in admin.roles:
                print(f"  Role: {role.name}")
                print(f"  Permissions: {len(role.permissions)}")
                if role.permissions:
                    for perm in role.permissions[:5]:  # Show first 5
                        print(f"    - {perm.name} ({perm.resource}/{perm.action})")

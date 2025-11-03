"""
Ensure all roles have all available permissions assigned
"""
from app import app, db
from auth_models import Role, Permission

with app.app_context():
    print("Syncing all permissions to all roles...\n")
    
    # Get all roles
    roles = Role.query.all()
    
    # Get all permissions
    all_permissions = Permission.query.all()
    
    print(f"Found {len(roles)} roles and {len(all_permissions)} permissions\n")
    
    # Show all available permissions
    print("Available Permissions:")
    print("=" * 70)
    for perm in all_permissions:
        print(f"  - {perm.name} ({perm.resource}/{perm.action})")
    print()
    
    # Assign all permissions to each role
    for role in roles:
        initial_count = len(role.permissions)
        added = 0
        
        for perm in all_permissions:
            if perm not in role.permissions:
                role.permissions.append(perm)
                added += 1
        
        db.session.commit()
        
        final_count = len(role.permissions)
        print(f"{role.name}:")
        print(f"  - Initial permissions: {initial_count}")
        print(f"  - Added: {added}")
        print(f"  - Total permissions: {final_count}")
        print()
    
    print("=" * 70)
    print("Summary:")
    print("=" * 70)
    for role in roles:
        print(f"{role.name}: {len(role.permissions)} permissions")
    
    print("\nOK All roles now have all available permissions!")

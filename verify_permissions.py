"""
Verify all roles have all permissions
"""
from app import app, db
from auth_models import Role, Permission

with app.app_context():
    print("Verifying role permissions...\n")
    
    roles = Role.query.all()
    all_permissions = Permission.query.all()
    
    print(f"Total permissions in system: {len(all_permissions)}\n")
    
    print("=" * 70)
    print("Role Permission Counts:")
    print("=" * 70)
    
    for role in roles:
        perm_count = len(role.permissions)
        status = "OK" if perm_count == len(all_permissions) else "MISSING"
        print(f"{role.name:20} {perm_count:3} permissions  [{status}]")
    
    print("\n" + "=" * 70)
    
    # Check if all roles have the same permissions
    all_equal = all(len(role.permissions) == len(all_permissions) for role in roles)
    
    if all_equal:
        print("OK All roles have ALL {0} permissions!".format(len(all_permissions)))
    else:
        print("WARNING: Some roles are missing permissions")
        print("\nTo fix, run: python sync_all_permissions.py")

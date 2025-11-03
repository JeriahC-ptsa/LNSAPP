"""
Add missing admin permissions for manage_users and manage_fields
"""
from app import app, db
from auth_models import User, Role, Permission

with app.app_context():
    print("Adding missing admin permissions...\n")
    
    # Get Super Admin role
    super_admin = Role.query.filter_by(name='Super Admin').first()
    
    if not super_admin:
        print("❌ Super Admin role not found!")
        exit(1)
    
    # Define admin permissions that are missing
    admin_permissions = [
        {
            'name': 'manage_users',
            'type': 'action',
            'resource': 'users',
            'action': 'manage',
            'description': 'Manage users, roles, and permissions'
        },
        {
            'name': 'manage_fields',
            'type': 'action',
            'resource': 'dynamic_fields',
            'action': 'manage',
            'description': 'Manage dynamic fields'
        },
        {
            'name': 'manage_roles',
            'type': 'action',
            'resource': 'roles',
            'action': 'manage',
            'description': 'Manage roles and permissions'
        },
        {
            'name': 'admin_access',
            'type': 'page_access',
            'resource': 'admin',
            'action': 'view',
            'description': 'Access to admin panel'
        }
    ]
    
    created = 0
    assigned = 0
    
    for perm_data in admin_permissions:
        # Check if permission exists
        perm = Permission.query.filter_by(name=perm_data['name']).first()
        
        if not perm:
            perm = Permission(
                name=perm_data['name'],
                type=perm_data['type'],
                resource=perm_data['resource'],
                action=perm_data['action'],
                description=perm_data['description']
            )
            db.session.add(perm)
            db.session.flush()
            created += 1
            print(f"✓ Created permission: {perm_data['name']}")
        else:
            print(f"  Permission exists: {perm_data['name']}")
        
        # Assign to Super Admin if not already assigned
        if perm not in super_admin.permissions:
            super_admin.permissions.append(perm)
            assigned += 1
            print(f"  > Assigned to Super Admin")
    
    db.session.commit()
    
    print(f"\nOK Created {created} new permissions")
    print(f"OK Assigned {assigned} permissions to Super Admin")
    print(f"OK Super Admin now has {len(super_admin.permissions)} total permissions")
    
    # Verify admin user
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print(f"\nAdmin user verification:")
        print(f"  - Username: {admin.username}")
        print(f"  - Is super admin: {admin.is_super_admin()}")
        print(f"  - Has manage_users permission: {admin.has_permission('manage_users')}")
        print(f"  - Has manage_fields permission: {admin.has_permission('manage_fields')}")
        print(f"  - Has manage_roles permission: {admin.has_permission('manage_roles')}")
        print(f"  - Has admin_access permission: {admin.has_permission('admin_access')}")
    
    print("\nOK All admin permissions added! You can now access:")
    print("  - Admin -> Manage Users")
    print("  - Admin -> Roles & Permissions")
    print("  - Admin -> Dynamic Fields")

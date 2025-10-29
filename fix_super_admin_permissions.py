"""
Grant Super Admin all permissions by modifying has_page_access to always return True for super admins
OR create all necessary permissions and assign them to Super Admin role
"""
from app import app, db
from auth_models import User, Role, Permission

with app.app_context():
    # Get Super Admin role
    super_admin_role = Role.query.filter_by(name='Super Admin').first()
    
    if not super_admin_role:
        print("❌ Super Admin role not found!")
        exit(1)
    
    print("Creating permissions for all pages...")
    
    # Define all page access permissions
    pages = [
        'students', 'groups', 'machines', 'inventory', 'modules', 
        'lecturers', 'schedule', 'reports', 'overheads', 'macroplan',
        'management', 'users', 'sites', 'settings'
    ]
    
    created = 0
    assigned = 0
    
    for page in pages:
        # Create permission if it doesn't exist
        perm = Permission.query.filter_by(
            name=f'{page}_access',
            type='page_access',
            resource=page
        ).first()
        
        if not perm:
            perm = Permission(
                name=f'{page}_access',
                type='page_access',
                resource=page,
                action='view',
                description=f'Access to {page} page'
            )
            db.session.add(perm)
            created += 1
            print(f"  ✓ Created permission: {page}_access")
        
        # Assign to Super Admin if not already assigned
        if perm not in super_admin_role.permissions:
            super_admin_role.permissions.append(perm)
            assigned += 1
    
    # Also create CRUD permissions for each resource
    actions = ['create', 'read', 'update', 'delete', 'view', 'edit']
    resources = ['students', 'groups', 'machines', 'modules', 'inventory', 'schedule']
    
    for resource in resources:
        for action in actions:
            perm = Permission.query.filter_by(
                resource=resource,
                action=action
            ).first()
            
            if not perm:
                perm = Permission(
                    name=f'{resource}_{action}',
                    type='action',
                    resource=resource,
                    action=action,
                    description=f'{action.title()} {resource}'
                )
                db.session.add(perm)
                created += 1
            
            if perm not in super_admin_role.permissions:
                super_admin_role.permissions.append(perm)
                assigned += 1
    
    db.session.commit()
    
    print(f"\n✅ Created {created} new permissions")
    print(f"✅ Assigned {assigned} permissions to Super Admin")
    print(f"✅ Super Admin now has {len(super_admin_role.permissions)} total permissions")
    
    # Verify admin user
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print(f"\n👤 Admin user:")
        print(f"  - Has {len(admin.sites)} sites")
        print(f"  - Has {len(admin.roles)} roles")
        print(f"  - Is super admin: {admin.is_super_admin()}")
        print(f"  - Can access machines: {admin.has_page_access('machines')}")
        print(f"  - Can access students: {admin.has_page_access('students')}")
        print(f"  - Can access inventory: {admin.has_page_access('inventory')}")

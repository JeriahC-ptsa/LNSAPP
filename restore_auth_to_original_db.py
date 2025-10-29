"""
Add auth tables and admin user to the original database (instance/app.db)
"""
from app import app, db
from auth_models import User, Role, Permission
from models import Site

with app.app_context():
    print("Checking instance/app.db for auth tables and data...\n")
    
    # Create auth tables if they don't exist
    db.create_all()
    print("✅ Auth tables ensured\n")
    
    # Check existing site
    sites = Site.query.all()
    print(f"📍 Sites: {len(sites)}")
    for site in sites:
        print(f"  - {site.name} ({site.code if hasattr(site, 'code') else 'N/A'})")
    
    # Check if Super Admin role exists
    super_admin_role = Role.query.filter_by(name='Super Admin').first()
    if not super_admin_role:
        print("\nCreating Super Admin role...")
        super_admin_role = Role(
            name='Super Admin',
            description='Full system access across all sites'
        )
        db.session.add(super_admin_role)
        db.session.commit()
        print("✅ Super Admin role created")
    else:
        print("\n✓ Super Admin role exists")
    
    # Create permissions
    print("\nCreating/updating permissions...")
    pages = [
        'students', 'groups', 'machines', 'inventory', 'modules', 
        'lecturers', 'schedule', 'reports', 'overheads', 'macroplan',
        'management', 'users', 'sites', 'settings'
    ]
    
    for page in pages:
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
        
        if perm not in super_admin_role.permissions:
            super_admin_role.permissions.append(perm)
    
    # Create CRUD permissions
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
            
            if perm not in super_admin_role.permissions:
                super_admin_role.permissions.append(perm)
    
    db.session.commit()
    print(f"✅ Super Admin has {len(super_admin_role.permissions)} permissions")
    
    # Check/create admin user
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        print("\nCreating admin user...")
        admin_user = User(
            username='admin',
            email='admin@example.com'
        )
        admin_user.active = True
        admin_user.set_password('admin123')
        admin_user.roles.append(super_admin_role)
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Admin user created")
    else:
        print("\n✓ Admin user exists")
        # Ensure admin has Super Admin role
        if super_admin_role not in admin_user.roles:
            admin_user.roles.append(super_admin_role)
            db.session.commit()
            print("✅ Added Super Admin role to admin user")
    
    # Assign admin to all sites
    all_sites = Site.query.all()
    for site in all_sites:
        if site not in admin_user.sites:
            admin_user.sites.append(site)
    db.session.commit()
    print(f"✅ Admin assigned to {len(admin_user.sites)} site(s)")
    
    # Show data counts
    from models import Group, Student, Machine, Module
    print(f"\n📊 Data in instance/app.db:")
    print(f"  Groups: {Group.query.count()}")
    print(f"  Students: {Student.query.count()}")
    print(f"  Machines: {Machine.query.count()}")
    print(f"  Modules: {Module.query.count()}")
    print(f"  Sites: {Site.query.count()}")
    print(f"  Users: {User.query.count()}")
    
    print(f"\n✅ Original database restored with auth tables!")
    print(f"\n{'='*60}")
    print(f"LOGIN CREDENTIALS:")
    print(f"{'='*60}")
    print(f"Username: admin")
    print(f"Password: admin123")
    print(f"{'='*60}")

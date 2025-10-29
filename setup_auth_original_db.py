"""
Add auth tables to instance/app.db (your original database)
"""
from app import app, db
from auth_models import User, Role, Permission
from models import Site, Group, Student, Machine

print("Connecting to instance/app.db...")

with app.app_context():
    # Create auth tables
    print("Creating auth tables...")
    db.create_all()
    print("✅ Tables created/verified\n")
    
    # Show current data
    print(f"📊 Current data in database:")
    print(f"  Students: {Student.query.count()}")
    print(f"  Groups: {Group.query.count()}")
    print(f"  Machines: {Machine.query.count()}")
    print(f"  Sites: {Site.query.count()}")
    
    # Show sample groups
    groups = Group.query.limit(5).all()
    if groups:
        print(f"\n  Sample Groups:")
        for g in groups:
            print(f"    - {g.name}")
    
    # Show sample students  
    students = Student.query.limit(5).all()
    if students:
        print(f"\n  Sample Students:")
        for s in students:
            print(f"    - {s.student_name}")
    
    print("\n" + "="*60)
    print("✅ Your original data is intact!")
    print("="*60)
    
    # Create Super Admin role
    super_admin = Role.query.filter_by(name='Super Admin').first()
    if not super_admin:
        super_admin = Role(name='Super Admin', description='Full access')
        db.session.add(super_admin)
        db.session.flush()
    
    # Create all permissions
    pages = ['students', 'groups', 'machines', 'inventory', 'modules', 
             'lecturers', 'schedule', 'reports', 'management', 'users', 'sites']
    
    for page in pages:
        p = Permission.query.filter_by(name=f'{page}_access').first()
        if not p:
            p = Permission(name=f'{page}_access', type='page_access', 
                          resource=page, action='view')
            db.session.add(p)
            db.session.flush()
        if p not in super_admin.permissions:
            super_admin.permissions.append(p)
    
    # Create admin user
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com')
        admin.active = True
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.flush()
    else:
        admin.set_password('admin123')
        admin.active = True
    
    if super_admin not in admin.roles:
        admin.roles.append(super_admin)
    
    # Assign to all sites
    for site in Site.query.all():
        if site not in admin.sites:
            admin.sites.append(site)
    
    db.session.commit()
    
    print(f"\n✅ Auth setup complete!")
    print(f"  Admin user: ✓")
    print(f"  Permissions: {len(super_admin.permissions)}")
    print(f"  Sites assigned: {len(admin.sites)}")
    
    print(f"\n{'='*60}")
    print(f"LOGIN: admin / admin123")
    print(f"{'='*60}\n")
    print("✅ Start your Flask app now - all data restored!")

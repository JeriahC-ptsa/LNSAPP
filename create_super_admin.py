"""
Create auth tables and super admin user
"""
from app import app, db
from auth_models import User, Role, Permission
from models import Site
from werkzeug.security import generate_password_hash

with app.app_context():
    print("Creating auth tables...")
    db.create_all()
    print("✅ Auth tables created!\n")
    
    # Check if super admin role exists
    super_admin_role = Role.query.filter_by(name='Super Admin').first()
    if not super_admin_role:
        print("Creating Super Admin role...")
        super_admin_role = Role(
            name='Super Admin',
            description='Full system access across all sites'
        )
        db.session.add(super_admin_role)
        db.session.commit()
        print("✅ Super Admin role created")
    else:
        print("✓ Super Admin role already exists")
    
    # Check if admin user exists
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        print("\nCreating admin user...")
        admin_user = User(
            username='admin',
            email='admin@example.com'
        )
        admin_user.active = True  # Set active field directly
        admin_user.set_password('admin123')
        admin_user.roles.append(super_admin_role)
        
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Admin user created successfully!")
        print("\n" + "="*60)
        print("LOGIN CREDENTIALS:")
        print("="*60)
        print("Username: admin")
        print("Password: admin123")
        print("="*60)
    else:
        print("\n✓ Admin user already exists")
        # Update password if needed
        admin_user.set_password('admin123')
        admin_user.active = True
        if super_admin_role not in admin_user.roles:
            admin_user.roles.append(super_admin_role)
        db.session.commit()
        print("✅ Password reset to: admin123")
    
    # Create a default site if none exists
    site = Site.query.first()
    if not site:
        print("\nNo sites found. Creating default site...")
        default_site = Site(
            name='Main Campus',
            code='MAIN',
            location='Head Office'
        )
        default_site.is_active = True
        db.session.add(default_site)
        db.session.commit()
        print("✅ Default site created")
    
    print("\n✅ Setup complete! You can now log in with admin/admin123")

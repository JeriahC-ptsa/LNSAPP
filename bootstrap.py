"""
Bootstrap module for initializing database and ensuring super admin exists on startup
"""
import logging
from flask import current_app
from models import db, Site
from auth_models import User, Role

log = logging.getLogger("wsgi")

def ensure_super_admin():
    """
    Ensures database tables exist and creates/updates super admin user.
    This runs on application startup to guarantee admin access.
    """
    with current_app.app_context():
        # Create all tables if they don't exist
        db.create_all()
        log.info("✓ Database tables created/verified")
        
        # Ensure Super Admin role exists
        role = Role.query.filter_by(name="Super Admin").first()
        if not role:
            role = Role(name="Super Admin", description="Full system access across all sites")
            db.session.add(role)
            db.session.flush()  # Get the role ID
        
        # Ensure admin user exists and is active
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(username="admin", email="admin@example.com")
            admin.set_password("admin123")
            admin.active = True
            admin.roles.append(role)
            db.session.add(admin)
        else:
            # Update existing admin: ensure active and has correct role
            admin.active = True
            admin.set_password("admin123")  # Reset password for consistency
            if role not in admin.roles:
                admin.roles.append(role)
        
        # Ensure at least one site exists
        site = Site.query.first()
        if not site:
            site = Site(name="Main Campus", code="MAIN", location="Head Office")
            site.is_active = True
            db.session.add(site)
        
        # Commit all changes
        db.session.commit()
        
        # Log admin user count
        admin_count = User.query.filter(User.roles.any(Role.name.in_(["Super Admin", "Admin"]))).count()
        log.info("✓ Found %s admin user(s)", admin_count)

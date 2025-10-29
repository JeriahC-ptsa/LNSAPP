# init_auth.py
from app import app, db
from auth_models import User, Role, Permission

def init_auth_system():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if admin exists
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            print("Admin user already exists.")
            return
        
        # Create permissions
        permissions_data = [
            # Page access permissions
            {'name': 'access_dashboard', 'type': 'page_access', 'resource': 'index', 'description': 'Access to dashboard'},
            {'name': 'access_machines', 'type': 'page_access', 'resource': 'machines_list', 'description': 'Access to machines page'},
            {'name': 'access_maintenance', 'type': 'page_access', 'resource': 'maintenance_dashboard', 'description': 'Access to maintenance'},
            {'name': 'access_inventory', 'type': 'page_access', 'resource': 'inventory_list', 'description': 'Access to inventory'},
            {'name': 'access_overheads', 'type': 'page_access', 'resource': 'overheads_dashboard', 'description': 'Access to overheads'},
            {'name': 'access_macroplan', 'type': 'page_access', 'resource': 'macroplan_page', 'description': 'Access to macroplan'},
            {'name': 'access_modules', 'type': 'page_access', 'resource': 'modules_page', 'description': 'Access to modules'},
            {'name': 'access_lecturers', 'type': 'page_access', 'resource': 'lecturers_page', 'description': 'Access to lecturers'},
            {'name': 'access_schedule', 'type': 'page_access', 'resource': 'view_schedule', 'description': 'Access to schedule'},
            {'name': 'access_students', 'type': 'page_access', 'resource': 'list_students', 'description': 'Access to students'},
            {'name': 'access_groups', 'type': 'page_access', 'resource': 'groups_list', 'description': 'Access to groups'},
            {'name': 'access_reports', 'type': 'page_access', 'resource': 'reports', 'description': 'Access to reports'},
            
            # Management permissions
            {'name': 'manage_users', 'type': 'action', 'resource': 'users', 'description': 'Manage user accounts'},
            {'name': 'manage_roles', 'type': 'action', 'resource': 'roles', 'description': 'Manage roles'},
            {'name': 'manage_permissions', 'type': 'action', 'resource': 'permissions', 'description': 'Manage permissions'},
            {'name': 'manage_fields', 'type': 'action', 'resource': 'dynamic_fields', 'description': 'Manage dynamic fields'},
            
            # Action permissions
            {'name': 'create_schedule', 'type': 'action', 'resource': 'schedule', 'description': 'Create schedules'},
            {'name': 'edit_students', 'type': 'action', 'resource': 'students', 'description': 'Edit student data'},
            {'name': 'export_data', 'type': 'action', 'resource': 'data', 'description': 'Export data'},
            {'name': 'import_data', 'type': 'action', 'resource': 'data', 'description': 'Import data'},
        ]
        
        permissions = []
        for perm_data in permissions_data:
            perm = Permission(**perm_data)
            db.session.add(perm)
            permissions.append(perm)
        
        db.session.commit()
        
        # Create roles
        # Admin role with all permissions
        admin_role = Role(name='Admin', description='Full system access')
        admin_role.permissions = permissions
        db.session.add(admin_role)
        
        # Manager role with most permissions except user management
        manager_perms = [p for p in permissions if not p.name.startswith('manage_')]
        manager_role = Role(name='Manager', description='Manage operations')
        manager_role.permissions = manager_perms
        db.session.add(manager_role)
        
        # Viewer role with read-only access
        viewer_perms = [p for p in permissions if p.type == 'page_access' and not p.name.startswith('manage_')]
        viewer_role = Role(name='Viewer', description='View-only access')
        viewer_role.permissions = viewer_perms
        db.session.add(viewer_role)
        
        # Lecturer role
        lecturer_perms = [p for p in permissions if p.resource in ['schedule', 'students', 'modules', 'groups']]
        lecturer_role = Role(name='Lecturer', description='Lecturer access')
        lecturer_role.permissions = lecturer_perms
        db.session.add(lecturer_role)
        
        db.session.commit()
        
        # Create admin user
        admin_user = User(username='admin', email='admin@ptsa.com')
        admin_user.set_password('admin123')  # Change this password!
        admin_user.roles.append(admin_role)
        db.session.add(admin_user)
        
        db.session.commit()
        
        print("Authentication system initialized successfully!")
        print("Admin user created:")
        print("  Username: admin")
        print("  Password: admin123")
        print("  ** PLEASE CHANGE THE PASSWORD AFTER FIRST LOGIN **")

if __name__ == '__main__':
    init_auth_system()

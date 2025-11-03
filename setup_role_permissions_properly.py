"""
Set up proper role-based permissions
Each role gets appropriate permissions based on their level
"""
from app import app, db
from auth_models import Role, Permission

with app.app_context():
    print("Setting up role-based permissions properly...\n")
    
    # Get all permissions
    all_permissions = Permission.query.all()
    
    # Define permission sets for each role
    role_permissions = {
        'Super Admin': 'ALL',  # Gets all permissions
        'Admin': 'ALL',  # Gets all permissions (same as Super Admin)
        'Manager': [
            # Page access
            'students_access', 'groups_access', 'machines_access', 'inventory_access',
            'modules_access', 'lecturers_access', 'schedule_access', 'reports_access',
            'management_access', 'overheads_access', 'macroplan_access',
            # Actions
            'access_dashboard', 'access_students', 'access_groups', 'access_machines',
            'access_inventory', 'access_modules', 'access_lecturers', 'access_schedule',
            'access_reports', 'access_overheads', 'access_macroplan',
            # CRUD operations
            'students_create', 'students_edit', 'students_delete',
            'modules_create', 'modules_edit', 'modules_delete', 'modules_assign',
            'create_schedule', 'edit_students',
            'reports_generate', 'reports_export',
            'import_data', 'export_data'
        ],
        'Viewer': [
            # Page access (read-only)
            'students_access', 'groups_access', 'machines_access', 'inventory_access',
            'modules_access', 'lecturers_access', 'schedule_access', 'reports_access',
            'access_dashboard', 'access_students', 'access_groups', 'access_machines',
            'access_inventory', 'access_modules', 'access_lecturers', 'access_schedule',
            'access_reports',
            'reports_generate', 'reports_export', 'export_data'
        ],
        'Lecturer': [
            # Limited access for lecturers
            'students_access', 'groups_access', 'modules_access', 'schedule_access',
            'access_dashboard', 'access_students', 'access_schedule',
            'lecturers_access', 'access_lecturers'
        ]
    }
    
    # Apply permissions to each role
    for role in Role.query.all():
        role.permissions.clear()  # Clear existing permissions
        
        if role.name in role_permissions:
            if role_permissions[role.name] == 'ALL':
                # Assign all permissions
                for perm in all_permissions:
                    role.permissions.append(perm)
                print(f"{role.name}: Assigned ALL {len(all_permissions)} permissions")
            else:
                # Assign specific permissions
                perm_names = role_permissions[role.name]
                assigned = 0
                for perm_name in perm_names:
                    perm = Permission.query.filter_by(name=perm_name).first()
                    if perm:
                        role.permissions.append(perm)
                        assigned += 1
                print(f"{role.name}: Assigned {assigned} permissions")
        
        db.session.commit()
    
    print("\n" + "=" * 70)
    print("Final Permission Counts:")
    print("=" * 70)
    for role in Role.query.all():
        print(f"{role.name}: {len(role.permissions)} permissions")
    
    print("\nOK Role permissions configured properly!")
    print("\nRole Hierarchy:")
    print("  Super Admin & Admin: Full access (43 permissions)")
    print("  Manager: Can create, edit, delete (30+ permissions)")
    print("  Viewer: Read-only access (20+ permissions)")
    print("  Lecturer: Limited access (8+ permissions)")

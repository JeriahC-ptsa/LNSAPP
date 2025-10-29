"""
Setup script to create default permissions and assign them to Admin role
Run this once to set up the permission system
"""
from app import app, db
from auth_models import Role, Permission

def setup_default_permissions():
    """Create default permissions for all pages and resources"""
    
    with app.app_context():
        # Define all page permissions
        page_permissions = [
            ('students_access', 'students', 'view', 'page_access', 'Access to students page'),
            ('modules_access', 'modules', 'view', 'page_access', 'Access to modules page'),
            ('reports_access', 'reports', 'view', 'page_access', 'Access to reports page'),
            ('schedule_access', 'schedule', 'view', 'page_access', 'Access to schedule page'),
            ('machines_access', 'machines', 'view', 'page_access', 'Access to machines page'),
            ('inventory_access', 'inventory', 'view', 'page_access', 'Access to inventory page'),
            ('lecturers_access', 'lecturers', 'view', 'page_access', 'Access to lecturers page'),
            ('admin_access', 'admin', 'view', 'page_access', 'Access to admin panel'),
            ('management_access', 'management', 'view', 'page_access', 'Access to management'),
            ('overheads_access', 'overheads', 'view', 'page_access', 'Access to overheads'),
            ('macroplan_access', 'macroplan', 'view', 'page_access', 'Access to macroplan'),
        ]
        
        # Define resource-action permissions
        resource_permissions = [
            ('students_create', 'students', 'create', 'function', 'Create new students'),
            ('students_edit', 'students', 'edit', 'function', 'Edit student information'),
            ('students_delete', 'students', 'delete', 'function', 'Delete students'),
            ('modules_create', 'modules', 'create', 'function', 'Create new modules'),
            ('modules_edit', 'modules', 'edit', 'function', 'Edit module information'),
            ('modules_delete', 'modules', 'delete', 'function', 'Delete modules'),
            ('modules_assign', 'modules', 'assign_modules', 'function', 'Assign modules to students'),
            ('reports_generate', 'reports', 'generate', 'function', 'Generate reports'),
            ('reports_export', 'reports', 'export', 'function', 'Export reports'),
        ]
        
        all_permissions = page_permissions + resource_permissions
        
        # Create permissions if they don't exist
        created_count = 0
        for perm_data in all_permissions:
            name, resource, action, perm_type, description = perm_data
            existing = Permission.query.filter_by(name=name).first()
            if not existing:
                perm = Permission(
                    name=name,
                    resource=resource,
                    action=action,
                    type=perm_type,
                    description=description
                )
                db.session.add(perm)
                created_count += 1
                print(f"Created permission: {name}")
        
        db.session.commit()
        print(f"\n✅ Created {created_count} new permissions")
        
        # Assign all permissions to Admin role
        admin_role = Role.query.filter_by(name='Admin').first()
        if admin_role:
            all_perms = Permission.query.all()
            admin_role.permissions = all_perms
            db.session.commit()
            print(f"✅ Assigned {len(all_perms)} permissions to Admin role")
        else:
            print("⚠️  Admin role not found. Please create it first.")
        
        # Create a Viewer role with limited permissions
        viewer_role = Role.query.filter_by(name='Viewer').first()
        if not viewer_role:
            viewer_role = Role(name='Viewer', description='View-only access')
            db.session.add(viewer_role)
        
        # Assign view-only permissions to Viewer role
        view_perms = Permission.query.filter(
            (Permission.action == 'view') | (Permission.type == 'page_access')
        ).all()
        viewer_role.permissions = view_perms
        db.session.commit()
        print(f"✅ Assigned {len(view_perms)} view permissions to Viewer role")
        
        print("\n🎉 Permission setup complete!")
        print("\nNext steps:")
        print("1. Assign roles to users in the admin panel")
        print("2. Create custom permissions as needed")
        print("3. Test access restrictions")

if __name__ == '__main__':
    setup_default_permissions()

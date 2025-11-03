# auth.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from auth_models import User, Role, Permission, DynamicField, DynamicFieldValue
from models import db
from functools import wraps
import json

auth_bp = Blueprint('auth', __name__)

def require_permission(permission_name):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.has_permission(permission_name):
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.active:
                flash('Your account has been deactivated. Please contact an administrator.', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=request.form.get('remember'))
            user.last_login = db.func.current_timestamp()
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/admin/users')
@require_permission('manage_users')
def manage_users():
    users = User.query.all()
    roles = Role.query.all()
    permissions = Permission.query.all()
    return render_template('admin/users.html', users=users, roles=roles, permissions=permissions)

@auth_bp.route('/admin/users/add', methods=['POST'])
@require_permission('manage_users')
def add_user():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    role_ids = request.form.getlist('roles')
    
    # Validate password confirmation
    if password != confirm_password:
        flash('Passwords do not match!', 'danger')
        return redirect(url_for('auth.manage_users'))
    
    # Validate password length
    if len(password) < 6:
        flash('Password must be at least 6 characters long.', 'danger')
        return redirect(url_for('auth.manage_users'))
    
    # Check if user exists
    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'danger')
        return redirect(url_for('auth.manage_users'))
    
    if User.query.filter_by(email=email).first():
        flash('Email already exists.', 'danger')
        return redirect(url_for('auth.manage_users'))
    
    # Create new user
    user = User(username=username, email=email)
    user.set_password(password)
    
    # Assign roles
    for role_id in role_ids:
        role = Role.query.get(role_id)
        if role:
            user.roles.append(role)
    
    db.session.add(user)
    db.session.commit()
    
    flash('User created successfully.', 'success')
    return redirect(url_for('auth.manage_users'))

@auth_bp.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@require_permission('manage_users')
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.active = not user.active
    db.session.commit()
    
    status = 'activated' if user.active else 'deactivated'
    flash(f'User {user.username} has been {status}.', 'success')
    return redirect(url_for('auth.manage_users'))

@auth_bp.route('/admin/users/<int:user_id>/update-roles', methods=['POST'])
@require_permission('manage_users')
def update_user_roles(user_id):
    user = User.query.get_or_404(user_id)
    role_ids = request.form.getlist('roles')
    
    # Clear existing roles
    user.roles.clear()
    
    # Add new roles
    for role_id in role_ids:
        role = Role.query.get(role_id)
        if role:
            user.roles.append(role)
    
    db.session.commit()
    flash(f'Roles updated for user {user.username}.', 'success')
    return redirect(url_for('auth.manage_users'))

@auth_bp.route('/admin/permissions')
@require_permission('manage_permissions')
def manage_permissions():
    permissions = Permission.query.all()
    # Define available pages in the system
    available_pages = [
        'index', 'machines_list', 'maintenance_dashboard', 'inventory_list',
        'overheads_dashboard', 'macroplan_page', 'modules_page', 'lecturers_page',
        'view_schedule', 'schedule_calendar', 'list_students', 'groups_list',
        'assign_inventory', 'reports'
    ]
    return render_template('admin/permissions.html', 
                         permissions=permissions, 
                         available_pages=available_pages)

@auth_bp.route('/admin/permissions/add', methods=['POST'])
@require_permission('manage_permissions')
def add_permission():
    name = request.form.get('name')
    perm_type = request.form.get('type')
    resource = request.form.get('resource')
    description = request.form.get('description')
    
    if Permission.query.filter_by(name=name).first():
        flash('Permission already exists.', 'danger')
        return redirect(url_for('auth.manage_permissions'))
    
    permission = Permission(
        name=name,
        type=perm_type,
        resource=resource,
        description=description
    )
    
    db.session.add(permission)
    db.session.commit()
    
    flash('Permission created successfully.', 'success')
    return redirect(url_for('auth.manage_permissions'))

# Dynamic fields management
@auth_bp.route('/admin/dynamic-fields')
@require_permission('manage_fields')
def manage_dynamic_fields():
    fields = DynamicField.query.all()
    models = ['Student', 'Lecturer', 'Machine', 'Module']  # Available models
    return render_template('admin/dynamic_fields.html', fields=fields, models=models)

@auth_bp.route('/admin/dynamic-fields/add', methods=['POST'])
@require_permission('manage_fields')
def add_dynamic_field():
    data = request.get_json()
    
    field = DynamicField(
        model_name=data['model_name'],
        field_name=data['field_name'],
        field_type=data['field_type'],
        field_options=json.dumps(data.get('field_options', [])),
        required=data.get('required', False)
    )
    
    db.session.add(field)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Field added successfully'})

@auth_bp.route('/admin/dynamic-fields/<int:field_id>/delete', methods=['DELETE'])
@require_permission('manage_fields')
def delete_dynamic_field(field_id):
    field = DynamicField.query.get_or_404(field_id)
    
    # Delete all values for this field
    DynamicFieldValue.query.filter_by(field_id=field_id).delete()
    
    db.session.delete(field)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Field deleted successfully'})

##############################################
# ROLE & PERMISSION MANAGEMENT
##############################################

@auth_bp.route('/admin/roles')
@login_required
def manage_roles():
    """Page to manage roles and permissions"""
    if not current_user.has_role('Admin') and not current_user.has_page_access('admin'):
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))
    
    roles = Role.query.all()
    all_permissions = Permission.query.order_by(Permission.type, Permission.name).all()
    
    return render_template('admin/manage_roles.html', 
                         roles=roles, 
                         all_permissions=all_permissions)

@auth_bp.route('/admin/role/create', methods=['POST'])
@login_required
def create_role():
    """Create a new role"""
    if not current_user.has_role('Admin'):
        flash('You do not have permission to create roles.', 'danger')
        return redirect(url_for('auth.manage_roles'))
    
    role_name = request.form.get('role_name')
    description = request.form.get('description')
    
    if not role_name:
        flash('Role name is required.', 'danger')
        return redirect(url_for('auth.manage_roles'))
    
    # Check if role already exists
    existing_role = Role.query.filter_by(name=role_name).first()
    if existing_role:
        flash(f'Role "{role_name}" already exists.', 'danger')
        return redirect(url_for('auth.manage_roles'))
    
    new_role = Role(name=role_name, description=description)
    db.session.add(new_role)
    db.session.commit()
    
    flash(f'Role "{role_name}" created successfully!', 'success')
    return redirect(url_for('auth.manage_roles'))

@auth_bp.route('/admin/role/update', methods=['POST'])
@login_required
def update_role():
    """Update an existing role"""
    if not current_user.has_role('Admin'):
        flash('You do not have permission to update roles.', 'danger')
        return redirect(url_for('auth.manage_roles'))
    
    role_id = request.form.get('role_id')
    role_name = request.form.get('role_name')
    description = request.form.get('description')
    
    role = Role.query.get_or_404(role_id)
    
    # Check if name is being changed to something that already exists
    if role_name != role.name:
        existing = Role.query.filter_by(name=role_name).first()
        if existing:
            flash(f'Role name "{role_name}" is already in use.', 'danger')
            return redirect(url_for('auth.manage_roles'))
    
    role.name = role_name
    role.description = description
    db.session.commit()
    
    flash(f'Role "{role_name}" updated successfully!', 'success')
    return redirect(url_for('auth.manage_roles'))

@auth_bp.route('/admin/role/<int:role_id>', methods=['DELETE'])
@login_required
def delete_role(role_id):
    """Delete a role"""
    if not current_user.has_role('Admin'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    role = Role.query.get_or_404(role_id)
    
    # Prevent deletion of Admin role
    if role.name == 'Admin':
        return jsonify({'success': False, 'message': 'Cannot delete Admin role'}), 400
    
    # Check if any users have this role
    if role.users:
        return jsonify({
            'success': False, 
            'message': f'Cannot delete role. {len(role.users)} user(s) are assigned to this role.'
        }), 400
    
    db.session.delete(role)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Role deleted successfully'})

@auth_bp.route('/admin/role/<int:role_id>/permissions', methods=['GET'])
@login_required
def get_role_permissions(role_id):
    """Get permissions for a specific role"""
    if not current_user.has_role('Admin') and not current_user.has_page_access('admin'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    role = Role.query.get_or_404(role_id)
    permission_ids = [p.id for p in role.permissions]
    
    return jsonify({
        'success': True,
        'role_id': role.id,
        'role_name': role.name,
        'permission_ids': permission_ids
    })

@auth_bp.route('/admin/role/<int:role_id>/permissions', methods=['POST'])
@login_required
def update_role_permissions(role_id):
    """Update permissions for a role"""
    if not current_user.has_role('Admin'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    role = Role.query.get_or_404(role_id)
    data = request.get_json()
    permission_ids = data.get('permission_ids', [])
    
    # Get permission objects
    permissions = Permission.query.filter(Permission.id.in_(permission_ids)).all()
    
    # Update role permissions
    role.permissions = permissions
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Permissions updated for role "{role.name}"',
        'permission_count': len(permissions)
    })

@auth_bp.route('/admin/permissions/create', methods=['POST'])
@login_required
def create_permission():
    """Create a new custom permission"""
    if not current_user.has_role('Admin'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    data = request.get_json()
    name = data.get('name')
    resource = data.get('resource')
    action = data.get('action')
    perm_type = data.get('type', 'function')
    description = data.get('description', '')
    
    if not name or not resource:
        return jsonify({'success': False, 'message': 'Name and resource are required'}), 400
    
    # Check if permission already exists
    existing = Permission.query.filter_by(name=name).first()
    if existing:
        return jsonify({'success': False, 'message': 'Permission already exists'}), 400
    
    new_permission = Permission(
        name=name,
        resource=resource,
        action=action,
        type=perm_type,
        description=description
    )
    db.session.add(new_permission)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Permission created successfully',
        'permission_id': new_permission.id
    })

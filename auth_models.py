# auth_models.py
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from models import db

# User-Role association table
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

# Role-Permission association table
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
)

# User-Site association table (for multi-site access)
user_sites = db.Table('user_sites',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('site_id', db.Integer, db.ForeignKey('sites.id'), primary_key=True),
    db.Column('is_manager', db.Boolean, default=False),  # Is this user a manager at this site?
    db.Column('assigned_date', db.DateTime, default=datetime.utcnow)
)

# User model
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    roles = db.relationship('Role', secondary=user_roles, backref='users')
    sites = db.relationship('Site', secondary=user_sites, backref='users')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission_name):
        for role in self.roles:
            for permission in role.permissions:
                if permission.name == permission_name:
                    return True
        return False
    
    def has_resource_permission(self, resource, action=None):
        """Check if user has permission for a specific resource and action"""
        for role in self.roles:
            for permission in role.permissions:
                if permission.resource == resource:
                    if action is None or permission.action == action or permission.action == '*':
                        return True
        return False
    
    def has_page_access(self, page_name):
        """Check if user can access a specific page"""
        return self.has_resource_permission(page_name, 'view') or self.has_permission(f'{page_name}_access')
    
    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)
    
    def get_accessible_pages(self):
        pages = set()
        for role in self.roles:
            for permission in role.permissions:
                if permission.type == 'page_access':
                    pages.add(permission.resource)
        return list(pages)
    
    def get_permissions_for_resource(self, resource):
        """Get all actions allowed for a specific resource"""
        actions = set()
        for role in self.roles:
            for permission in role.permissions:
                if permission.resource == resource and permission.action:
                    actions.add(permission.action)
        return list(actions)
    
    def has_site_access(self, site_id):
        """Check if user has access to a specific site"""
        return any(site.id == site_id for site in self.sites)
    
    def is_site_manager(self, site_id):
        """Check if user is a manager at a specific site"""
        # Query the user_sites table for this user-site combination
        from sqlalchemy import and_
        result = db.session.execute(
            user_sites.select().where(
                and_(
                    user_sites.c.user_id == self.id,
                    user_sites.c.site_id == site_id
                )
            )
        ).fetchone()
        return result and result.is_manager if result else False
    
    def get_accessible_sites(self):
        """Get list of sites user can access"""
        return self.sites
    
    def is_super_admin(self):
        """Check if user is super admin (has access to all sites)"""
        return self.has_role('Admin') or self.has_role('Super Admin') or self.has_role('System Administrator')

# Role model
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))
    
    # Relationships
    permissions = db.relationship('Permission', secondary=role_permissions, backref='roles')

# Permission model
class Permission(db.Model):
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    type = db.Column(db.String(50))  # 'page_access', 'function', 'action', 'read', 'write', 'delete'
    resource = db.Column(db.String(100))  # The page or resource name (e.g., 'students', 'modules')
    action = db.Column(db.String(100))  # Specific action (e.g., 'create', 'edit', 'delete', 'view', 'assign_modules')
    description = db.Column(db.String(255))

# Dynamic Field model for adding custom fields to models
class DynamicField(db.Model):
    __tablename__ = 'dynamic_fields'
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(50), nullable=False)  # e.g., 'Student'
    field_name = db.Column(db.String(50), nullable=False)
    field_type = db.Column(db.String(20), nullable=False)  # 'text', 'number', 'date', 'select'
    field_options = db.Column(db.Text)  # JSON string for select options
    required = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Dynamic Field Values for storing actual data
class DynamicFieldValue(db.Model):
    __tablename__ = 'dynamic_field_values'
    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey('dynamic_fields.id'))
    record_id = db.Column(db.Integer)  # ID of the record in the target model
    value = db.Column(db.Text)
    
    # Relationship
    field = db.relationship('DynamicField', backref='values')

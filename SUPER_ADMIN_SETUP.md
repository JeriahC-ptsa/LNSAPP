# Super Admin Account Setup

## Issue
Unable to log in with admin/admin123 because:
1. Auth tables (users, roles, permissions) didn't exist in the database
2. No super admin user was created

## Solution

### Created Auth Tables and Super Admin User

Ran `create_super_admin.py` which:

1. **Created all auth tables** in `database.db`:
   - `users` - User accounts
   - `roles` - User roles (Super Admin, Admin, etc.)
   - `permissions` - Granular permissions
   - `user_roles` - Many-to-many relationship
   - `role_permissions` - Many-to-many relationship
   - `user_sites` - User site access

2. **Created Super Admin role**:
   - Name: "Super Admin"
   - Description: "Full system access across all sites"

3. **Created admin user**:
   - Username: `admin`
   - Email: `admin@example.com`
   - Password: `admin123`
   - Active: Yes
   - Role: Super Admin

4. **Created default site**:
   - Name: "Main Campus"
   - Code: "MAIN"
   - Location: "Head Office"

## Login Credentials

```
Username: admin
Password: admin123
```

## What You Can Do Now

✅ **Log in to the application** at http://127.0.0.1:5000/auth/login

✅ **Full system access** - Super admin has access to:
- All sites
- All students, groups, modules, machines
- User management
- Site management
- Reports and analytics
- All CRUD operations

✅ **Create more users** - After logging in, you can create additional users with different roles

✅ **Create more sites** - Add additional sites/campuses as needed

## File Location

- **Script**: `create_super_admin.py`
- **Database**: `database.db`
- **Auth Models**: `auth_models.py`

## Next Steps

1. **Log in** with admin/admin123
2. **Change the password** (recommended for production)
3. **Create site-specific users** with limited access
4. **Configure permissions** for different user roles
5. **Add more sites** if managing multiple campuses

## Re-running the Script

If you run `create_super_admin.py` again:
- It won't duplicate the admin user
- It will **reset the password** to `admin123`
- Useful if you forget the password

## User Model Fields

The User model uses:
- `active` (Boolean field in database)
- `username` (unique)
- `email` (unique)
- `password_hash` (encrypted)
- `roles` (relationship to Role model)
- `sites` (relationship to Site model)

## Security Notes

🔒 **Change default password** - The default admin123 password should be changed in production

🔒 **Limit super admin accounts** - Create role-based users instead of giving everyone super admin

🔒 **Use strong passwords** - Passwords are hashed using Werkzeug security

---
**Setup Completed**: October 24, 2025  
**Status**: ✅ READY TO USE

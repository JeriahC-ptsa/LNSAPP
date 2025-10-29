# 🔐 Role & Permission Management Guide

## Overview
You now have a complete role and permission management system that allows you to:
- Create custom roles
- Assign specific permissions to each role
- Control what users can see and do based on their roles

---

## 📍 How to Access

1. **Navigate to Admin → Roles & Permissions** from the navbar
2. **You must be logged in as an Admin** to access this page

---

## ✨ Features

### 1. **Create New Roles**
- Click **"Add Role"** button in the Roles panel
- Enter role name (e.g., "Lab Assistant", "Student Advisor", "Lecturer")
- Add optional description
- Click **"Create Role"**

### 2. **Assign Permissions to Roles**
- Click on any role in the left panel
- Check/uncheck permissions you want to grant
- Permissions are organized into two categories:
  - **Page Access Permissions** - Control what pages users can view
  - **Function Permissions** - Control specific actions (create, edit, delete)
- Click **"Save Permissions"** to apply changes

### 3. **Edit Roles**
- Select a role from the list
- Click **"Edit Role"** button
- Modify name or description
- Click **"Update Role"**

### 4. **Delete Roles**
- Select a role from the list
- Click **"Delete Role"** button
- Confirm deletion
- **Note**: Cannot delete Admin role or roles with assigned users

### 5. **Quick Actions**
- **Select All** - Check all permission checkboxes
- **Deselect All** - Uncheck all permission checkboxes

---

## 🎯 Example Use Cases

### Example 1: Create "Lab Assistant" Role

**Permissions to Grant:**
- ✅ `inventory_access` - View inventory
- ✅ `machines_access` - View machines
- ✅ `schedule_access` - View schedule
- ✅ `students_access` - View students
- ❌ No create/edit/delete permissions

**What they can do:**
- View inventory, machines, schedules, and students
- Cannot modify anything

---

### Example 2: Create "Student Advisor" Role

**Permissions to Grant:**
- ✅ `students_access` - View students page
- ✅ `students_create` - Add new students
- ✅ `students_edit` - Edit student information
- ✅ `reports_access` - View reports
- ✅ `reports_generate` - Generate reports
- ❌ No delete permissions
- ❌ No module/inventory access

**What they can do:**
- Add and edit students
- Generate reports
- Cannot delete students or access other areas

---

### Example 3: Create "Lecturer" Role

**Permissions to Grant:**
- ✅ `students_access` - View students
- ✅ `modules_access` - View modules
- ✅ `modules_assign` - Assign modules to students
- ✅ `reports_access` - View reports
- ✅ `reports_generate` - Generate reports
- ✅ `schedule_access` - View schedule

**What they can do:**
- View students and modules
- Assign modules to students
- View schedules and generate reports
- Cannot delete or modify core data

---

## 🔄 How Permissions Work

### Page Access Flow:
1. User logs in
2. System checks user's roles
3. For each role, system gets assigned permissions
4. Navbar hides menu items user doesn't have access to
5. If user tries to access restricted page, they're redirected

### Function Permission Flow:
1. User tries to perform action (e.g., delete student)
2. System checks if any of user's roles have required permission
3. If yes: Action proceeds
4. If no: Error message shown

---

## 📊 Available Permissions

### Page Access (View-Only):
| Permission | Controls |
|-----------|----------|
| `students_access` | Students page visibility |
| `modules_access` | Modules page visibility |
| `reports_access` | Reports page visibility |
| `schedule_access` | Schedule pages visibility |
| `machines_access` | Machines page visibility |
| `inventory_access` | Inventory page visibility |
| `lecturers_access` | Lecturers page visibility |
| `admin_access` | Admin panel visibility |
| `management_access` | Management dropdown visibility |
| `overheads_access` | Overheads page visibility |
| `macroplan_access` | MacroPlan page visibility |

### Function Permissions (Actions):
| Permission | Controls |
|-----------|----------|
| `students_create` | Adding new students |
| `students_edit` | Editing student info |
| `students_delete` | Deleting students |
| `modules_create` | Creating modules |
| `modules_edit` | Editing modules |
| `modules_delete` | Deleting modules |
| `modules_assign` | Assigning modules to students |
| `reports_generate` | Generating reports |
| `reports_export` | Exporting reports |

---

## 🛡️ Security Features

1. **Admin Protection**: Cannot delete Admin role
2. **User Safety**: Cannot delete roles with assigned users
3. **Permission Check**: All sensitive actions require authentication
4. **Automatic Enforcement**: Permissions automatically hide UI elements
5. **Backend Validation**: Routes verify permissions before executing

---

## 🚀 How to Use with Users

### Step 1: Create Roles
1. Go to Admin → Roles & Permissions
2. Create roles with appropriate names
3. Assign permissions to each role

### Step 2: Assign Roles to Users
1. Go to Admin → Manage Users
2. Edit a user
3. Select the appropriate role(s)
4. Save changes

### Step 3: Test
1. Log out
2. Log in as a user with the new role
3. Verify they only see permitted pages
4. Verify they can only perform permitted actions

---

## 💡 Best Practices

1. **Start with Viewer Role**
   - Give new users Viewer role first
   - Gradually increase permissions as needed

2. **Create Specific Roles**
   - Don't grant more permissions than necessary
   - Create role-specific access (Lab Assistant, Lecturer, etc.)

3. **Regular Review**
   - Periodically review role permissions
   - Remove unnecessary permissions

4. **Document Custom Roles**
   - Keep notes on why each role has specific permissions
   - Document intended use case for each role

5. **Test Before Deploying**
   - Create test users with new roles
   - Verify permissions work as expected

---

## 🔧 Advanced: Creating Custom Permissions

You can create custom permissions via the API:

```python
# Example: Create permission to approve timesheets
POST /admin/permissions/create
{
  "name": "timesheets_approve",
  "resource": "timesheets",
  "action": "approve",
  "type": "function",
  "description": "Can approve student timesheets"
}
```

Then use it in code:
```python
@require_resource_permission('timesheets', 'approve')
def approve_timesheet():
    # Only users with timesheets_approve permission can access
    ...
```

---

## ✅ Quick Checklist

- [ ] Restart server after setup
- [ ] Create at least 2-3 custom roles
- [ ] Assign permissions to each role
- [ ] Create test users with different roles
- [ ] Verify navbar changes based on role
- [ ] Test that restricted actions are blocked
- [ ] Document your custom roles

---

## 🆘 Troubleshooting

**Problem**: Role management page not showing
- **Solution**: Ensure you're logged in as Admin

**Problem**: Permissions not taking effect
- **Solution**: Log out and log back in

**Problem**: Cannot delete role
- **Solution**: Remove all users from that role first

**Problem**: User sees pages they shouldn't
- **Solution**: Verify correct permissions are unchecked for their role

---

## 🎉 You're Ready!

You now have complete control over:
- ✅ Who can access what pages
- ✅ Who can perform which actions
- ✅ Custom roles for your organization
- ✅ Granular permission management

Navigate to **Admin → Roles & Permissions** to get started!

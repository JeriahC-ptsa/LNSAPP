# 🏢 Multi-Site/Facility Implementation Guide

## 📋 Overview

Your system now supports **multiple sites/facilities** with complete data isolation and multi-tenancy. Each site has its own:

- ✅ Students
- ✅ Groups
- ✅ Lecturers/Staff
- ✅ Machines
- ✅ Modules
- ✅ Inventory
- ✅ Schedules
- ✅ Managers

Users can be assigned to multiple sites, and all data is filtered based on the currently active site.

---

## 🗂️ Database Changes

### **New Model: Site**

```python
class Site(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    code = db.Column(db.String(50), unique=True)  # e.g., "JHB", "CPT"
    location = db.Column(db.String(255))
    address = db.Column(db.Text)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime)
```

### **Modified Models (site_id added)**

All the following models now have `site_id` foreign key:

| Model | Description |
|-------|-------------|
| `Group` | Each group belongs to a site |
| `Student` | Each student belongs to a site |
| `Lecturer` | Each lecturer belongs to a site |
| `Machine` | Each machine belongs to a site |
| `Module` | Each module belongs to a site |
| `Inventory` | Each inventory item belongs to a site |
| `InventoryUsage` | Each usage record belongs to a site |
| `Schedule` | Each schedule belongs to a site |
| `OverheadCost` | Each cost record belongs to a site |
| `MachineMaintenance` | Each maintenance record belongs to a site |
| `MacroPlan` | Each plan belongs to a site |

### **User-Site Association**

New table `user_sites` allows users to access multiple sites:

```python
user_sites = db.Table('user_sites',
    db.Column('user_id', db.Integer, ForeignKey('users.id')),
    db.Column('site_id', db.Integer, ForeignKey('sites.id')),
    db.Column('is_manager', db.Boolean, default=False),
    db.Column('assigned_date', db.DateTime)
)
```

---

## 🚀 Implementation Status

### ✅ **COMPLETED:**

1. **Database Schema**
   - Created `Site` model
   - Added `site_id` to all relevant models
   - Created `user_sites` association table
   - Added relationships and foreign keys

2. **User Model Enhancements**
   - Added `sites` relationship
   - Added `has_site_access(site_id)` method
   - Added `is_site_manager(site_id)` method
   - Added `get_accessible_sites()` method
   - Added `is_super_admin()` method

### ⏳ **PENDING (Requires Implementation):**

The following components need to be updated to support multi-site functionality:

1. **Site Selector in Navigation**
   - Add site dropdown in header
   - Store active site in session
   - Switch between sites dynamically

2. **All Database Queries**
   - Filter by `site_id = session['active_site']`
   - Update ALL `.query.all()` calls
   - Update ALL `.query.filter()` calls
   - Add site_id when creating new records

3. **Schedule Generation**
   - Filter students by site
   - Filter groups by site
   - Filter machines by site
   - Filter modules by site
   - Add site_id to generated schedules

4. **Reports**
   - Add site filter to all reports
   - Show only data from active site
   - Option to compare across sites (for admins)

5. **User Management**
   - Assign users to sites
   - Set site managers
   - UI for managing user-site access

6. **Site Management Interface**
   - Create/Edit/Delete sites
   - View site details
   - Activate/Deactivate sites

---

## 📝 Migration Steps

### **Step 1: Run Database Migration**

```bash
flask db migrate -m "Add multi-site support"
flask db upgrade
```

### **Step 2: Create Initial Site**

After migration, you MUST create at least one site before the system works:

```python
# Run this in Flask shell or create a migration script
from models import db, Site
from datetime import datetime

# Create default site
default_site = Site(
    name="Main Campus",
    code="MAIN",
    location="Johannesburg",
    address="123 Main Street",
    phone="+27 11 123 4567",
    email="main@example.com",
    is_active=True,
    created_date=datetime.utcnow()
)
db.session.add(default_site)
db.session.commit()
```

### **Step 3: Assign Existing Data to Default Site**

All existing records need to be assigned to the default site:

```python
# Update all existing records (run once after creating default site)
from models import *

default_site_id = 1  # ID of the site you just created

# Update Groups
Group.query.update({Group.site_id: default_site_id})

# Update Students
Student.query.update({Student.site_id: default_site_id})

# Update Lecturers
Lecturer.query.update({Lecturer.site_id: default_site_id})

# Update Machines
Machine.query.update({Machine.site_id: default_site_id})

# Update Modules
Module.query.update({Module.site_id: default_site_id})

# Update Inventory
Inventory.query.update({Inventory.site_id: default_site_id})

# Update InventoryUsage
InventoryUsage.query.update({InventoryUsage.site_id: default_site_id})

# Update Schedules
Schedule.query.update({Schedule.site_id: default_site_id})

# Update OverheadCost
OverheadCost.query.update({OverheadCost.site_id: default_site_id})

# Update MachineMaintenance
MachineMaintenance.query.update({MachineMaintenance.site_id: default_site_id})

# Update MacroPlan
MacroPlan.query.update({MacroPlan.site_id: default_site_id})

db.session.commit()
```

### **Step 4: Assign Users to Sites**

```python
# Assign all existing users to default site
from auth_models import User
from models import Site

default_site = Site.query.first()
users = User.query.all()

for user in users:
    if default_site not in user.sites:
        user.sites.append(default_site)

db.session.commit()
```

---

## 🔧 Code Updates Required

### **1. Add Site Context Filter**

Create a helper function to get active site:

```python
from flask import session

def get_active_site_id():
    """Get the currently active site ID from session"""
    return session.get('active_site_id')

def set_active_site(site_id):
    """Set the active site in session"""
    session['active_site_id'] = site_id

def require_site_access(f):
    """Decorator to ensure user has access to active site"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        site_id = get_active_site_id()
        if not site_id:
            flash('Please select a site first.', 'warning')
            return redirect(url_for('select_site'))
        
        if not current_user.is_super_admin() and not current_user.has_site_access(site_id):
            flash('You do not have access to this site.', 'danger')
            return redirect(url_for('select_site'))
        
        return f(*args, **kwargs)
    return decorated_function
```

### **2. Update All Queries**

**Before:**
```python
students = Student.query.all()
```

**After:**
```python
site_id = get_active_site_id()
students = Student.query.filter_by(site_id=site_id).all()
```

### **3. Update Create Operations**

**Before:**
```python
student = Student(
    student_name=name,
    student_number=number
)
```

**After:**
```python
student = Student(
    student_name=name,
    student_number=number,
    site_id=get_active_site_id()
)
```

### **4. Add Site Selector to Navigation**

Add to `base.html`:

```html
{% if current_user.is_authenticated %}
<li class="nav-item dropdown">
  <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
    <i class="bi bi-building"></i>
    {{ session.get('active_site_name', 'Select Site') }}
  </a>
  <ul class="dropdown-menu">
    {% for site in current_user.get_accessible_sites() %}
    <li>
      <a class="dropdown-item" href="{{ url_for('switch_site', site_id=site.id) }}">
        <i class="bi bi-building-check"></i> {{ site.name }}
        {% if site.id == session.get('active_site_id') %}
        <i class="bi bi-check-circle-fill text-success"></i>
        {% endif %}
      </a>
    </li>
    {% endfor %}
    
    {% if current_user.is_super_admin() %}
    <li><hr class="dropdown-divider"></li>
    <li><a class="dropdown-item" href="{{ url_for('manage_sites') }}">
      <i class="bi bi-gear-fill"></i> Manage Sites
    </a></li>
    {% endif %}
  </ul>
</li>
{% endif %}
```

### **5. Create Site Switching Route**

```python
@app.route('/switch_site/<int:site_id>')
@login_required
def switch_site(site_id):
    # Check access
    if not current_user.is_super_admin() and not current_user.has_site_access(site_id):
        flash('You do not have access to this site.', 'danger')
        return redirect(url_for('index'))
    
    # Get site
    site = Site.query.get_or_404(site_id)
    
    if not site.is_active:
        flash('This site is currently inactive.', 'warning')
        return redirect(url_for('index'))
    
    # Switch site
    session['active_site_id'] = site.id
    session['active_site_name'] = site.name
    session['active_site_code'] = site.code
    
    flash(f'Switched to {site.name}', 'success')
    return redirect(url_for('index'))
```

---

## 📊 Example: Updating a Route

### **Before (No Multi-Site):**

```python
@app.route('/students')
@login_required
def list_students():
    students = Student.query.all()
    groups = Group.query.all()
    return render_template('students/list.html', 
                         students=students,
                         groups=groups)
```

### **After (With Multi-Site):**

```python
@app.route('/students')
@login_required
@require_site_access
def list_students():
    site_id = get_active_site_id()
    students = Student.query.filter_by(site_id=site_id).all()
    groups = Group.query.filter_by(site_id=site_id).all()
    
    return render_template('students/list.html', 
                         students=students,
                         groups=groups,
                         active_site=Site.query.get(site_id))
```

---

## 🎯 Implementation Checklist

### **Phase 1: Critical (Must Do First)**
- [ ] Run database migration
- [ ] Create default site
- [ ] Assign existing data to default site
- [ ] Assign users to default site
- [ ] Test that system still works

### **Phase 2: Site Selector**
- [ ] Add site dropdown to navigation
- [ ] Create `switch_site` route
- [ ] Add `get_active_site_id()` helper
- [ ] Add `require_site_access` decorator
- [ ] Set default site on login

### **Phase 3: Update All Routes**
- [ ] Update all `Student` queries
- [ ] Update all `Group` queries
- [ ] Update all `Lecturer` queries
- [ ] Update all `Machine` queries
- [ ] Update all `Module` queries
- [ ] Update all `Inventory` queries
- [ ] Update all `Schedule` queries
- [ ] Update all create/update operations

### **Phase 4: Site Management**
- [ ] Create site management page
- [ ] Add/Edit/Delete sites
- [ ] Assign users to sites
- [ ] Set site managers
- [ ] View site statistics

### **Phase 5: Reports**
- [ ] Update all reports to filter by site
- [ ] Add cross-site comparison (admin only)
- [ ] Update dashboard for multi-site

### **Phase 6: Schedule Generation**
- [ ] Update basic schedule generator
- [ ] Update advanced schedule generator
- [ ] Filter all dropdowns by site
- [ ] Add site_id to generated schedules

---

## ⚠️ Important Warnings

### **1. Data Isolation**
- Each site's data is completely isolated
- Users can only see data from sites they have access to
- Super admins can access all sites

### **2. Breaking Changes**
- ALL queries must be updated to filter by site
- Missing site_id will cause errors
- Existing code will break until updated

### **3. Migration Requirements**
- Backup database before migration
- Create default site immediately after migration
- Assign all existing data to default site
- Test thoroughly before going live

### **4. Performance Considerations**
- Add index on site_id columns for better performance
- Consider caching site data
- Optimize queries with proper joins

---

## 🔐 Security Considerations

### **User Access Control:**
- Users can only access assigned sites
- Site managers have elevated privileges
- Super admins bypass site restrictions
- Session stores active site

### **Data Protection:**
- Site_id is required on all records
- Queries automatically filter by site
- No cross-site data leakage
- Audit trails include site information

---

## 📈 Future Enhancements

1. **Site Dashboard**
   - Per-site statistics
   - Site performance metrics
   - Cross-site comparisons

2. **Site Settings**
   - Per-site configurations
   - Custom branding per site
   - Site-specific workflows

3. **Data Sharing**
   - Share resources between sites
   - Transfer students between sites
   - Cross-site reporting

4. **Bulk Operations**
   - Apply changes to multiple sites
   - Clone site configurations
   - Batch user assignments

---

## 🆘 Troubleshooting

### **Error: "site_id cannot be null"**
**Solution**: Ensure `get_active_site_id()` returns a valid site ID and add it to all create operations.

### **Error: "User has no accessible sites"**
**Solution**: Assign the user to at least one site via the `user_sites` table.

### **No data showing after update**
**Solution**: Check that active_site_id is set in session and that data has been assigned to sites.

### **Can't switch sites**
**Solution**: Verify user has been assigned to multiple sites and that they are active.

---

## 📞 Support

For issues or questions about multi-site implementation:
1. Check this documentation
2. Review the migration checklist
3. Test with default site first
4. Verify user-site assignments

---

**This is a major architectural change. Take time to implement carefully and test thoroughly!**

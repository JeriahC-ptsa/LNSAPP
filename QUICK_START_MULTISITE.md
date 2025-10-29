# 🚀 Multi-Site Quick Start Guide

## ✅ **What's Already Done**

1. ✅ **Database** - All tables have site_id
2. ✅ **Migration** - 1,027 records assigned to Gauteng site
3. ✅ **Site Management** - Full CRUD interface at `/sites`
4. ✅ **Site Selector** - Dropdown in navigation bar
5. ✅ **Students Routes** - Fully updated and working

---

## 🎯 **Test It Now**

### **1. Restart Your App**
```powershell
python app.py
```

### **2. Log In**
- You should see "Gauteng" badge in the navbar

### **3. Test Site Management**
1. Click the "Gauteng" dropdown
2. Click "Manage Sites"
3. Click "Add New Site"
4. Create a test site:
   - Name: "Cape Town Campus"
   - Code: "CPT"
   - Location: "Cape Town"
   - Check "Active"
5. Click "Create Site"

### **4. Assign Yourself to New Site**
1. On the sites list, click the "👥" (people) icon for Cape Town
2. Find your username
3. Click "Grant Access"
4. You now have access to both sites!

### **5. Test Site Switching**
1. Click "Gauteng" dropdown in navbar
2. Click "Cape Town Campus (CPT)"
3. Notice the badge changes to "Cape Town Campus"
4. Go to Students page
5. You should see NO students (Cape Town is empty)
6. Switch back to Gauteng
7. You should see all 200 students again

### **6. Test Data Isolation**
1. Switch to Cape Town site
2. Add a test student
3. Switch to Gauteng
4. Verify the Cape Town student is NOT visible
5. ✅ **Data isolation works!**

---

## 📝 **Update Remaining Routes**

### **Copy-Paste Pattern for Each Route:**

#### **List Route:**
```python
@app.route("/resource")
@require_site_access  # ← ADD
def list_resource():
    site_id = get_active_site_id()  # ← ADD
    items = Resource.query.filter_by(site_id=site_id).all()  # ← MODIFY
    return render_template("resource/list.html", items=items)
```

#### **Create Route:**
```python
@app.route("/resource/add", methods=["GET", "POST"])
@require_site_access  # ← ADD
def add_resource():
    site_id = get_active_site_id()  # ← ADD
    
    if request.method == "POST":
        new_item = Resource(
            name=request.form["name"],
            site_id=site_id  # ← ADD THIS LINE
        )
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for("list_resource"))
    
    return render_template("resource/add.html")
```

#### **Edit/Delete Route:**
```python
@app.route("/resource/edit/<int:id>")
@require_site_access  # ← ADD
def edit_resource(id):
    site_id = get_active_site_id()  # ← ADD
    item = Resource.query.filter_by(id=id, site_id=site_id).first_or_404()  # ← MODIFY
    # ... rest of code
```

---

## 📋 **Routes to Update (In Order)**

### **Do These Next:**
1. **Groups** (4 routes) - Similar to Students
2. **Machines** (8 routes) - Similar to Students
3. **Modules** (5 routes) - Similar to Students
4. **Lecturers** (4 routes) - Similar to Students

### **Then These:**
5. **Schedule** (7 routes) - More complex, do last
6. **Inventory** (5 routes)
7. **Overheads** (4 routes)
8. **MacroPlan** (4 routes)

### **Finally:**
9. **Dashboard** (1 route) - Update statistics
10. **Reports** (multiple routes) - Add site filtering

---

## 🔍 **Find Routes to Update**

Search in `app.py` for:
- `@app.route("/groups")`
- `@app.route("/machines")`
- `@app.route("/modules")`
- `@app.route("/lecturers")`
- etc.

Apply the pattern to each one.

---

## ✅ **Checklist**

After updating each section:
- [ ] Add `@require_site_access` decorator
- [ ] Add `site_id = get_active_site_id()`
- [ ] Filter queries with `.filter_by(site_id=site_id)`
- [ ] Add `site_id=site_id` to create operations
- [ ] Test the routes
- [ ] Verify data isolation

---

## 🎉 **You're Ready!**

**What Works Now:**
- ✅ Site management (create, edit, delete sites)
- ✅ User-site assignment
- ✅ Site switching
- ✅ Students (fully multi-site enabled)
- ✅ Data isolation

**What Needs Work:**
- ⏳ Other routes (use the pattern above)

**Estimated Time:**
- Groups: 30 minutes
- Machines: 1 hour
- Modules: 45 minutes
- Lecturers: 30 minutes
- Schedule: 2 hours
- Everything else: 3-4 hours
- **Total: ~8-10 hours of work**

---

## 📞 **Need Help?**

Check these files:
- `IMPLEMENTATION_COMPLETE_SUMMARY.md` - Full status
- `MULTI_SITE_IMPLEMENTATION.md` - Technical details
- `update_routes_for_multisite.py` - Code examples

---

**Start testing now, then update routes one section at a time!** 🚀

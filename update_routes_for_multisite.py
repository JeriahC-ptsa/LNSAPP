"""
Multi-Site Route Update Helper
===============================
This script provides the code snippets you need to update each route for multi-site support.

Usage:
    python update_routes_for_multisite.py

This will print out all the updates you need to make.
"""

print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    MULTI-SITE ROUTE UPDATE GUIDE                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

✅ STUDENTS ROUTES - ALREADY COMPLETED

The following routes have been updated:
- /students
- /students/export
- /students/add
- /students/edit
- /students/delete

═══════════════════════════════════════════════════════════════════════════════

📋 REMAINING ROUTES TO UPDATE

I'll provide you with the exact code changes needed for each section.
You can copy-paste these updates into app.py

═══════════════════════════════════════════════════════════════════════════════
""")

print("""
🔹 GROUPS ROUTES
════════════════════════════════════════════════════════════════════════════════

Find the groups routes in app.py and update them as follows:

1. LIST GROUPS (/groups):
   - Add @require_site_access decorator
   - Filter by site_id

2. ADD GROUP (/groups/add):
   - Add @require_site_access decorator
   - Add site_id to new Group()

3. EDIT GROUP (/groups/edit/<id>):
   - Add @require_site_access decorator
   - Filter query by site_id

4. DELETE GROUP (/groups/delete/<id>):
   - Add @require_site_access decorator
   - Filter query by site_id

════════════════════════════════════════════════════════════════════════════════
""")

print("""
🔹 MACHINES ROUTES
════════════════════════════════════════════════════════════════════════════════

Update all machine-related routes:

1. LIST MACHINES (/machines):
   Machine.query.filter_by(site_id=site_id).all()

2. ADD MACHINE (/machines/add):
   Machine(..., site_id=get_active_site_id())

3. EDIT MACHINE (/machines/edit/<id>):
   Machine.query.filter_by(id=id, site_id=site_id).first_or_404()

4. DELETE MACHINE (/machines/delete/<id>):
   Machine.query.filter_by(id=id, site_id=site_id).first_or_404()

5. MAINTENANCE DASHBOARD (/maintenance_dashboard):
   MachineMaintenance.query.filter_by(site_id=site_id).all()

6. ADD MAINTENANCE (/maintenance/add):
   MachineMaintenance(..., site_id=get_active_site_id())

════════════════════════════════════════════════════════════════════════════════
""")

print("""
🔹 QUICK REFERENCE: Common Patterns
════════════════════════════════════════════════════════════════════════════════

PATTERN 1: List Route
---------------------
@app.route("/resource")
@require_site_access
def list_resource():
    site_id = get_active_site_id()
    items = Resource.query.filter_by(site_id=site_id).all()
    return render_template("resource/list.html", items=items)


PATTERN 2: Create Route
------------------------
@app.route("/resource/add", methods=["GET", "POST"])
@require_site_access
def add_resource():
    site_id = get_active_site_id()
    
    if request.method == "POST":
        new_item = Resource(
            name=request.form["name"],
            site_id=site_id  # ← ADD THIS LINE
        )
        db.session.add(new_item)
        db.session.commit()
        flash("Added successfully!", "success")
        return redirect(url_for("list_resource"))
    
    return render_template("resource/add.html")


PATTERN 3: Edit Route
----------------------
@app.route("/resource/edit/<int:id>", methods=["GET", "POST"])
@require_site_access
def edit_resource(id):
    site_id = get_active_site_id()
    item = Resource.query.filter_by(id=id, site_id=site_id).first_or_404()
    
    if request.method == "POST":
        item.name = request.form["name"]
        db.session.commit()
        flash("Updated successfully!", "success")
        return redirect(url_for("list_resource"))
    
    return render_template("resource/edit.html", item=item)


PATTERN 4: Delete Route
------------------------
@app.route("/resource/delete/<int:id>", methods=["POST"])
@require_site_access
def delete_resource(id):
    site_id = get_active_site_id()
    item = Resource.query.filter_by(id=id, site_id=site_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Deleted successfully!", "success")
    return redirect(url_for("list_resource"))

════════════════════════════════════════════════════════════════════════════════
""")

print("""
📊 PROGRESS CHECKLIST
════════════════════════════════════════════════════════════════════════════════

Mark off each section as you complete it:

HIGH PRIORITY:
[ ] Groups (4 routes)
[ ] Machines (8 routes)
[ ] Modules (5 routes)
[ ] Lecturers (4 routes)
[ ] Schedule (7 routes)

MEDIUM PRIORITY:
[ ] Inventory (5 routes)
[ ] Overheads (4 routes)
[ ] MacroPlan (4 routes)

LOW PRIORITY:
[ ] Dashboard (1 route)
[ ] Reports (multiple routes)

NEW FEATURES:
[ ] Site Management CRUD (6 routes)

════════════════════════════════════════════════════════════════════════════════

💡 TIP: Update one section at a time, then test before moving to the next!

════════════════════════════════════════════════════════════════════════════════
""")

print("\n✅ Students routes are already complete!")
print("📝 Use the patterns above to update the remaining routes.")
print("\n🚀 Start with Groups, then Machines, then continue down the list.\n")

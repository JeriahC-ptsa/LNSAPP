# app.py
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, session
)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_required, current_user
from flask import send_file
from io import BytesIO
import pandas as pd
from datetime import datetime, timedelta
import os
import random
from sqlalchemy.orm import joinedload
from flask import render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps

from config import Config
from models import db
from models import (
    Site, Group, Lecturer, Student, Machine, Module, MiniTask,
    StudentMiniTaskProgress, Attempt, StudentModuleProgress, ErrorLog, Inventory, InventoryUsage,
    OverheadCost, MachineMaintenance, MacroPlan, Schedule
)
from auth_models import User, Role, Permission, DynamicField, DynamicFieldValue
from auth import auth_bp
from reports import reports_bp
import json

app = Flask(__name__)
app.config.from_object(Config)

# Force template reload in development
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

db.init_app(app)
migrate = Migrate(app, db)

# Bootstrap: Ensure database tables and super admin exist on startup
from bootstrap import ensure_super_admin
ensure_super_admin()

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Site Management Helpers
def get_active_site_id():
    """Get the currently active site ID from session"""
    return session.get('active_site_id')

def set_active_site(site_id):
    """Set the active site in session"""
    site = Site.query.get(site_id)
    if site:
        session['active_site_id'] = site.id
        session['active_site_name'] = site.name
        session['active_site_code'] = site.code
        return True
    return False

def should_filter_by_site():
    """Check if we should filter by site or show all data (for admins)"""
    # Admins can see all data across all sites
    if current_user.is_authenticated and current_user.is_super_admin():
        return False
    return True

def get_query_site_filter():
    """Get site_id for filtering queries. Returns None if admin (show all sites)"""
    if not should_filter_by_site():
        return None  # Admin sees all sites
    return get_active_site_id()

def apply_site_filter(query, model):
    """Apply site filter to query. Admins see all sites, regular users see only their site."""
    site_id = get_query_site_filter()
    if site_id is not None:
        return query.filter_by(site_id=site_id)
    return query  # Admin - no filter, show all sites

def require_site_access(f):
    """Decorator to ensure user has access to active site"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        site_id = get_active_site_id()
        if not site_id:
            # If no site selected, set the first available site
            if current_user.sites:
                set_active_site(current_user.sites[0].id)
                site_id = current_user.sites[0].id
            elif current_user.is_super_admin():
                # Super admin gets first site
                first_site = Site.query.first()
                if first_site:
                    set_active_site(first_site.id)
                    site_id = first_site.id
            
            if not site_id:
                flash('Please select a site first.', 'warning')
                return redirect(url_for('select_site'))
        
        # Verify user has access (only check if authenticated, which is guaranteed by @login_required)
        if not current_user.is_super_admin() and not current_user.has_site_access(site_id):
            flash('You do not have access to this site.', 'danger')
            return redirect(url_for('select_site'))
        
        return f(*args, **kwargs)
    return decorated_function

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(reports_bp)

# Permission decorators
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

def require_resource_permission(resource, action):
    """Decorator for checking granular resource-level permissions"""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.has_resource_permission(resource, action):
                flash(f'You do not have permission to {action} {resource}.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_page_access(page_name):
    """Decorator for checking page-level access"""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.has_page_access(page_name):
                flash(f'You do not have permission to access the {page_name} page.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

##############################################
# HOME / DASHBOARD
##############################################
@app.route("/")
@require_site_access
def index():
    from collections import defaultdict

    site_id = get_active_site_id()

    # Admins see all sites, regular users see only their site
    total_machines = apply_site_filter(Machine.query, Machine).count()
    machines_in_use = apply_site_filter(Schedule.query, Schedule).with_entities(Schedule.machine_name).distinct().count()
    active_modules = apply_site_filter(Module.query, Module).count()
    
    # For pending tasks, need to join with Student
    if should_filter_by_site():
        pending_tasks = StudentMiniTaskProgress.query.join(Student).filter(Student.site_id == site_id).count()
    else:
        pending_tasks = StudentMiniTaskProgress.query.count()
    
    total_students = apply_site_filter(Student.query, Student).count()

    # 1. Total machine usage (in hours) - admins see all sites
    usage_query = db.session.query(
        Schedule.machine_name,
        db.func.sum(
            db.func.strftime('%s', Schedule.end_time) - db.func.strftime('%s', Schedule.start_time)
        ).label("total_seconds")
    )
    if should_filter_by_site():
        usage_query = usage_query.filter(Schedule.site_id == site_id)
    usage_summary = usage_query.group_by(Schedule.machine_name).all()

    usage_data = {
        "labels": [row.machine_name for row in usage_summary],
        "hours": [round(row.total_seconds / 3600, 2) for row in usage_summary]
    }

    # 📦 2. Inventory totals
    inv_summary = db.session.query(
        InventoryUsage.consumable,
        db.func.sum(InventoryUsage.quantity)
    ).group_by(InventoryUsage.consumable).all()

    inv_data = {
        "labels": [row[0] for row in inv_summary],
        "values": [row[1] for row in inv_summary]
    }

    # 💰 3. Cost Analytics
    # Total spent on inventory
    total_spent = db.session.query(
        db.func.sum(InventoryUsage.quantity * InventoryUsage.unit_cost)
    ).scalar() or 0

    # Average spend per student
    avg_spend_per_student = total_spent / total_students if total_students > 0 else 0

    # Total inventory used (quantity)
    total_inventory_used = db.session.query(
        db.func.sum(InventoryUsage.quantity)
    ).scalar() or 0

    # Spending breakdown by student
    spending_by_student = db.session.query(
        InventoryUsage.student_name,
        db.func.sum(InventoryUsage.quantity * InventoryUsage.unit_cost).label("total_cost")
    ).group_by(InventoryUsage.student_name).order_by(db.text("total_cost DESC")).all()

    # Spending breakdown by item
    spending_by_item = db.session.query(
        InventoryUsage.consumable,
        db.func.sum(InventoryUsage.quantity).label("qty"),
        db.func.sum(InventoryUsage.quantity * InventoryUsage.unit_cost).label("cost")
    ).group_by(InventoryUsage.consumable).order_by(db.text("cost DESC")).all()

    # 📈 4. Last 7 days – machine usage trends
    today = datetime.utcnow().date()
    last_7_days = today - timedelta(days=6)

    trend_raw = db.session.query(
        db.func.date(Schedule.start_time).label("day"),
        Schedule.machine_name,
        db.func.sum(
            db.func.strftime('%s', Schedule.end_time) - db.func.strftime('%s', Schedule.start_time)
        ).label("total_seconds")
    ).filter(Schedule.start_time >= last_7_days).group_by("day", Schedule.machine_name).all()

    machine_trend_data = defaultdict(lambda: defaultdict(float))
    for day, machine, seconds in trend_raw:
        machine_trend_data[str(day)][machine] += round(seconds / 3600, 2)

    # 📉 5. Last 7 days – inventory usage trends
    inv_trend = db.session.query(
        db.func.date(InventoryUsage.date_issued).label("day"),
        InventoryUsage.consumable,
        db.func.sum(InventoryUsage.quantity)
    ).filter(InventoryUsage.date_issued >= last_7_days).group_by("day", InventoryUsage.consumable).all()

    inventory_trend_data = defaultdict(lambda: defaultdict(int))
    for day, item, qty in inv_trend:
        inventory_trend_data[str(day)][item] += qty

    # Machine usage breakdown
    machine_usage_breakdown = []
    for row in usage_summary:
        hours = round(row.total_seconds / 3600, 2)
        machine_usage_breakdown.append({
            "machine": row.machine_name,
            "hours": hours
        })

    # ✅ NEW: Group-based analytics (admins see all sites)
    # Spending by group - Fixed to handle student name mismatches (InventoryUsage has student number prefix)
    spending_query = db.session.query(
        Group.name,
        db.func.coalesce(db.func.sum(InventoryUsage.quantity * InventoryUsage.unit_cost), 0).label("total_cost"),
        db.func.count(db.func.distinct(Student.id)).label("student_count")
    ).select_from(Group)
    
    if should_filter_by_site():
        spending_query = spending_query.filter(Group.site_id == site_id)
    
    spending_by_group = spending_query\
     .outerjoin(Student, Group.id == Student.group_id)\
     .outerjoin(InventoryUsage, InventoryUsage.student_name.like('%' + Student.student_name + '%'))\
     .group_by(Group.name)\
     .having(db.func.sum(InventoryUsage.quantity * InventoryUsage.unit_cost) > 0)\
     .order_by(db.text("total_cost DESC")).all()

    # Item usage by group - Fixed to handle student name mismatches (admins see all sites)
    item_usage_query = db.session.query(
        Group.name,
        InventoryUsage.consumable,
        db.func.sum(InventoryUsage.quantity).label("qty"),
        db.func.sum(InventoryUsage.quantity * InventoryUsage.unit_cost).label("cost")
    ).select_from(Group)
    
    if should_filter_by_site():
        item_usage_query = item_usage_query.filter(Group.site_id == site_id)
    
    item_usage_by_group = item_usage_query\
     .join(Student, Group.id == Student.group_id)\
     .join(InventoryUsage, InventoryUsage.student_name.like('%' + Student.student_name + '%'))\
     .group_by(Group.name, InventoryUsage.consumable)\
     .order_by(Group.name, db.text("cost DESC")).all()

    # Group item usage structured
    group_item_usage = defaultdict(list)
    for group_name, item, qty, cost in item_usage_by_group:
        group_item_usage[group_name].append({
            "item": item,
            "qty": qty,
            "cost": cost
        })

    # Machine usage by group - Fixed to handle student name mismatches (admins see all sites)
    machine_usage_query = db.session.query(
        Group.name,
        Schedule.machine_name,
        db.func.count(Schedule.id).label("slot_count"),
        db.func.sum(
            db.func.strftime('%s', Schedule.end_time) - db.func.strftime('%s', Schedule.start_time)
        ).label("total_seconds")
    ).select_from(Group)
    
    if should_filter_by_site():
        machine_usage_query = machine_usage_query.filter(Group.site_id == site_id)
    
    machine_usage_by_group = machine_usage_query\
     .join(Student, Group.id == Student.group_id)\
     .join(Schedule, Schedule.student_name.like('%' + Student.student_name + '%'))
    
    if should_filter_by_site():
        machine_usage_by_group = machine_usage_by_group.filter(Schedule.site_id == site_id)
    
    machine_usage_by_group = machine_usage_by_group\
     .group_by(Group.name, Schedule.machine_name)\
     .order_by(Group.name).all()

    # Total groups (admins see all sites)
    total_groups = apply_site_filter(Group.query, Group).count()

    # ✅ Fetch all machines for manual scheduling dropdown (admins see all sites)
    all_machines = apply_site_filter(Machine.query, Machine).all()
    students = apply_site_filter(Student.query, Student).order_by(Student.student_name).all()
    groups = apply_site_filter(Group.query, Group).order_by(Group.name).all()
    machines = apply_site_filter(Machine.query, Machine).order_by(Machine.machine_name).all()

    return render_template(
    "index.html",
    machines_in_use=machines_in_use,
    total_machines=total_machines,
    active_modules=active_modules,
    pending_tasks=pending_tasks,
    total_students=total_students,
    total_groups=total_groups,
    total_spent=round(total_spent, 2),
    avg_spend_per_student=round(avg_spend_per_student, 2),
    total_inventory_used=total_inventory_used,
    spending_by_student=spending_by_student,
    spending_by_item=spending_by_item,
    spending_by_group=spending_by_group,
    group_item_usage=dict(group_item_usage),
    machine_usage_by_group=machine_usage_by_group,
    machine_usage_breakdown=machine_usage_breakdown,
    machine_usage_data=usage_data,
    inventory_consumption_data=inv_data,
    machine_trend_data=dict(machine_trend_data),
    inventory_trend_data=dict(inventory_trend_data),
    students=students,
    groups=groups,
    machines=machines
)



# Export to Excel route
@app.route("/download_schedule")
def download_schedule():
    data = [{
        "Student": s.student_name,
        "Group": s.group_name,
        "Machine": s.machine_name,
        "Start Time": s.start_time.strftime("%Y-%m-%d %H:%M"),
        "End Time": s.end_time.strftime("%Y-%m-%d %H:%M"),
        "Extra Time": s.extra_time
    } for s in Schedule.query.all()]
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Schedule")
    output.seek(0)
    
    return send_file(output, as_attachment=True, download_name="Schedule.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

##############################################
# MACHINES
##############################################
@app.route("/machines")
@require_site_access
def machines_list():
    site_id = get_active_site_id()
    # Admins see all sites, regular users see only their site
    all_machines = apply_site_filter(Machine.query, Machine).all()
    return render_template("machines/list.html", machine_levels=all_machines)

@app.route("/machines/add", methods=["GET","POST"])
@require_site_access
def machines_add():
    site_id = get_active_site_id()
    
    if request.method == "POST":
        machine_name = request.form["machine_name"].strip()
        level = request.form["level"].strip()
        new_machine = Machine(machine_name=machine_name, level=level, site_id=site_id)
        db.session.add(new_machine)
        db.session.flush()  # Flush to get the machine ID
        
        # Handle dynamic fields
        dynamic_fields = DynamicField.query.filter_by(model_name='Machine').all()
        for field in dynamic_fields:
            field_value = request.form.get(f'dynamic_{field.field_name}', '').strip()
            
            if field_value:  # Only save if there's a value
                new_value = DynamicFieldValue(
                    field_id=field.id,
                    record_id=new_machine.id,
                    value=field_value
                )
                db.session.add(new_value)
        
        db.session.commit()
        flash("Machine added successfully!", "success")
        return redirect(url_for("machines_list"))
    
    dynamic_fields = DynamicField.query.filter_by(model_name='Machine').all()
    return render_template("machines/add.html", dynamic_fields=dynamic_fields)

@app.route("/machines/edit/<int:machine_id>", methods=["GET","POST"])
@require_site_access
def machines_edit(machine_id):
    site_id = get_active_site_id()
    machine = Machine.query.filter_by(id=machine_id, site_id=site_id).first_or_404()
    
    if request.method == "POST":
        machine.machine_name = request.form["machine_name"].strip()
        machine.level = request.form["level"].strip()
        
        # Handle dynamic fields
        dynamic_fields = DynamicField.query.filter_by(model_name='Machine').all()
        for field in dynamic_fields:
            field_value = request.form.get(f'dynamic_{field.field_name}', '').strip()
            
            # Find or create dynamic field value
            existing_value = DynamicFieldValue.query.filter_by(
                field_id=field.id,
                record_id=machine.id
            ).first()
            
            if field_value:  # If there's a value
                if existing_value:
                    existing_value.value = field_value
                else:
                    new_value = DynamicFieldValue(
                        field_id=field.id,
                        record_id=machine.id,
                        value=field_value
                    )
                    db.session.add(new_value)
            elif existing_value:  # If no value but existing record, delete it
                db.session.delete(existing_value)
        
        db.session.commit()
        flash("Machine updated!", "success")
        return redirect(url_for("machines_list"))
    
    # GET request - load dynamic fields and values
    dynamic_fields = DynamicField.query.filter_by(model_name='Machine').all()
    
    # Get current dynamic field values
    dynamic_values = {}
    for field in dynamic_fields:
        field_value = DynamicFieldValue.query.filter_by(
            field_id=field.id,
            record_id=machine.id
        ).first()
        dynamic_values[field.field_name] = field_value.value if field_value else ""
    
    return render_template("machines/edit.html", 
                         machine=machine,
                         dynamic_fields=dynamic_fields,
                         dynamic_values=dynamic_values)

@app.route("/machines/delete/<int:machine_id>", methods=["POST"])
@require_site_access
def machines_delete(machine_id):
    site_id = get_active_site_id()
    machine = Machine.query.filter_by(id=machine_id, site_id=site_id).first_or_404()
    db.session.delete(machine)
    db.session.commit()
    flash("Machine deleted.", "success")
    return redirect(url_for("machines_list"))

##############################################
# MACHINES BULK UPLOAD
##############################################
@app.route("/machines/upload_form")
@require_site_access
def machines_upload_form():
    return render_template("machines/upload_machines.html")

@app.route("/machines/upload_preview", methods=["POST"])
@require_site_access
def upload_machines_preview():
    """Step 1: Analyze Excel file and show column mapping preview"""
    if "file" not in request.files:
        flash("No file uploaded", "error")
        return redirect(url_for("machines_upload_form"))
    
    file = request.files["file"]
    if file.filename == '':
        flash("No file selected", "error")
        return redirect(url_for("machines_upload_form"))
    
    try:
        import os
        from werkzeug.utils import secure_filename
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join('temp_uploads', filename)
        os.makedirs('temp_uploads', exist_ok=True)
        file.save(temp_path)
        
        # Read Excel file without assuming header row
        df_raw = pd.read_excel(temp_path, header=None)
        
        # Try to detect header row
        header_row = 0
        for idx in range(min(10, len(df_raw))):
            row = df_raw.iloc[idx]
            text_count = sum(isinstance(val, str) and val.strip() != '' for val in row)
            if text_count >= 1:  # At least 1 column with text
                header_row = idx
                break
        
        # Show first 10 rows for user to select header row
        preview_rows = df_raw.head(10).values.tolist()
        
        return render_template('machines/upload_machines_select_header.html',
                             preview_rows=preview_rows,
                             detected_header_row=header_row,
                             filename=filename,
                             total_rows=len(df_raw))
    except Exception as e:
        flash(f"Error reading Excel file: {str(e)}", "error")
        return redirect(url_for("machines_upload_form"))

@app.route("/machines/upload_analyze", methods=["POST"])
@require_site_access
def upload_machines_analyze():
    """Step 1.5: Analyze with specified header row"""
    filename = request.form.get('filename')
    header_row = int(request.form.get('header_row', 0))
    
    if not filename:
        flash("Upload session expired", "error")
        return redirect(url_for("machines_upload_form"))
    
    import os
    temp_path = os.path.join('temp_uploads', filename)
    
    if not os.path.exists(temp_path):
        flash("Upload file not found", "error")
        return redirect(url_for("machines_upload_form"))
    
    try:
        # Read Excel file with specified header row
        df = pd.read_excel(temp_path, header=header_row)
        columns = df.columns.tolist()
        
        # Built-in machine fields
        builtin_fields = [
            'Machine Name', 'machine_name', 'MACHINE NAME', 'Machine_Name',
            'Level', 'level', 'LEVEL'
        ]
        
        # Detect which columns are built-in vs custom
        custom_columns = [col for col in columns if col not in builtin_fields]
        
        # Get existing dynamic fields for Machine model
        existing_dynamic_fields = DynamicField.query.filter_by(model_name='Machine').all()
        existing_field_names = [f.field_name for f in existing_dynamic_fields]
        
        # Helper function to clean preview values
        def clean_preview_value(value):
            if pd.isna(value):
                return ""
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned.lower() in ['nan', 'none', 'null', '-', 'n/a', 'na']:
                    return ""
                return cleaned
            return value
        
        # Preview first 5 data rows
        preview_data = []
        for _, row in df.head(5).iterrows():
            cleaned_row = {col: clean_preview_value(row[col]) for col in columns}
            preview_data.append(cleaned_row)
        
        return render_template('machines/upload_machines_preview.html',
                             columns=columns,
                             custom_columns=custom_columns,
                             existing_field_names=existing_field_names,
                             preview_data=preview_data,
                             filename=filename,
                             header_row=header_row,
                             total_rows=len(df))
    except Exception as e:
        flash(f"Error reading Excel file: {str(e)}", "error")
        return redirect(url_for("machines_upload_form"))

@app.route("/machines/upload_confirm", methods=["POST"])
@require_site_access
def upload_machines_confirm():
    """Step 2: Create dynamic fields and import machines"""
    site_id = get_active_site_id()
    filename = request.form.get('filename')
    header_row = int(request.form.get('header_row', 0))
    
    if not filename:
        flash("Upload session expired", "error")
        return redirect(url_for("machines_upload_form"))
    
    import os
    temp_path = os.path.join('temp_uploads', filename)
    
    if not os.path.exists(temp_path):
        flash("Upload file not found", "error")
        return redirect(url_for("machines_upload_form"))
    
    try:
        # Get selected fields to create as dynamic fields
        selected_fields = request.form.getlist('dynamic_fields')
        field_types = {}
        for field in selected_fields:
            field_types[field] = request.form.get(f'field_type_{field}', 'text')
        
        # Create dynamic fields if they don't exist
        for field_name in selected_fields:
            existing = DynamicField.query.filter_by(model_name='Machine', field_name=field_name).first()
            if not existing:
                new_field = DynamicField(
                    model_name='Machine',
                    field_name=field_name,
                    field_type=field_types.get(field_name, 'text'),
                    required=False
                )
                db.session.add(new_field)
        db.session.commit()
        
        # Import the machines
        df = pd.read_excel(temp_path, header=header_row)
        machines_added = 0
        machines_updated = 0
        
        # Helper function to clean values
        def clean_value(value):
            if pd.isna(value):
                return None
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned.lower() in ['nan', 'none', 'null', '', '-', 'n/a', 'na']:
                    return None
                return cleaned
            return value
        
        for _, row in df.iterrows():
            # Get machine name (required)
            machine_name = (clean_value(row.get("Machine Name")) or 
                          clean_value(row.get("machine_name")) or
                          clean_value(row.get("MACHINE NAME")) or
                          clean_value(row.get("Machine_Name")))
            
            # Skip rows without machine name
            if not machine_name:
                continue
            
            # Get level (optional)
            level = (clean_value(row.get("Level")) or 
                    clean_value(row.get("level")) or
                    clean_value(row.get("LEVEL")))
            
            # Check if machine exists (by name and site)
            existing_machine = Machine.query.filter_by(
                machine_name=str(machine_name),
                site_id=site_id
            ).first()
            
            if existing_machine:
                # Update existing machine
                if level:
                    existing_machine.level = str(level)
                machine = existing_machine
                machines_updated += 1
            else:
                # Create new machine
                machine = Machine(
                    machine_name=str(machine_name),
                    level=str(level) if level else None,
                    site_id=site_id
                )
                db.session.add(machine)
                machines_added += 1
            
            db.session.flush()
            
            # Add or update dynamic field values
            for field_name in selected_fields:
                cleaned_value = clean_value(row.get(field_name))
                if cleaned_value is not None:
                    field_def = DynamicField.query.filter_by(model_name='Machine', field_name=field_name).first()
                    if field_def:
                        # Check if this machine already has a value for this field
                        existing_field_value = DynamicFieldValue.query.filter_by(
                            field_id=field_def.id,
                            record_id=machine.id
                        ).first()
                        
                        if existing_field_value:
                            # Update existing value
                            existing_field_value.value = str(cleaned_value)
                        else:
                            # Create new value
                            field_value = DynamicFieldValue(
                                field_id=field_def.id,
                                record_id=machine.id,
                                value=str(cleaned_value)
                            )
                            db.session.add(field_value)
        
        db.session.commit()
        
        # Clean up temp file
        os.remove(temp_path)
        
        # Create success message
        message_parts = []
        if machines_added > 0:
            message_parts.append(f"{machines_added} new machine(s) added")
        if machines_updated > 0:
            message_parts.append(f"{machines_updated} existing machine(s) updated")
        
        if message_parts:
            success_message = f"Successfully processed: {' and '.join(message_parts)} with {len(selected_fields)} custom field(s)!"
        else:
            success_message = "No machines were added or updated."
        
        flash(success_message, "success")
        return redirect(url_for("machines_list"))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error importing data: {str(e)}", "error")
        return redirect(url_for("machines_upload_form"))


# app.py (add this to support summary views)

@app.route("/api/summary/student/<int:student_id>")
def api_summary_student(student_id):
    student = Student.query.get_or_404(student_id)
    schedules = Schedule.query.filter(Schedule.student_name == student.student_name).all()
    tasks = StudentMiniTaskProgress.query.filter_by(student_id=student.id).all()
    total_hours = sum((s.end_time - s.start_time).seconds for s in schedules) / 3600

    return jsonify({
        "student_name": student.student_name,
        "group": student.group.name if student.group else None,
        "scheduled_slots": len(schedules),
        "total_hours": total_hours,
        "mini_tasks": [{
            "title": t.mini_task.title,
            "attempt_1": t.attempt_1,
            "attempt_2": t.attempt_2,
            "attempt_3": t.attempt_3
        } for t in tasks]
    })

@app.route("/summary/student/<int:student_id>")
def summary_student(student_id):
    student = Student.query.get_or_404(student_id)
    schedules = Schedule.query.filter(Schedule.student_name == student.student_name).all()
    tasks = StudentMiniTaskProgress.query.filter_by(student_id=student.id).all()
    total_hours = sum((s.end_time - s.start_time).seconds for s in schedules) / 3600

    return render_template("summary_student.html", student=student, schedules=schedules, tasks=tasks, total_hours=total_hours)

@app.route("/api/summary/machine/<machine_name>")
def api_summary_machine(machine_name):
    site_id = get_active_site_id()
    schedules = Schedule.query.filter(Schedule.machine_name == machine_name, Schedule.site_id == site_id).all()
    macro_entries = MacroPlan.query.filter(MacroPlan.machine_name == machine_name, MacroPlan.site_id == site_id).all()
    maintenance_logs = MachineMaintenance.query.filter(MachineMaintenance.machine_name == machine_name, MachineMaintenance.site_id == site_id).all()

    return jsonify({
        "machine_name": machine_name,
        "total_slots": len(schedules),
        "total_hours": sum((s.end_time - s.start_time).seconds for s in schedules) / 3600,
        "maintenance": [m.task for m in maintenance_logs],
        "macro_plan": [{
            "date": m.date.isoformat(),
            "usage": m.usage,
            "capacity": m.installed_capacity,
            "planned_maintenance": m.planned_maintenance,
            "breakdown": m.breakdown
        } for m in macro_entries]
    })

@app.route("/summary/machine/<machine_name>")
def summary_machine(machine_name):
    site_id = get_active_site_id()
    schedules = Schedule.query.filter(Schedule.machine_name == machine_name, Schedule.site_id == site_id).all()
    macro_entries = MacroPlan.query.filter(MacroPlan.machine_name == machine_name, MacroPlan.site_id == site_id).all()
    maintenance_logs = MachineMaintenance.query.filter(MachineMaintenance.machine_name == machine_name, MachineMaintenance.site_id == site_id).all()
    total_hours = sum((s.end_time - s.start_time).seconds for s in schedules) / 3600

    return render_template("summary_machine.html", machine_name=machine_name, schedules=schedules, macros=macro_entries, maintenance=maintenance_logs, total_hours=total_hours)

##############################################
# MAINTENANCE
##############################################
@app.route("/maintenance")
@require_site_access
def maintenance_dashboard():
    site_id = get_active_site_id()
    logs = MachineMaintenance.query.filter_by(site_id=site_id).all()
    machines = Machine.query.filter_by(site_id=site_id).all()
    return render_template("maintenance/dashboard.html", logs=logs, machines=machines)

@app.route("/maintenance/add", methods=["POST"])
@require_site_access
def maintenance_add():
    site_id = get_active_site_id()
    machine_name = request.form.get("machine_name", "").strip()
    task = request.form.get("task", "").strip()
    performed_by = request.form.get("performed_by", "").strip()
    notes = request.form.get("notes", "").strip()
    
    new_log = MachineMaintenance(
        machine_name=machine_name,
        task=task,
        performed_by=performed_by,
        notes=notes,
        site_id=site_id
    )
    db.session.add(new_log)
    db.session.commit()
    flash("Maintenance log added!", "success")
    return redirect(url_for("maintenance_dashboard"))

@app.route("/maintenance/edit/<int:log_id>", methods=["GET", "POST"])
@require_site_access
def maintenance_edit(log_id):
    site_id = get_active_site_id()
    log = MachineMaintenance.query.filter_by(id=log_id, site_id=site_id).first_or_404()
    
    if request.method == "POST":
        log.machine_name = request.form.get("machine_name", "").strip()
        log.task = request.form.get("task", "").strip()
        log.performed_by = request.form.get("performed_by", "").strip()
        log.notes = request.form.get("notes", "").strip()
        db.session.commit()
        flash("Maintenance log updated!", "success")
        return redirect(url_for("maintenance_dashboard"))
    machines = Machine.query.filter_by(site_id=site_id).all()
    return render_template("maintenance/edit.html", log=log, machines=machines)

@app.route("/maintenance/delete/<int:log_id>", methods=["POST"])
@require_site_access
def maintenance_delete(log_id):
    site_id = get_active_site_id()
    log = MachineMaintenance.query.filter_by(id=log_id, site_id=site_id).first_or_404()
    db.session.delete(log)
    db.session.commit()
    flash("Maintenance log deleted!", "success")
    return redirect(url_for("maintenance_dashboard"))

##############################################
# INVENTORY
##############################################
@app.route("/inventory")
@require_site_access
def inventory_list():
    site_id = get_active_site_id()
    items = Inventory.query.filter_by(site_id=site_id).all()
    return render_template("inventory/list.html", items=items)

@app.route("/inventory/add", methods=["GET","POST"])
@require_site_access
def inventory_add():
    site_id = get_active_site_id()
    
    if request.method == "POST":
        name = request.form.get("item_name", "").strip()
        quantity_str = request.form.get("quantity", "0")
        cost_str = request.form.get("cost_per_unit", "0")
        try:
            quantity = int(quantity_str)
        except:
            quantity = 0
        try:
            cost = float(cost_str)
        except:
            cost = 0.0

        new_item = Inventory(item_name=name, quantity=quantity, cost_per_unit=cost, site_id=site_id)
        db.session.add(new_item)
        db.session.commit()
        flash(f"Inventory item '{name}' added.", "success")
        return redirect(url_for("inventory_list"))
    return render_template("inventory/add.html")

@app.route("/inventory/edit/<int:item_id>", methods=["GET", "POST"])
@require_site_access
def inventory_edit(item_id):
    site_id = get_active_site_id()
    item = Inventory.query.filter_by(id=item_id, site_id=site_id).first_or_404()
    if request.method == "POST":
        item.item_name = request.form.get("item_name", "").strip()
        try:
            item.quantity = int(request.form.get("quantity", 0))
        except:
            item.quantity = 0
        try:
            item.cost_per_unit = float(request.form.get("cost_per_unit", 0))
        except:
            item.cost_per_unit = 0.0
        
        db.session.commit()
        flash("Inventory item updated successfully!", "success")
        return redirect(url_for("inventory_list"))
    return render_template("inventory/edit.html", item=item)

@app.route("/inventory/delete/<int:item_id>", methods=["POST"])
@require_site_access
def inventory_delete(item_id):
    site_id = get_active_site_id()
    item = Inventory.query.filter_by(id=item_id, site_id=site_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Inventory item deleted successfully!", "success")
    return redirect(url_for("inventory_list"))


@app.route("/inventory/assign", methods=["GET", "POST"])
def assign_inventory():
    students = Student.query.all()
    
    # Get all student-task combinations (from progress records and schedules)
    # Create a list of dicts with student_id, mini_task_id, and mini_task info
    task_list = []
    
    # Add tasks from progress records
    progress_tasks = StudentMiniTaskProgress.query.all()
    for pt in progress_tasks:
        if pt.mini_task:
            task_list.append({
                'id': pt.id,
                'student_id': pt.student_id,
                'mini_task_id': pt.mini_task_id,
                'mini_task_title': pt.mini_task.title,
                'type': 'progress'
            })
    
    # Add tasks from schedule (for students who may not have progress yet)
    schedules = Schedule.query.all()
    for sched in schedules:
        # Find student by name
        student = Student.query.filter_by(student_name=sched.student_name).first()
        if student:
            # Check if this combination already exists in task_list
            existing = any(t.get('student_id') == student.id and t.get('schedule_id') == sched.id for t in task_list)
            if not existing and sched.machine_name:
                task_list.append({
                    'id': f"sched_{sched.id}",
                    'student_id': student.id,
                    'schedule_id': sched.id,
                    'mini_task_title': f"Scheduled: {sched.machine_name} ({sched.start_time.strftime('%Y-%m-%d %H:%M') if sched.start_time else 'TBD'})",
                    'type': 'schedule'
                })
    
    inventory = Inventory.query.all()

    if request.method == "POST":
        student_id = request.form["student_id"]
        task_id = request.form["task_id"]
        inventory_id = request.form["inventory_id"]
        quantity = int(request.form["quantity"])

        student = Student.query.get(student_id)
        item = Inventory.query.get(inventory_id)
        
        # Handle both progress tasks and schedule tasks
        if task_id.startswith("sched_"):
            schedule_id = int(task_id.replace("sched_", ""))
            student_task_id = None
        else:
            task = StudentMiniTaskProgress.query.get(task_id)
            student_task_id = task.id if task else None

        usage = InventoryUsage(
            consumable=item.item_name,
            student_name=student.student_name,
            quantity=quantity,
            unit_cost=item.cost_per_unit,
            student_task_id=student_task_id
        )
        item.quantity -= quantity
        db.session.add(usage)
        db.session.commit()

        flash("Inventory assigned successfully.", "success")
        return redirect(url_for("assign_inventory"))

    return render_template("assign_inventory.html", students=students, tasks=task_list, inventory=inventory)





##############################################
# OVERHEADS
##############################################
@app.route("/overheads")
@require_site_access
def overheads_dashboard():
    site_id = get_active_site_id()
    overhead_list = OverheadCost.query.filter_by(site_id=site_id).all()
    return render_template("overheads/dashboard.html", overhead_list=overhead_list)

@app.route("/overheads/add", methods=["POST"])
@require_site_access
def overheads_add():
    site_id = get_active_site_id()
    description = request.form.get("description", "").strip()
    cost = float(request.form.get("cost", 0))
    
    new_overhead = OverheadCost(description=description, cost=cost, site_id=site_id)
    db.session.add(new_overhead)
    db.session.commit()
    flash("Overhead cost added!", "success")
    return redirect(url_for("overheads_dashboard"))

@app.route("/overheads/edit/<int:overhead_id>", methods=["GET", "POST"])
@require_site_access
def overheads_edit(overhead_id):
    site_id = get_active_site_id()
    overhead = OverheadCost.query.filter_by(id=overhead_id, site_id=site_id).first_or_404()
    if request.method == "POST":
        overhead.description = request.form.get("description", "").strip()
        overhead.cost = float(request.form.get("cost", 0))
        db.session.commit()
        flash("Overhead cost updated!", "success")
        return redirect(url_for("overheads_dashboard"))
    return render_template("overheads/edit.html", overhead=overhead)

@app.route("/overheads/delete/<int:overhead_id>", methods=["POST"])
@require_site_access
def overheads_delete(overhead_id):
    site_id = get_active_site_id()
    overhead = OverheadCost.query.filter_by(id=overhead_id, site_id=site_id).first_or_404()
    db.session.delete(overhead)
    db.session.commit()
    flash("Overhead cost deleted!", "success")
    return redirect(url_for("overheads_dashboard"))

##############################################
# MACROPLAN
##############################################
@app.route("/macroplan")
@require_site_access
def macroplan_page():
    site_id = get_active_site_id()
    rows = MacroPlan.query.filter_by(site_id=site_id).all()
    machines = Machine.query.filter_by(site_id=site_id).all()
    return render_template("macroplan.html", rows=rows, machines=machines)

@app.route("/macroplan/add", methods=["POST"])
@require_site_access
def macroplan_add():
    site_id = get_active_site_id()
    machine_name = request.form.get("machine_name", "").strip()
    date_str = request.form.get("date")
    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    planned_maintenance = float(request.form.get("planned_maintenance", 0))
    breakdown = float(request.form.get("breakdown", 0))
    installed_capacity = float(request.form.get("installed_capacity", 0))
    usage = float(request.form.get("usage", 0))
    
    new_plan = MacroPlan(
        machine_name=machine_name,
        date=date_obj,
        planned_maintenance=planned_maintenance,
        breakdown=breakdown,
        installed_capacity=installed_capacity,
        usage=usage,
        site_id=site_id
    )
    db.session.add(new_plan)
    db.session.commit()
    flash("Macro plan added!", "success")
    return redirect(url_for("macroplan_page"))

@app.route("/macroplan/edit/<int:plan_id>", methods=["GET", "POST"])
@require_site_access
def macroplan_edit(plan_id):
    site_id = get_active_site_id()
    plan = MacroPlan.query.filter_by(id=plan_id, site_id=site_id).first_or_404()
    if request.method == "POST":
        plan.machine_name = request.form.get("machine_name", "").strip()
        date_str = request.form.get("date")
        plan.date = datetime.strptime(date_str, "%Y-%m-%d").date()
        plan.planned_maintenance = float(request.form.get("planned_maintenance", 0))
        plan.breakdown = float(request.form.get("breakdown", 0))
        plan.installed_capacity = float(request.form.get("installed_capacity", 0))
        plan.usage = float(request.form.get("usage", 0))
        db.session.commit()
        flash("Macro plan updated!", "success")
        return redirect(url_for("macroplan_page"))
    machines = Machine.query.filter_by(site_id=site_id).all()
    return render_template("edit_macroplan.html", plan=plan, machines=machines)

@app.route("/macroplan/delete/<int:plan_id>", methods=["POST"])
@require_site_access
def macroplan_delete(plan_id):
    site_id = get_active_site_id()
    plan = MacroPlan.query.filter_by(id=plan_id, site_id=site_id).first_or_404()
    db.session.delete(plan)
    db.session.commit()
    flash("Macro plan deleted!", "success")
    return redirect(url_for("macroplan_page"))

##############################################
# SITE MANAGEMENT
##############################################
@app.route('/switch_site/<int:site_id>')
@login_required
def switch_site(site_id):
    """Switch to a different site"""
    if not current_user.is_super_admin() and not current_user.has_site_access(site_id):
        flash('You do not have access to this site.', 'danger')
        return redirect(url_for('index'))
    
    site = Site.query.get_or_404(site_id)
    
    if not site.is_active:
        flash('This site is currently inactive.', 'warning')
        return redirect(url_for('index'))
    
    if set_active_site(site.id):
        flash(f'Switched to {site.name}', 'success')
    
    return redirect(url_for('index'))

@app.route('/select_site')
@login_required
def select_site():
    """Page to select a site if none is active"""
    if current_user.is_super_admin():
        sites = Site.query.filter_by(is_active=True).all()
    else:
        sites = current_user.sites
    
    return render_template('select_site.html', sites=sites)

@app.context_processor
def inject_site_info():
    """Make site info available in all templates"""
    # Check if admin is viewing all sites
    is_admin_viewing_all = False
    site_name = session.get('active_site_name', 'No Site Selected')
    
    if current_user.is_authenticated and current_user.is_super_admin():
        is_admin_viewing_all = True
        site_name = f"All Sites ({session.get('active_site_name', 'All')})"
    
    return {
        'active_site_id': get_active_site_id(),
        'active_site_name': site_name,
        'active_site_code': session.get('active_site_code', ''),
        'user_sites': current_user.get_accessible_sites() if current_user.is_authenticated else [],
        'is_admin_viewing_all': is_admin_viewing_all,
        'now': datetime.now
    }

##############################################
# SITE MANAGEMENT CRUD
##############################################
@app.route('/sites')
@login_required
def list_sites():
    """List all sites - Admin only"""
    if not current_user.is_super_admin():
        flash('Only administrators can manage sites.', 'danger')
        return redirect(url_for('index'))
    
    sites = Site.query.order_by(Site.name).all()
    
    # Get counts for each site
    for site in sites:
        site.user_count = len(site.users)
        site.student_count = Student.query.filter_by(site_id=site.id).count()
        site.machine_count = Machine.query.filter_by(site_id=site.id).count()
    
    return render_template('sites/list.html', sites=sites)

@app.route('/sites/add', methods=['GET', 'POST'])
@login_required
def add_site():
    """Create a new site - Admin only"""
    if not current_user.is_super_admin():
        flash('Only administrators can create sites.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip().upper()
        location = request.form.get('location', '').strip()
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        is_active = request.form.get('is_active') == 'on'
        
        if not name or not code:
            flash('Site name and code are required.', 'danger')
            return redirect(url_for('add_site'))
        
        existing = Site.query.filter_by(code=code).first()
        if existing:
            flash(f'Site code "{code}" already exists.', 'danger')
            return redirect(url_for('add_site'))
        
        new_site = Site(
            name=name,
            code=code,
            location=location,
            address=address,
            phone=phone,
            email=email,
            is_active=is_active,
            created_date=datetime.utcnow()
        )
        
        db.session.add(new_site)
        db.session.commit()
        
        flash(f'Site "{name}" created successfully!', 'success')
        return redirect(url_for('list_sites'))
    
    return render_template('sites/add.html')

@app.route('/sites/edit/<int:site_id>', methods=['GET', 'POST'])
@login_required
def edit_site(site_id):
    """Edit a site - Admin only"""
    if not current_user.is_super_admin():
        flash('Only administrators can edit sites.', 'danger')
        return redirect(url_for('index'))
    
    site = Site.query.get_or_404(site_id)
    
    if request.method == 'POST':
        site.name = request.form.get('name', '').strip()
        site.code = request.form.get('code', '').strip().upper()
        site.location = request.form.get('location', '').strip()
        site.address = request.form.get('address', '').strip()
        site.phone = request.form.get('phone', '').strip()
        site.email = request.form.get('email', '').strip()
        site.is_active = request.form.get('is_active') == 'on'
        
        if not site.name or not site.code:
            flash('Site name and code are required.', 'danger')
            return redirect(url_for('edit_site', site_id=site_id))
        
        existing = Site.query.filter(Site.code == site.code, Site.id != site_id).first()
        if existing:
            flash(f'Site code "{site.code}" already exists.', 'danger')
            return redirect(url_for('edit_site', site_id=site_id))
        
        db.session.commit()
        flash(f'Site "{site.name}" updated successfully!', 'success')
        return redirect(url_for('list_sites'))
    
    return render_template('sites/edit.html', site=site)

@app.route('/sites/delete/<int:site_id>', methods=['POST'])
@login_required
def delete_site(site_id):
    """Delete a site - Admin only"""
    if not current_user.is_super_admin():
        flash('Only administrators can delete sites.', 'danger')
        return redirect(url_for('index'))
    
    site = Site.query.get_or_404(site_id)
    
    student_count = Student.query.filter_by(site_id=site_id).count()
    machine_count = Machine.query.filter_by(site_id=site_id).count()
    
    if student_count > 0 or machine_count > 0:
        flash(f'Cannot delete site "{site.name}" because it has {student_count} students and {machine_count} machines.', 'danger')
        return redirect(url_for('list_sites'))
    
    site_name = site.name
    db.session.delete(site)
    db.session.commit()
    
    flash(f'Site "{site_name}" deleted successfully!', 'success')
    return redirect(url_for('list_sites'))

@app.route('/sites/<int:site_id>/users')
@login_required
def site_users(site_id):
    """Manage users for a site - Admin only"""
    if not current_user.is_super_admin():
        flash('Only administrators can manage site users.', 'danger')
        return redirect(url_for('index'))
    
    site = Site.query.get_or_404(site_id)
    all_users = User.query.order_by(User.username).all()
    
    from sqlalchemy import and_
    from auth_models import user_sites
    
    site_user_data = []
    for user in all_users:
        has_access = site in user.sites
        is_manager = False
        
        if has_access:
            result = db.session.execute(
                user_sites.select().where(
                    and_(
                        user_sites.c.user_id == user.id,
                        user_sites.c.site_id == site_id
                    )
                )
            ).fetchone()
            is_manager = result.is_manager if result else False
        
        site_user_data.append({
            'user': user,
            'has_access': has_access,
            'is_manager': is_manager
        })
    
    return render_template('sites/users.html', site=site, site_user_data=site_user_data)

@app.route('/sites/<int:site_id>/assign_user/<int:user_id>', methods=['POST'])
@login_required
def assign_user_to_site(site_id, user_id):
    """Assign a user to a site - Admin only"""
    if not current_user.is_super_admin():
        flash('Only administrators can assign users to sites.', 'danger')
        return redirect(url_for('index'))
    
    site = Site.query.get_or_404(site_id)
    user = User.query.get_or_404(user_id)
    is_manager = request.form.get('is_manager') == 'on'
    
    if site not in user.sites:
        user.sites.append(site)
        db.session.commit()
    
    from auth_models import user_sites
    from sqlalchemy import and_
    
    db.session.execute(
        user_sites.update().where(
            and_(
                user_sites.c.user_id == user_id,
                user_sites.c.site_id == site_id
            )
        ).values(is_manager=is_manager)
    )
    db.session.commit()
    
    flash(f'User "{user.username}" assigned to site "{site.name}"' + (' as manager' if is_manager else '') + '.', 'success')
    return redirect(url_for('site_users', site_id=site_id))

@app.route('/sites/<int:site_id>/remove_user/<int:user_id>', methods=['POST'])
@login_required
def remove_user_from_site(site_id, user_id):
    """Remove a user from a site - Admin only"""
    if not current_user.is_super_admin():
        flash('Only administrators can remove users from sites.', 'danger')
        return redirect(url_for('index'))
    
    site = Site.query.get_or_404(site_id)
    user = User.query.get_or_404(user_id)
    
    if site in user.sites:
        user.sites.remove(site)
        db.session.commit()
        flash(f'User "{user.username}" removed from site "{site.name}".', 'success')
    else:
        flash(f'User "{user.username}" does not have access to site "{site.name}".', 'warning')
    
    return redirect(url_for('site_users', site_id=site_id))

##############################################
# STUDENTS
##############################################
from sqlalchemy.orm import joinedload

@app.route("/students")
@require_site_access
def list_students():
    site_id = get_active_site_id()
    # Admins see all sites, regular users see only their site
    students = apply_site_filter(Student.query, Student).options(
        joinedload(Student.group),
        joinedload(Student.progress).joinedload(StudentMiniTaskProgress.mini_task)
    ).all()
    
    # Get dynamic fields for Student model
    dynamic_fields = DynamicField.query.filter_by(model_name='Student').all()
    
    # Add dynamic field values to each student
    for student in students:
        student.dynamic_fields = {}
        for field in dynamic_fields:
            field_value = DynamicFieldValue.query.filter_by(
                field_id=field.id,
                record_id=student.id
            ).first()
            student.dynamic_fields[field.field_name] = field_value.value if field_value else None
    
    # Get all groups for filtering (admins see all sites)
    groups = apply_site_filter(Group.query, Group).all()
    
    return render_template("students/list.html", students=students, dynamic_fields=dynamic_fields, groups=groups)

@app.route("/students/export")
@login_required
@require_site_access
def export_students():
    import pandas as pd
    from io import BytesIO, StringIO
    
    site_id = get_active_site_id()
    
    # Get parameters
    fields = request.args.get('fields', '').split(',')
    student_ids = request.args.get('students', '')
    search_term = request.args.get('search', '')
    export_format = request.args.get('format', 'excel')
    
    # Get students (site-specific)
    query = Student.query.filter_by(site_id=site_id).options(joinedload(Student.group))
    
    if student_ids != 'all' and student_ids:
        student_ids = [int(id) for id in student_ids.split(',')]
        query = query.filter(Student.id.in_(student_ids))
    elif search_term:
        query = query.filter(
            db.or_(
                Student.student_name.contains(search_term),
                Student.student_number.contains(search_term)
            )
        )
    
    students = query.all()
    
    # Get dynamic fields
    dynamic_fields = DynamicField.query.filter_by(model_name='Student').all()
    dynamic_field_names = [f.field_name for f in dynamic_fields]
    
    # Build data for export
    data = []
    for student in students:
        row = {}
        
        # Standard fields
        if 'student_number' in fields:
            row['Student Number'] = student.student_number or ''
        if 'student_name' in fields:
            row['Name'] = student.student_name
        if 'group' in fields:
            row['Group'] = student.group.name if student.group else 'No Group'
        
        # Dynamic fields
        for field_name in fields:
            if field_name in dynamic_field_names:
                field = next((f for f in dynamic_fields if f.field_name == field_name), None)
                if field:
                    field_value = DynamicFieldValue.query.filter_by(
                        field_id=field.id,
                        record_id=student.id
                    ).first()
                    row[field_name.replace('_', ' ').title()] = field_value.value if field_value else ''
        
        data.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    if export_format == 'csv':
        # Export as CSV
        output = StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return send_file(
            BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'students_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    else:
        # Export as Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Students', index=False)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'students_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )

@app.route("/students/add", methods=["GET", "POST"])
@require_site_access
def students_add():
    site_id = get_active_site_id()
    
    if request.method == "POST":
        student_number = request.form.get("student_number", "").strip() or None
        student_name = request.form["student_name"].strip()
        group_id = request.form.get("group_id")
        
        new_student = Student(
            student_number=student_number,
            student_name=student_name,
            site_id=site_id,
            group_id=group_id if group_id else None
        )
        db.session.add(new_student)
        db.session.flush()  # Flush to get the student ID
        
        # Handle dynamic fields
        dynamic_fields = DynamicField.query.filter_by(model_name='Student').all()
        for field in dynamic_fields:
            field_value = request.form.get(f'dynamic_{field.field_name}', '').strip()
            
            if field_value:  # Only save if there's a value
                new_value = DynamicFieldValue(
                    field_id=field.id,
                    record_id=new_student.id,
                    value=field_value
                )
                db.session.add(new_value)
        
        db.session.commit()
        flash("Student added successfully!", "success")
        return redirect(url_for("list_students"))
    
    groups = Group.query.filter_by(site_id=site_id).all()
    dynamic_fields = DynamicField.query.filter_by(model_name='Student').all()
    return render_template("students/add.html", groups=groups, dynamic_fields=dynamic_fields)

@app.route("/students/edit/<int:student_id>", methods=["GET", "POST"])
@require_site_access
def students_edit(student_id):
    site_id = get_active_site_id()
    student = Student.query.filter_by(id=student_id, site_id=site_id).first_or_404()
    
    if request.method == "POST":
        student.student_number = request.form.get("student_number", "").strip() or None
        student.student_name = request.form["student_name"].strip()
        group_id = request.form.get("group_id")
        student.group_id = group_id if group_id else None
        
        # Handle dynamic fields
        dynamic_fields = DynamicField.query.filter_by(model_name='Student').all()
        for field in dynamic_fields:
            field_value = request.form.get(f'dynamic_{field.field_name}', '').strip()
            
            # Find or create dynamic field value
            existing_value = DynamicFieldValue.query.filter_by(
                field_id=field.id,
                record_id=student.id
            ).first()
            
            if field_value:  # If there's a value
                if existing_value:
                    existing_value.value = field_value
                else:
                    new_value = DynamicFieldValue(
                        field_id=field.id,
                        record_id=student.id,
                        value=field_value
                    )
                    db.session.add(new_value)
            elif existing_value:  # If no value but existing record, delete it
                db.session.delete(existing_value)
        
        db.session.commit()
        flash("Student updated successfully!", "success")
        return redirect(url_for("list_students"))
    
    # GET request - load dynamic fields and values
    groups = Group.query.filter_by(site_id=site_id).all()
    dynamic_fields = DynamicField.query.filter_by(model_name='Student').all()
    
    # Get current dynamic field values
    dynamic_values = {}
    for field in dynamic_fields:
        field_value = DynamicFieldValue.query.filter_by(
            field_id=field.id,
            record_id=student.id
        ).first()
        dynamic_values[field.field_name] = field_value.value if field_value else ""
    
    return render_template("students/edit.html", 
                         student=student, 
                         groups=groups,
                         dynamic_fields=dynamic_fields,
                         dynamic_values=dynamic_values)

@app.route("/students/delete/<int:student_id>", methods=["POST"])
@require_site_access
def students_delete(student_id):
    site_id = get_active_site_id()
    student = Student.query.filter_by(id=student_id, site_id=site_id).first_or_404()
    db.session.delete(student)
    db.session.commit()
    flash("Student deleted successfully!", "success")
    return redirect(url_for("list_students"))

@app.route("/select_module/<int:student_id>")
def select_module(student_id):
    """Select a module/mini-task to record an attempt for a student"""
    student = Student.query.get_or_404(student_id)
    modules = Module.query.all()
    return render_template("students/select_module.html", student=student, modules=modules)

@app.route("/record_module_progress/<int:student_id>/<int:module_id>", methods=["GET", "POST"])
def record_module_progress(student_id, module_id):
    """Record pass/fail for an entire module (editable)"""
    student = Student.query.get_or_404(student_id)
    module = Module.query.get_or_404(module_id)
    
    # Get existing progress or create new
    progress = StudentModuleProgress.query.filter_by(
        student_id=student_id,
        module_id=module_id
    ).first()
    
    if request.method == "POST":
        if not progress:
            progress = StudentModuleProgress(
                student_id=student_id,
                module_id=module_id
            )
            db.session.add(progress)
        
        progress.result = request.form.get("result")
        progress.notes = request.form.get("notes", "").strip()
        
        # Handle completion date - can be manually set or auto-set
        completion_date_str = request.form.get("completion_date", "").strip()
        if completion_date_str:
            # Manual date provided
            progress.completion_date = datetime.strptime(completion_date_str, '%Y-%m-%dT%H:%M')
        elif progress.result in ['Pass', 'Complete']:
            # Auto-set for Pass/Complete if not already set
            if not progress.completion_date:
                progress.completion_date = datetime.utcnow()
        
        db.session.commit()
        flash(f"Module result recorded for {student.student_name} on {module.name}!", "success")
        return redirect(url_for("list_students"))
    
    return render_template("students/record_module_progress.html", 
                         student=student, 
                         module=module, 
                         progress=progress)

@app.route("/record_attempt/<int:student_id>/<int:mini_task_id>", methods=["GET", "POST"])
def record_attempt(student_id, mini_task_id):
    """Record or update attempts for a student on a mini-task"""
    student = Student.query.get_or_404(student_id)
    mini_task = MiniTask.query.get_or_404(mini_task_id)
    
    # Get existing progress or create new
    progress = StudentMiniTaskProgress.query.filter_by(
        student_id=student_id,
        mini_task_id=mini_task_id
    ).first()
    
    if not progress:
        progress = StudentMiniTaskProgress(
            student_id=student_id,
            mini_task_id=mini_task_id
        )
        db.session.add(progress)
        db.session.flush()
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "add_attempt":
            # Add a new attempt with custom date
            attempt_type = request.form.get("attempt_type")
            result = request.form.get("result")
            notes = request.form.get("attempt_notes", "").strip()
            attempt_date_str = request.form.get("attempt_date", "").strip()
            
            # Parse the date
            attempt_date = datetime.strptime(attempt_date_str, '%Y-%m-%dT%H:%M') if attempt_date_str else datetime.utcnow()
            
            new_attempt = Attempt(
                progress_id=progress.id,
                attempt_type=attempt_type,
                result=result,
                notes=notes,
                attempt_date=attempt_date
            )
            db.session.add(new_attempt)
            db.session.commit()
            flash(f"New {attempt_type} attempt added: {result}!", "success")
            return redirect(url_for("record_attempt", student_id=student_id, mini_task_id=mini_task_id))
        
        elif action == "edit_attempt":
            # Edit an existing attempt (fully editable)
            attempt_id = request.form.get("attempt_id")
            attempt = Attempt.query.get(attempt_id)
            if attempt and attempt.progress_id == progress.id:
                attempt.result = request.form.get("result")
                attempt.notes = request.form.get("notes", "").strip()
                
                # Update date if provided
                attempt_date_str = request.form.get("attempt_date", "").strip()
                if attempt_date_str:
                    attempt.attempt_date = datetime.strptime(attempt_date_str, '%Y-%m-%dT%H:%M')
                
                db.session.commit()
                flash("Attempt updated!", "success")
            return redirect(url_for("record_attempt", student_id=student_id, mini_task_id=mini_task_id))
        
        elif action == "delete_attempt":
            # Delete an attempt
            attempt_id = request.form.get("attempt_id")
            attempt = Attempt.query.get(attempt_id)
            if attempt and attempt.progress_id == progress.id:
                db.session.delete(attempt)
                db.session.commit()
                flash("Attempt deleted!", "success")
            return redirect(url_for("record_attempt", student_id=student_id, mini_task_id=mini_task_id))
        
        else:
            # Update notes
            progress.notes = request.form.get("notes", "").strip()
            db.session.commit()
            flash(f"Notes updated for {student.student_name} on {mini_task.title}!", "success")
            return redirect(url_for("list_students"))
    
    # Get all attempts grouped by type
    attempts_by_type = {
        'regular': Attempt.query.filter_by(progress_id=progress.id, attempt_type='regular').order_by(Attempt.attempt_date).all(),
        'iwp': Attempt.query.filter_by(progress_id=progress.id, attempt_type='iwp').order_by(Attempt.attempt_date).all(),
        'cwp': Attempt.query.filter_by(progress_id=progress.id, attempt_type='cwp').order_by(Attempt.attempt_date).all(),
        'oe': Attempt.query.filter_by(progress_id=progress.id, attempt_type='oe').order_by(Attempt.attempt_date).all(),
    }
    
    return render_template("students/record_attempt.html", 
                         student=student, 
                         mini_task=mini_task, 
                         progress=progress,
                         attempts_by_type=attempts_by_type)


@app.route("/view_data")
def view_data():
    """
    Display all students (with group, level, mark, etc.)
    """
    all_students = Student.query.all()
    if not all_students:
        flash("No data found.", "error")
        return redirect(url_for("index"))

    df_data = []
    for s in all_students:
        df_data.append({
            "Student Name": s.student_name,
            "Group": s.group.name if s.group else ""
        })
    student_df = pd.DataFrame(df_data)
    data_html = student_df.to_html(classes='data-table', index=False)
    return render_template('view_data.html', data_html=data_html)

@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        name = request.form.get("student_name", "").strip()
        student = Student.query.filter_by(student_name=name).first()
        if student:
            session["student_id"] = student.id
            return redirect(url_for("student_dashboard"))
        flash("Student not found. Please try again.", "danger")
    return render_template("login_student.html")

@app.route("/student/logout")
def student_logout():
    session.pop("student_id", None)
    return redirect(url_for("student_login"))

@app.route("/student/dashboard")
def student_dashboard():
    if "student_id" not in session:
        return redirect(url_for("student_login"))

    student = Student.query.get_or_404(session["student_id"])
    schedules = Schedule.query.filter_by(student_name=student.student_name).order_by(Schedule.start_time).all()
    progress = StudentMiniTaskProgress.query.filter_by(student_id=student.id).all()
    
    # Calculate total training hours
    total_hours = sum((s.end_time - s.start_time).total_seconds() / 3600 for s in schedules)
    
    # Get upcoming schedules (future)
    now = datetime.utcnow()
    upcoming_schedules = [s for s in schedules if s.start_time > now][:5]
    
    # Get past schedules
    past_schedules = [s for s in schedules if s.start_time <= now]
    
    # Calculate completion rate
    total_tasks = len(progress)
    completed_tasks = sum(1 for p in progress if p.attempt_1 or p.attempt_2 or p.attempt_3)
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Get inventory usage for this student (use LIKE to match partial names)
    inventory_usage = InventoryUsage.query.filter(InventoryUsage.student_name.like(f'%{student.student_name}%')).all()
    total_inventory_cost = sum(i.quantity * i.unit_cost for i in inventory_usage)
    
    # Get modules and mini-tasks
    modules_progress = {}
    for p in progress:
        module_name = p.mini_task.module.name
        if module_name not in modules_progress:
            modules_progress[module_name] = []
        modules_progress[module_name].append(p)
    
    # Recent activity
    recent_activity = []
    for p in progress[-5:]:
        if p.attempt_1 or p.attempt_2 or p.attempt_3:
            recent_activity.append({
                "task": p.mini_task.title,
                "module": p.mini_task.module.name,
                "latest_attempt": p.attempt_3 or p.attempt_2 or p.attempt_1
            })
    
    return render_template(
        "student_dashboard.html", 
        student=student, 
        schedules=schedules,
        upcoming_schedules=upcoming_schedules,
        past_schedules=past_schedules,
        progress=progress,
        total_hours=round(total_hours, 2),
        completion_rate=round(completion_rate, 1),
        inventory_usage=inventory_usage,
        total_inventory_cost=round(total_inventory_cost, 2),
        modules_progress=modules_progress,
        recent_activity=recent_activity
    )

@app.route("/profile/student/<int:student_id>")
def profile_student(student_id):
    student = Student.query.get_or_404(student_id)
    progress = StudentMiniTaskProgress.query.filter_by(student_id=student.id).all()
    # Use LIKE query to match partial student names (e.g., "Maila Frans" matches "AGT21006 Maila Frans")
    inventory = InventoryUsage.query.filter(InventoryUsage.student_name.like(f'%{student.student_name}%')).all()
    schedule = Schedule.query.filter(Schedule.student_name.like(f'%{student.student_name}%')).all()
    
    # Get dynamic field values
    dynamic_fields = DynamicField.query.filter_by(model_name='Student').all()
    dynamic_data = {}
    for field in dynamic_fields:
        field_value = DynamicFieldValue.query.filter_by(
            field_id=field.id,
            record_id=student.id
        ).first()
        dynamic_data[field.field_name] = field_value.value if field_value else ""

    response_data = {
        "full_name": student.student_name,
        "student_number": student.student_number or "",
        "group": student.group.name if student.group else "",
        "current_module": progress[-1].mini_task.module.name if progress else "",
        "phone_number": dynamic_data.get("CONTACT NUMBER", dynamic_data.get("Phone", "")),
        "email": dynamic_data.get("Email", ""),
        "mini_tasks": [{
            "mini_task_title": p.mini_task.title,
            "attempt_1": p.attempt_1 or "NYP",
            "attempt_2": p.attempt_2 or "NYP",
            "attempt_3": p.attempt_3 or "NYP"
        } for p in progress],
        "inventory_usage": [{
            "item_name": i.consumable or "Unknown",
            "quantity_used": i.quantity or 0,
            "date_issued": i.date_issued.strftime("%Y-%m-%d") if i.date_issued else "N/A"
        } for i in inventory],
        "schedule": [{
            "machine": s.machine_name or "Unknown",
            "start_time": s.start_time.strftime("%Y-%m-%d %H:%M") if s.start_time else "N/A",
            "end_time": s.end_time.strftime("%H:%M") if s.end_time else "N/A"
        } for s in schedule]
    }
    
    # Add all dynamic fields to the response
    response_data["dynamic_fields"] = dynamic_data
    
    return jsonify(response_data)

##############################################
# UPLOAD STUDENTS (EXCEL)
##############################################
@app.route("/students/upload_form")
def students_upload_form():
    groups = Group.query.all()
    return render_template("upload_students.html", groups=groups)

@app.route("/students/upload_preview", methods=["POST"])
def upload_students_preview():
    """Step 1: Analyze Excel file and show column mapping preview"""
    if "file" not in request.files:
        flash("No file uploaded", "error")
        return redirect(url_for("students_upload_form"))
    
    file = request.files["file"]
    if file.filename == '':
        flash("No file selected", "error")
        return redirect(url_for("students_upload_form"))
    
    # Get intake group ID
    intake_group_id = request.form.get("intake_group_id")
    if not intake_group_id:
        flash("Please select an intake group", "error")
        return redirect(url_for("students_upload_form"))
    
    # Verify group exists
    intake_group = Group.query.get(intake_group_id)
    if not intake_group:
        flash("Invalid intake group selected", "error")
        return redirect(url_for("students_upload_form"))
    
    try:
        import os
        from werkzeug.utils import secure_filename
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join('temp_uploads', filename)
        os.makedirs('temp_uploads', exist_ok=True)
        file.save(temp_path)
        
        # Read Excel file without assuming header row
        df_raw = pd.read_excel(temp_path, header=None)
        
        # Try to detect header row (look for rows with text-heavy content)
        header_row = 0
        for idx in range(min(10, len(df_raw))):  # Check first 10 rows
            row = df_raw.iloc[idx]
            # Count how many cells are non-empty strings
            text_count = sum(isinstance(val, str) and val.strip() != '' for val in row)
            if text_count >= 2:  # If at least 2 columns have text
                header_row = idx
                break
        
        # Show first 10 rows for user to select header row
        preview_rows = df_raw.head(10).values.tolist()
        
        return render_template('upload_students_select_header.html',
                             preview_rows=preview_rows,
                             detected_header_row=header_row,
                             filename=filename,
                             total_rows=len(df_raw),
                             intake_group_id=intake_group_id,
                             intake_group_name=intake_group.name)
    except Exception as e:
        flash(f"Error reading Excel file: {str(e)}", "error")
        return redirect(url_for("students_upload_form"))

@app.route("/students/upload_analyze", methods=["POST"])
def upload_students_analyze():
    """Step 1.5: Analyze with specified header row"""
    filename = request.form.get('filename')
    header_row = int(request.form.get('header_row', 0))
    intake_group_id = request.form.get('intake_group_id')
    
    if not filename:
        flash("Upload session expired", "error")
        return redirect(url_for("students_upload_form"))
    
    if not intake_group_id:
        flash("Intake group not specified", "error")
        return redirect(url_for("students_upload_form"))
    
    # Get intake group name
    intake_group = Group.query.get(intake_group_id)
    if not intake_group:
        flash("Invalid intake group", "error")
        return redirect(url_for("students_upload_form"))
    
    import os
    temp_path = os.path.join('temp_uploads', filename)
    
    if not os.path.exists(temp_path):
        flash("Upload file not found", "error")
        return redirect(url_for("students_upload_form"))
    
    try:
        # Read Excel file with specified header row
        df = pd.read_excel(temp_path, header=header_row)
        columns = df.columns.tolist()
        
        # Built-in student fields
        builtin_fields = [
            'Student Number', 'student_number', 'STUDENT NUMBER', 'Student_Number',
            'Student Name', 'student_name', 'STUDENT NAME', 'Student_Name',
            'NAME', 'Name', 'name',
            'SURNAME', 'Surname', 'surname',
            'Group Name', 'group_name', 'GROUP NAME', 'Group_Name'
        ]
        
        # Detect which columns are built-in vs custom
        custom_columns = [col for col in columns if col not in builtin_fields]
        
        # Get existing dynamic fields for Student model
        existing_dynamic_fields = DynamicField.query.filter_by(model_name='Student').all()
        existing_field_names = [f.field_name for f in existing_dynamic_fields]
        
        # Helper function to clean preview values
        def clean_preview_value(value):
            """Clean cell value for display, return empty string if invalid"""
            if pd.isna(value):
                return ""
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned.lower() in ['nan', 'none', 'null', '-', 'n/a', 'na']:
                    return ""
                return cleaned
            return value
        
        # Preview first 5 data rows (after header) with cleaned values
        preview_data = []
        for _, row in df.head(5).iterrows():
            cleaned_row = {col: clean_preview_value(row[col]) for col in columns}
            preview_data.append(cleaned_row)
        
        return render_template('upload_students_preview.html',
                             columns=columns,
                             custom_columns=custom_columns,
                             existing_field_names=existing_field_names,
                             preview_data=preview_data,
                             filename=filename,
                             header_row=header_row,
                             total_rows=len(df),
                             intake_group_id=intake_group_id,
                             intake_group_name=intake_group.name)
    except Exception as e:
        flash(f"Error reading Excel file: {str(e)}", "error")
        return redirect(url_for("students_upload_form"))

@app.route("/students/upload_confirm", methods=["POST"])
def upload_students_confirm():
    """Step 2: Create dynamic fields and import data"""
    filename = request.form.get('filename')
    header_row = int(request.form.get('header_row', 0))
    intake_group_id = request.form.get('intake_group_id')
    
    if not filename:
        flash("Upload session expired", "error")
        return redirect(url_for("students_upload_form"))
    
    if not intake_group_id:
        flash("Intake group not specified", "error")
        return redirect(url_for("students_upload_form"))
    
    # Verify intake group exists
    intake_group = Group.query.get(intake_group_id)
    if not intake_group:
        flash("Invalid intake group", "error")
        return redirect(url_for("students_upload_form"))
    
    import os
    temp_path = os.path.join('temp_uploads', filename)
    
    if not os.path.exists(temp_path):
        flash("Upload file not found", "error")
        return redirect(url_for("students_upload_form"))
    
    try:
        # Get selected fields to create as dynamic fields
        selected_fields = request.form.getlist('dynamic_fields')
        field_types = {}
        for field in selected_fields:
            field_types[field] = request.form.get(f'field_type_{field}', 'text')
        
        # Create dynamic fields if they don't exist
        for field_name in selected_fields:
            existing = DynamicField.query.filter_by(model_name='Student', field_name=field_name).first()
            if not existing:
                new_field = DynamicField(
                    model_name='Student',
                    field_name=field_name,
                    field_type=field_types.get(field_name, 'text'),
                    required=False
                )
                db.session.add(new_field)
        db.session.commit()
        
        # Now import the students with specified header row
        df = pd.read_excel(temp_path, header=header_row)
        students_added = 0
        students_updated = 0
        
        # Helper function to clean and validate cell values
        def clean_value(value):
            """Clean cell value and return None if invalid"""
            if pd.isna(value):
                return None
            if isinstance(value, str):
                cleaned = value.strip()
                # Check for common invalid values
                if cleaned.lower() in ['nan', 'none', 'null', '', '-', 'n/a', 'na']:
                    return None
                return cleaned
            return value
        
        for _, row in df.iterrows():
            # Handle built-in fields with multiple possible column names
            student_number = (clean_value(row.get("Student Number")) or 
                            clean_value(row.get("student_number")) or
                            clean_value(row.get("STUDENT NUMBER")) or
                            clean_value(row.get("Student_Number")) or
                            clean_value(row.get("ID NUMBER")) or
                            clean_value(row.get("ID_NUMBER")))
            
            # Try to get student name from different possible columns
            student_name = (clean_value(row.get("Student Name")) or 
                          clean_value(row.get("student_name")) or
                          clean_value(row.get("STUDENT NAME")) or
                          clean_value(row.get("Student_Name")))
            
            # If no combined name, try NAME and SURNAME columns
            if not student_name:
                name_part = clean_value(row.get("NAME")) or clean_value(row.get("Name")) or clean_value(row.get("name"))
                surname_part = clean_value(row.get("SURNAME")) or clean_value(row.get("Surname")) or clean_value(row.get("surname"))
                
                if name_part and surname_part:
                    student_name = f"{name_part} {surname_part}"
                elif name_part:
                    student_name = name_part
                elif surname_part:
                    student_name = surname_part
            
            # Skip rows without valid student name
            if not student_name:
                continue
            
            # ====== CHECK FOR EXISTING STUDENT ======
            existing_student = None
            
            # Try to find by student_number first (most reliable)
            if student_number:
                existing_student = Student.query.filter_by(student_number=str(student_number)).first()
            
            # If not found by number, try by name (fallback)
            if not existing_student:
                existing_student = Student.query.filter_by(student_name=str(student_name)).first()
            
            # If student exists, UPDATE them
            if existing_student:
                # Update basic fields if they have new values
                if student_number and not existing_student.student_number:
                    existing_student.student_number = str(student_number)
                
                # Update group if specified (optional - you can remove this if you don't want to change groups)
                if intake_group.id:
                    existing_student.group_id = intake_group.id
                
                student = existing_student
                students_updated += 1
            else:
                # Create NEW student with the selected intake group
                student = Student(
                    student_number=str(student_number) if student_number else None,
                    student_name=str(student_name),
                    group_id=intake_group.id
                )
                db.session.add(student)
                students_added += 1
            
            db.session.flush()
            
            # Add or UPDATE dynamic field values
            for field_name in selected_fields:
                cleaned_value = clean_value(row.get(field_name))
                if cleaned_value is not None:
                    field_def = DynamicField.query.filter_by(model_name='Student', field_name=field_name).first()
                    if field_def:
                        # Check if this student already has a value for this field
                        existing_field_value = DynamicFieldValue.query.filter_by(
                            field_id=field_def.id,
                            record_id=student.id
                        ).first()
                        
                        if existing_field_value:
                            # UPDATE existing value
                            existing_field_value.value = str(cleaned_value)
                        else:
                            # CREATE new value
                            field_value = DynamicFieldValue(
                                field_id=field_def.id,
                                record_id=student.id,
                                value=str(cleaned_value)
                            )
                            db.session.add(field_value)
        
        db.session.commit()
        
        # Clean up temp file
        os.remove(temp_path)
        
        # Create detailed success message
        message_parts = []
        if students_added > 0:
            message_parts.append(f"{students_added} new student(s) added")
        if students_updated > 0:
            message_parts.append(f"{students_updated} existing student(s) updated")
        
        if message_parts:
            success_message = f"Successfully processed: {' and '.join(message_parts)} to '{intake_group.name}' with {len(selected_fields)} custom field(s)!"
        else:
            success_message = "No students were added or updated."
        
        flash(success_message, "success")
        return redirect(url_for("list_students"))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error importing data: {str(e)}", "error")
        return redirect(url_for("students_upload_form"))
# LECTURERS
##############################################
@app.route("/lecturers")
@require_site_access
def lecturers_page():
    site_id = get_active_site_id()
    lecturers = Lecturer.query.filter_by(site_id=site_id).all()
    return render_template("lecturers.html", lecturers=lecturers)

@app.route("/add_lecturer", methods=["POST"])
@require_site_access
def add_lecturer():
    site_id = get_active_site_id()
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone_number", "").strip()
    email = request.form.get("email", "").strip()
    notes = request.form.get("notes", "").strip()

    lec = Lecturer(name=name, phone_number=phone, email=email, notes=notes, site_id=site_id)
    db.session.add(lec)
    db.session.commit()
    flash("Lecturer added!", "success")
    return redirect(url_for("lecturers_page"))

@app.route("/edit_lecturer/<int:lecturer_id>", methods=["GET", "POST"])
@require_site_access
def edit_lecturer(lecturer_id):
    site_id = get_active_site_id()
    lecturer = Lecturer.query.filter_by(id=lecturer_id, site_id=site_id).first_or_404()
    
    if request.method == "POST":
        lecturer.name = request.form.get("name", "").strip()
        lecturer.phone_number = request.form.get("phone_number", "").strip()
        lecturer.email = request.form.get("email", "").strip()
        lecturer.notes = request.form.get("notes", "").strip()
        db.session.commit()
        flash("Lecturer updated!", "success")
        return redirect(url_for("lecturers_page"))
    return render_template("edit_lecturer.html", lecturer=lecturer)

@app.route("/delete_lecturer/<int:lecturer_id>", methods=["POST"])
@require_site_access
def delete_lecturer(lecturer_id):
    site_id = get_active_site_id()
    lecturer = Lecturer.query.filter_by(id=lecturer_id, site_id=site_id).first_or_404()
    db.session.delete(lecturer)
    db.session.commit()
    flash("Lecturer deleted!", "success")
    return redirect(url_for("lecturers_page"))

##############################################
# MODULES & MINITASKS
##############################################
@app.route("/modules")
@require_site_access
def modules_page():
    site_id = get_active_site_id()
    modules = Module.query.filter_by(site_id=site_id).all()
    mini_tasks = MiniTask.query.all()
    return render_template("modules.html", modules=modules, mini_tasks=mini_tasks)

@app.route("/add_module", methods=["POST"])
@require_site_access
def add_module():
    site_id = get_active_site_id()
    name = request.form["module_name"].strip()
    code = request.form.get("module_code", "").strip()
    category = request.form.get("module_category", "").strip()
    status_type = request.form.get("module_status_type", "P/NYP").strip()
    credits = request.form.get("module_credits", "").strip()
    
    m = Module(
        name=name,
        code=code if code else None,
        category=category if category else None,
        status_type=status_type,
        credits=credits if credits else None,
        site_id=site_id
    )
    db.session.add(m)
    db.session.commit()
    flash("Module added!", "success")
    return redirect(url_for("modules_page"))

@app.route("/edit_module/<int:mod_id>", methods=["GET", "POST"])
@require_site_access
def edit_module(mod_id):
    site_id = get_active_site_id()
    module = Module.query.filter_by(id=mod_id, site_id=site_id).first_or_404()
    
    if request.method == "POST":
        module.name = request.form["module_name"].strip()
        module.code = request.form.get("module_code", "").strip() or None
        module.category = request.form.get("module_category", "").strip() or None
        module.status_type = request.form.get("module_status_type", "P/NYP").strip()
        module.credits = request.form.get("module_credits", "").strip() or None
        db.session.commit()
        flash("Module updated!", "success")
        return redirect(url_for("modules_page"))
    return render_template("edit_module.html", module=module)

@app.route("/delete_module/<int:mod_id>", methods=["POST"])
@require_site_access
def delete_module(mod_id):
    site_id = get_active_site_id()
    mod = Module.query.filter_by(id=mod_id, site_id=site_id).first_or_404()
    db.session.delete(mod)
    db.session.commit()
    flash("Module deleted!", "success")
    return redirect(url_for("modules_page"))

@app.route("/add_mini_task", methods=["POST"])
def add_mini_task():
    module_id = request.form["module_id"]
    title = request.form["title"].strip()
    mt = MiniTask(module_id=module_id, title=title)
    db.session.add(mt)
    db.session.commit()
    flash("Mini-task added!", "success")
    return redirect(url_for("modules_page"))

@app.route("/edit_mini_task/<int:mt_id>", methods=["GET", "POST"])
def edit_mini_task(mt_id):
    mini_task = MiniTask.query.get_or_404(mt_id)
    if request.method == "POST":
        mini_task.title = request.form["title"].strip()
        mini_task.module_id = request.form["module_id"]
        db.session.commit()
        flash("Mini-task updated!", "success")
        return redirect(url_for("modules_page"))
    modules = Module.query.all()
    return render_template("edit_mini_task.html", mini_task=mini_task, modules=modules)

@app.route("/delete_mini_task/<int:mt_id>", methods=["POST"])
def delete_mini_task(mt_id):
    mt = MiniTask.query.get_or_404(mt_id)
    db.session.delete(mt)
    db.session.commit()
    flash("Mini-task deleted!", "success")
    return redirect(url_for("modules_page"))

##############################################
# BULK MODULE ASSIGNMENT
##############################################
@app.route("/assign_modules", methods=["GET", "POST"])
@login_required
def assign_modules_bulk():
    """Assign multiple modules to multiple students"""
    if request.method == "POST":
        student_ids = request.form.getlist("student_ids[]")
        module_ids = request.form.getlist("module_ids[]")
        
        if not student_ids or not module_ids:
            flash("Please select at least one student and one module.", "warning")
            return redirect(url_for("assign_modules_bulk"))
        
        # Assign modules to students
        assignments_made = 0
        for student_id in student_ids:
            student = Student.query.get(int(student_id))
            if student:
                for module_id in module_ids:
                    module = Module.query.get(int(module_id))
                    if module and module not in student.enrolled_modules:
                        student.enrolled_modules.append(module)
                        assignments_made += 1
        
        db.session.commit()
        flash(f"Successfully assigned {len(module_ids)} module(s) to {len(student_ids)} student(s). Total {assignments_made} new assignments made.", "success")
        return redirect(url_for("assign_modules_bulk"))
    
    # GET request - show the form
    students = Student.query.order_by(Student.student_name).all()
    modules = Module.query.order_by(Module.name).all()
    groups = Group.query.all()
    
    return render_template("modules/assign_modules_bulk.html", 
                         students=students, 
                         modules=modules, 
                         groups=groups)

@app.route("/view_module_assignments")
@login_required
def view_module_assignments():
    """View all module assignments"""
    students = Student.query.order_by(Student.student_name).all()
    modules = Module.query.order_by(Module.name).all()
    
    return render_template("modules/view_assignments.html", 
                         students=students, 
                         modules=modules)

@app.route("/remove_module_assignment", methods=["POST"])
@login_required
def remove_module_assignment():
    """Remove a module assignment from a student"""
    student_id = request.form.get("student_id")
    module_id = request.form.get("module_id")
    
    student = Student.query.get_or_404(int(student_id))
    module = Module.query.get_or_404(int(module_id))
    
    if module in student.enrolled_modules:
        student.enrolled_modules.remove(module)
        db.session.commit()
        flash(f"Removed {module.name} from {student.student_name}'s assignments.", "success")
    else:
        flash("Module not assigned to this student.", "warning")
    
    return redirect(url_for("view_module_assignments"))

@app.route("/api/students_by_group/<int:group_id>")
@login_required
def get_students_by_group(group_id):
    """API endpoint to get students by group"""
    students = Student.query.filter_by(group_id=group_id).all()
    return jsonify([{
        'id': s.id,
        'name': s.student_name,
        'student_number': s.student_number
    } for s in students])

@app.route("/api/student_modules/<int:student_id>")
@login_required
def get_student_modules(student_id):
    """API endpoint to get student's enrolled modules"""
    student = Student.query.get_or_404(student_id)
    return jsonify([{
        'id': m.id,
        'name': m.name,
        'code': m.code
    } for m in student.enrolled_modules])

##############################################
# STUDENT -> MINITASK PROGRESS
##############################################
@app.route("/student_module_form/<int:mini_task_id>/<int:student_id>", methods=["GET", "POST"])
def student_module_form(mini_task_id, student_id):
    """Record attempts for a student on a mini-task (using new Pass/Fail system with editable dates)"""
    student = Student.query.get_or_404(student_id)
    mini_task = MiniTask.query.get_or_404(mini_task_id)
    
    # Get existing progress or create new
    progress = StudentMiniTaskProgress.query.filter_by(
        student_id=student_id,
        mini_task_id=mini_task_id
    ).first()
    
    if not progress:
        progress = StudentMiniTaskProgress(
            student_id=student_id,
            mini_task_id=mini_task_id
        )
        db.session.add(progress)
        db.session.flush()
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "add_attempt":
            # Add a new attempt with custom date
            attempt_type = request.form.get("attempt_type")
            result = request.form.get("result")
            notes = request.form.get("attempt_notes", "").strip()
            attempt_date_str = request.form.get("attempt_date", "").strip()
            
            # Parse the date
            attempt_date = datetime.strptime(attempt_date_str, '%Y-%m-%dT%H:%M') if attempt_date_str else datetime.utcnow()
            
            new_attempt = Attempt(
                progress_id=progress.id,
                attempt_type=attempt_type,
                result=result,
                notes=notes,
                attempt_date=attempt_date
            )
            db.session.add(new_attempt)
            db.session.commit()
            flash(f"New {attempt_type} attempt added: {result}!", "success")
            return redirect(url_for("student_module_form", mini_task_id=mini_task_id, student_id=student_id))
        
        elif action == "edit_attempt":
            # Edit an existing attempt (fully editable)
            attempt_id = request.form.get("attempt_id")
            attempt = Attempt.query.get(attempt_id)
            if attempt and attempt.progress_id == progress.id:
                attempt.result = request.form.get("result")
                attempt.notes = request.form.get("notes", "").strip()
                
                # Update date if provided
                attempt_date_str = request.form.get("attempt_date", "").strip()
                if attempt_date_str:
                    attempt.attempt_date = datetime.strptime(attempt_date_str, '%Y-%m-%dT%H:%M')
                
                db.session.commit()
                flash("Attempt updated!", "success")
            return redirect(url_for("student_module_form", mini_task_id=mini_task_id, student_id=student_id))
        
        elif action == "delete_attempt":
            # Delete an attempt
            attempt_id = request.form.get("attempt_id")
            attempt = Attempt.query.get(attempt_id)
            if attempt and attempt.progress_id == progress.id:
                db.session.delete(attempt)
                db.session.commit()
                flash("Attempt deleted!", "success")
            return redirect(url_for("student_module_form", mini_task_id=mini_task_id, student_id=student_id))
        
        else:
            # Update notes
            progress.notes = request.form.get("notes", "").strip()
            db.session.commit()
            flash(f"Notes updated for {student.student_name} on {mini_task.title}!", "success")
            return redirect(url_for("modules_page"))
    
    # Get all attempts grouped by type (using actual assessment types from modules)
    attempts_by_type = {
        'Online': Attempt.query.filter_by(progress_id=progress.id, attempt_type='Online').order_by(Attempt.attempt_date).all(),
        'MT': Attempt.query.filter_by(progress_id=progress.id, attempt_type='MT').order_by(Attempt.attempt_date).all(),
        'MT1': Attempt.query.filter_by(progress_id=progress.id, attempt_type='MT1').order_by(Attempt.attempt_date).all(),
        'MT2': Attempt.query.filter_by(progress_id=progress.id, attempt_type='MT2').order_by(Attempt.attempt_date).all(),
        'IWP': Attempt.query.filter_by(progress_id=progress.id, attempt_type='IWP').order_by(Attempt.attempt_date).all(),
        'CWP': Attempt.query.filter_by(progress_id=progress.id, attempt_type='CWP').order_by(Attempt.attempt_date).all(),
    }
    
    return render_template("student_module_form.html", 
                         student=student, 
                         mini_task=mini_task, 
                         progress=progress,
                         attempts_by_type=attempts_by_type)

##############################################
# SCHEDULE GENERATION
##############################################
@app.route("/generate_schedule", methods=["POST"])
def generate_schedule():
    try:
        session["schedule_form"] = {
            "slot_duration": request.form["slot_duration"],
            "start_date": request.form["start_date"],
            "end_date": request.form["end_date"],
            "start_time": request.form["start_time"],
            "end_time": request.form["end_time"],
            "threshold_mark": request.form["threshold_mark"],
            "auto_extra_time": request.form["auto_extra_time"],
            "scheduling_mode": request.form.get("scheduling_mode", "forward"),
            "priority_rule": request.form.get("priority_rule", "FIFO"),
            "allowance_time": request.form.get("allowance_time", "0"),
            "lunch_start": request.form.get("lunch_start", "12:00"),
            "lunch_duration": request.form.get("lunch_duration", "60")
        }

        base_slot_duration = int(request.form["slot_duration"])
        start_date_obj = datetime.strptime(request.form["start_date"], "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(request.form["end_date"], "%Y-%m-%d").date()
        start_time_obj = datetime.strptime(request.form["start_time"], "%H:%M").time()
        end_time_obj = datetime.strptime(request.form["end_time"], "%H:%M").time()
        lunch_start_obj = datetime.strptime(request.form.get("lunch_start", "12:00"), "%H:%M").time()
        lunch_duration = int(request.form["lunch_duration"])
        threshold_mark = float(request.form.get("threshold_mark", 0))
        auto_extra_time = int(request.form.get("auto_extra_time", 0))
        allowance_time = int(request.form.get("allowance_time", 0))
        priority_rule = request.form.get("priority_rule", "FIFO")

        lunch_start_dt = datetime.combine(start_date_obj, lunch_start_obj)
        lunch_end_dt = lunch_start_dt + timedelta(minutes=lunch_duration)

        current_dt = datetime.combine(start_date_obj, start_time_obj)
        final_dt = datetime.combine(end_date_obj, end_time_obj)

        all_students = Student.query.all()
        orders = []
        for s in all_students:
            # No mark-based extra time anymore, just use base duration
            total_time = base_slot_duration
            orders.append({
                "Student": s.student_name,
                "Group": s.group.name if s.group else "",
                "processing_time": total_time,
                "extra_time": 0
            })

        if priority_rule == "SPT":
            orders.sort(key=lambda x: x["processing_time"])
        elif priority_rule == "LPT":
            orders.sort(key=lambda x: x["processing_time"], reverse=True)

        Schedule.query.delete()
        db.session.commit()

        machines = Machine.query.all()

        while orders and current_dt < final_dt:
            order = orders.pop(0)
            working_day_end = datetime.combine(current_dt.date(), end_time_obj)

            if current_dt >= working_day_end:
                current_dt = datetime.combine(current_dt.date() + timedelta(days=1), start_time_obj)
                continue

            slot_end_dt = current_dt + timedelta(minutes=order["processing_time"])

            if lunch_start_dt <= current_dt < lunch_end_dt or current_dt < lunch_start_dt < slot_end_dt:
                current_dt = lunch_end_dt
                slot_end_dt = current_dt + timedelta(minutes=order["processing_time"])

            if slot_end_dt > working_day_end:
                current_dt = datetime.combine(current_dt.date() + timedelta(days=1), start_time_obj)
                continue

            machine_index = Schedule.query.count() % len(machines) if machines else 0
            machine_name = machines[machine_index].machine_name if machines else "N/A"

            db.session.add(Schedule(
                student_name=order["Student"],
                group_name=order["Group"],
                machine_name=machine_name,
                start_time=current_dt,
                end_time=slot_end_dt,
                extra_time=order["extra_time"]
            ))
            db.session.commit()

            current_dt = slot_end_dt + timedelta(minutes=allowance_time)

        flash("Schedule generated successfully with lunch break!", "success")
    except Exception as e:
        flash(f"Error generating schedule: {e}", "danger")

    return redirect(url_for("index"))

@app.route("/schedule/generate_advanced")
@login_required
@require_site_access
def schedule_generate_advanced_page():
    """Advanced schedule generation page"""
    site_id = get_active_site_id()
    groups = Group.query.filter_by(site_id=site_id).all()
    modules = Module.query.filter_by(site_id=site_id).all()
    machines = Machine.query.filter_by(site_id=site_id).all()
    students = Student.query.filter_by(site_id=site_id).all()
    
    return render_template('schedule/generate_advanced.html',
                         groups=groups,
                         modules=modules,
                         machines=machines,
                         students=students)

@app.route("/generate_schedule_advanced", methods=["POST"])
@login_required
def generate_schedule_advanced():
    """Generate schedule with advanced options"""
    try:
        # Get form parameters
        session_type = request.form.get('session_type', 'practical')
        students_per_session = int(request.form.get('students_per_session', 1))
        slot_duration = int(request.form.get('slot_duration', 60))
        generation_scope = request.form.get('generation_scope', 'all')
        priority_rule = request.form.get('priority_rule', 'FIFO')
        clear_existing = request.form.get('clear_existing') == 'on'
        notes = request.form.get('notes', '')
        
        # Date and time settings
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(request.form['start_time'], '%H:%M').time()
        end_time = datetime.strptime(request.form['end_time'], '%H:%M').time()
        lunch_start = datetime.strptime(request.form.get('lunch_start', '12:00'), '%H:%M').time()
        lunch_duration = int(request.form.get('lunch_duration', 60))
        allowance_time = int(request.form.get('allowance_time', 0))
        
        # Get allowed days of week
        allowed_days = [int(day) for day in request.form.getlist('days[]')]
        if not allowed_days:
            allowed_days = [0, 1, 2, 3, 4]  # Default to weekdays
        
        # Combined filtering - collect all student IDs matching ANY criteria
        all_student_ids = set()
        module_names_for_schedule = []
        
        # Check for specific student selection first (overrides other filters)
        custom_student_ids = request.form.getlist('student_ids')
        if custom_student_ids:
            # Custom selection overrides everything
            all_student_ids.update([int(sid) for sid in custom_student_ids])
        else:
            # Apply group filter
            group_ids = request.form.getlist('group_ids')
            if group_ids:
                group_students = Student.query.filter(Student.group_id.in_(group_ids)).all()
                all_student_ids.update([s.id for s in group_students])
            
            # Apply module filter
            module_ids = request.form.getlist('module_ids')
            if module_ids:
                for module_id in module_ids:
                    module = Module.query.get(module_id)
                    if module:
                        module_names_for_schedule.append(module.name)
                        student_ids = [p.student_id for p in StudentModuleProgress.query.filter_by(module_id=module_id).all()]
                        all_student_ids.update(student_ids)
            
            # If no filters selected, get all students
            if not group_ids and not module_ids:
                all_students = Student.query.all()
                all_student_ids.update([s.id for s in all_students])
        
        # Get student objects
        students = Student.query.filter(Student.id.in_(list(all_student_ids))).all() if all_student_ids else []
        
        if not students:
            flash('No students found matching the criteria.', 'warning')
            return redirect(url_for('schedule_generate_advanced_page'))
        
        # Get machines - use selected machines or all machines
        machine_ids = request.form.getlist('machine_ids')
        if machine_ids:
            machines = Machine.query.filter(Machine.id.in_(machine_ids)).all()
        else:
            machines = Machine.query.all()
        
        if not machines:
            flash('No machines available for scheduling.', 'danger')
            return redirect(url_for('schedule_generate_advanced_page'))
        
        # Clear existing schedule if requested
        if clear_existing:
            Schedule.query.delete()
            db.session.commit()
        
        # Prepare student orders
        orders = []
        module_name_combined = ', '.join(module_names_for_schedule) if module_names_for_schedule else None
        for student in students:
            orders.append({
                'student': student,
                'processing_time': slot_duration,
                'module_name': module_name_combined
            })
        
        # Apply priority sorting
        if priority_rule == 'SPT':
            orders.sort(key=lambda x: x['processing_time'])
        elif priority_rule == 'LPT':
            orders.sort(key=lambda x: x['processing_time'], reverse=True)
        elif priority_rule == 'GROUP':
            orders.sort(key=lambda x: x['student'].group.name if x['student'].group else 'ZZZ')
        elif priority_rule == 'MODULE':
            orders.sort(key=lambda x: x['module_name'] or 'ZZZ')
        
        # Calculate lunch times
        lunch_start_dt = datetime.combine(start_date, lunch_start)
        lunch_end_dt = lunch_start_dt + timedelta(minutes=lunch_duration)
        
        # Schedule generation logic
        current_dt = datetime.combine(start_date, start_time)
        final_dt = datetime.combine(end_date, end_time)
        machine_index = 0
        scheduled_count = 0
        
        # For tests with multiple students per session
        if session_type in ['practical_test', 'written_test'] and students_per_session > 1:
            # Batch students together
            batches = [orders[i:i + students_per_session] for i in range(0, len(orders), students_per_session)]
            
            for batch in batches:
                if current_dt >= final_dt:
                    break
                
                # Skip to next allowed day if needed
                while current_dt.weekday() not in allowed_days:
                    current_dt = datetime.combine(current_dt.date() + timedelta(days=1), start_time)
                    if current_dt >= final_dt:
                        break
                
                if current_dt >= final_dt:
                    break
                
                working_day_end = datetime.combine(current_dt.date(), end_time)
                
                # Update lunch times for current day
                lunch_start_today = datetime.combine(current_dt.date(), lunch_start)
                lunch_end_today = lunch_start_today + timedelta(minutes=lunch_duration)
                
                # Skip lunch break
                if lunch_start_today <= current_dt < lunch_end_today:
                    current_dt = lunch_end_today
                
                slot_end_dt = current_dt + timedelta(minutes=slot_duration)
                
                # Handle lunch overlap
                if current_dt < lunch_start_today < slot_end_dt:
                    current_dt = lunch_end_today
                    slot_end_dt = current_dt + timedelta(minutes=slot_duration)
                
                # Move to next day if session doesn't fit
                if slot_end_dt > working_day_end:
                    current_dt = datetime.combine(current_dt.date() + timedelta(days=1), start_time)
                    continue
                
                # Assign machine
                machine = machines[machine_index % len(machines)]
                
                # Create schedule entries for all students in batch
                for order in batch:
                    student = order['student']
                    schedule_entry = Schedule(
                        student_name=student.student_name,
                        group_name=student.group.name if student.group else '',
                        machine_name=machine.machine_name,
                        module_name=order['module_name'],
                        start_time=current_dt,
                        end_time=slot_end_dt,
                        session_type=session_type,
                        capacity=students_per_session,
                        notes=notes
                    )
                    db.session.add(schedule_entry)
                    scheduled_count += 1
                
                db.session.commit()
                
                # Move to next time slot
                current_dt = slot_end_dt + timedelta(minutes=allowance_time)
                if not request.form.get('same_machine_for_test'):
                    machine_index += 1
        
        else:
            # Individual scheduling (one student per session)
            for order in orders:
                if current_dt >= final_dt:
                    break
                
                # Skip to next allowed day if needed
                while current_dt.weekday() not in allowed_days:
                    current_dt = datetime.combine(current_dt.date() + timedelta(days=1), start_time)
                    if current_dt >= final_dt:
                        break
                
                if current_dt >= final_dt:
                    break
                
                working_day_end = datetime.combine(current_dt.date(), end_time)
                
                # Update lunch times for current day
                lunch_start_today = datetime.combine(current_dt.date(), lunch_start)
                lunch_end_today = lunch_start_today + timedelta(minutes=lunch_duration)
                
                # Skip lunch break
                if lunch_start_today <= current_dt < lunch_end_today:
                    current_dt = lunch_end_today
                
                slot_end_dt = current_dt + timedelta(minutes=order['processing_time'])
                
                # Handle lunch overlap
                if current_dt < lunch_start_today < slot_end_dt:
                    current_dt = lunch_end_today
                    slot_end_dt = current_dt + timedelta(minutes=order['processing_time'])
                
                # Move to next day if session doesn't fit
                if slot_end_dt > working_day_end:
                    current_dt = datetime.combine(current_dt.date() + timedelta(days=1), start_time)
                    continue
                
                # Assign machine
                machine = machines[machine_index % len(machines)]
                student = order['student']
                
                schedule_entry = Schedule(
                    student_name=student.student_name,
                    group_name=student.group.name if student.group else '',
                    machine_name=machine.machine_name,
                    module_name=order['module_name'],
                    start_time=current_dt,
                    end_time=slot_end_dt,
                    session_type=session_type,
                    capacity=1,
                    notes=notes
                )
                db.session.add(schedule_entry)
                scheduled_count += 1
                
                db.session.commit()
                
                # Move to next time slot and machine
                current_dt = slot_end_dt + timedelta(minutes=allowance_time)
                machine_index += 1
        
        flash(f'Schedule generated successfully! {scheduled_count} session(s) created.', 'success')
        return redirect(url_for('view_schedule'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error generating schedule: {str(e)}', 'danger')
        return redirect(url_for('schedule_generate_advanced_page'))

##############################################
# MANUAL SCHEDULING
##############################################
@app.route('/manual_add_schedule', methods=['POST'])
def manual_add_schedule():
    try:
        selected_students = request.form.getlist('students')
        selected_groups = request.form.getlist('groups')
        selected_machines = request.form.getlist('machines')
        date = request.form['date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")

        if not selected_students and not selected_groups:
            flash("Please select at least one student or group.", "danger")
            return redirect(url_for('index'))

        all_students = list(selected_students)
        for group_name in selected_groups:
            group_students = Student.query.filter(Student.group.has(name=group_name)).all()
            all_students.extend([s.student_name for s in group_students])
        all_students = list(set(all_students))

        conflict_log = []
        added_count = 0

        for machine in selected_machines:
            for student_name in all_students:
                conflict = Schedule.query.filter(
                    Schedule.student_name == student_name,
                    Schedule.machine_name == machine,
                    Schedule.start_time < end_dt,
                    Schedule.end_time > start_dt
                ).first()

                if conflict:
                    conflict_log.append(f"{student_name} → {machine} @ {start_time}-{end_time}")
                    continue

                db.session.add(Schedule(
                    student_name=student_name,
                    machine_name=machine,
                    start_time=start_dt,
                    end_time=end_dt
                ))
                added_count += 1

        db.session.commit()

        if added_count:
            flash(f"✅ {added_count} entries added.", "success")
        if conflict_log:
            summary = "<br>".join(conflict_log[:10])
            if len(conflict_log) > 10:
                summary += f"<br>...and {len(conflict_log)-10} more"
            flash(f"⚠️ {len(conflict_log)} conflicts avoided:<br>{summary}", "warning")

    except Exception as e:
        db.session.rollback()
        flash(f"Error adding schedule: {e}", "danger")

    return redirect(url_for("index"))

##############################################
# GROUPS
##############################################
@app.route("/groups")
@require_site_access
def groups_list():
    site_id = get_active_site_id()
    # Admins see all sites, regular users see only their site
    groups = apply_site_filter(Group.query, Group).all()
    return render_template("groups/list.html", groups=groups)

@app.route("/groups/add", methods=["GET", "POST"])
@require_site_access
def groups_add():
    site_id = get_active_site_id()
    
    if request.method == "POST":
        name = request.form["name"].strip()
        selected_site_id = request.form.get("site_id")
        province = request.form.get("province", "").strip()
        date_added_str = request.form.get("date_added")
        
        # Parse date if provided
        date_added = None
        if date_added_str:
            try:
                date_added = datetime.strptime(date_added_str, '%Y-%m-%d')
            except ValueError:
                date_added = datetime.utcnow()
        else:
            date_added = datetime.utcnow()
        
        new_group = Group(
            name=name, 
            site_id=selected_site_id if selected_site_id else site_id,
            province=province,
            date_added=date_added
        )
        db.session.add(new_group)
        db.session.commit()
        flash("Group added successfully!", "success")
        return redirect(url_for("groups_list"))
    
    # Get all sites for the dropdown
    sites = Site.query.filter_by(is_active=True).order_by(Site.name).all()
    return render_template("groups/add.html", sites=sites)

@app.route("/groups/edit/<int:group_id>", methods=["GET", "POST"])
@require_site_access
def groups_edit(group_id):
    site_id = get_active_site_id()
    group = Group.query.filter_by(id=group_id, site_id=site_id).first_or_404()
    
    if request.method == "POST":
        group.name = request.form["name"].strip()
        group.site_id = request.form.get("site_id")
        group.province = request.form.get("province", "").strip()
        
        # Parse date if provided
        date_added_str = request.form.get("date_added")
        if date_added_str:
            try:
                group.date_added = datetime.strptime(date_added_str, '%Y-%m-%d')
            except ValueError:
                pass  # Keep existing date if format is invalid
        
        db.session.commit()
        flash("Group updated successfully!", "success")
        return redirect(url_for("groups_list"))
    
    # Get all sites for the dropdown
    sites = Site.query.filter_by(is_active=True).order_by(Site.name).all()
    return render_template("groups/edit.html", group=group, sites=sites)

@app.route("/groups/delete/<int:group_id>", methods=["POST"])
@require_site_access
def groups_delete(group_id):
    site_id = get_active_site_id()
    group = Group.query.filter_by(id=group_id, site_id=site_id).first_or_404()
    db.session.delete(group)
    db.session.commit()
    flash("Group deleted successfully!", "success")
    return redirect(url_for("groups_list"))

##############################################
# VIEW SCHEDULE & INVENTORY
##############################################
@app.route("/view_schedule")
@require_site_access
def view_schedule():
    site_id = get_active_site_id()
    schedules = Schedule.query.filter_by(site_id=site_id).all()
    students = {s.student_name: s for s in Student.query.filter_by(site_id=site_id).all()}
    inventory = Inventory.query.filter_by(site_id=site_id).all()
    mini_tasks = {m.id: m for m in MiniTask.query.all()}
    progress_by_student = {
        p.student_id: p for p in StudentMiniTaskProgress.query.order_by(StudentMiniTaskProgress.id.desc()).all()
    }

    schedule_data = []
    for slot in schedules:
        student = students.get(slot.student_name)
        if not student:
            continue
        progress = progress_by_student.get(student.id)
        mini_task_id = progress.mini_task_id if progress else None
        mini_task_title = mini_tasks[mini_task_id].title if mini_task_id in mini_tasks else None

        schedule_data.append({
            "id": slot.id,
            "Machine": slot.machine_name,
            "Student": slot.student_name,
            "Group": student.group.name if student.group else None,
            "Start Time": slot.start_time.strftime("%Y-%m-%d %H:%M"),
            "End Time": slot.end_time.strftime("%Y-%m-%d %H:%M"),
            "student_id": student.id,
            "mini_task_id": mini_task_id,
            "MiniTask": mini_task_title
        })

    return render_template("view_schedule.html", schedule_data=schedule_data, inventory=inventory)

@app.route("/inventory/assign_modal", methods=["POST"])
def assign_inventory_modal():
    student_id = request.form["student_id"]
    mini_task_id = request.form["mini_task_id"]
    inventory_id = request.form["inventory_id"]
    quantity = int(request.form["quantity"])

    student = Student.query.get_or_404(student_id)
    task = StudentMiniTaskProgress.query.filter_by(student_id=student_id, mini_task_id=mini_task_id).first()
    item = Inventory.query.get_or_404(inventory_id)

    if not task:
        flash("Mini-task progress not found.", "danger")
        return redirect(url_for("view_schedule"))

    usage = InventoryUsage(
        consumable=item.item_name,
        student_name=student.student_name,
        quantity=quantity,
        unit_cost=item.cost_per_unit,
        student_task_id=task.id
    )
    item.quantity -= quantity
    db.session.add(usage)
    db.session.commit()
    flash("Inventory assigned.", "success")
    return redirect(url_for("view_schedule"))

##############################################
# CALENDAR VIEW + API
##############################################
@app.route("/schedule/calendar")
@require_site_access
def schedule_calendar():
    site_id = get_active_site_id()
    schedules = Schedule.query.filter_by(site_id=site_id).all()
    machines = Machine.query.filter_by(site_id=site_id).all()
    groups = Group.query.filter_by(site_id=site_id).all()
    students = {s.student_name: s for s in Student.query.filter_by(site_id=site_id).all()}
    mini_tasks = {m.id: m for m in MiniTask.query.all()}
    progress_map = {
        p.student_id: p for p in StudentMiniTaskProgress.query.order_by(StudentMiniTaskProgress.id.desc()).all()
    }

    events = []
    for slot in schedules:
        student = students.get(slot.student_name)
        if not student:
            continue
        progress = progress_map.get(student.id)
        mini_task_id = progress.mini_task_id if progress else None
        mini_task_title = mini_tasks[mini_task_id].title if mini_task_id else "—"

        events.append({
            "id": slot.id,
            "title": student.student_name,
            "start": slot.start_time.isoformat(),
            "end": slot.end_time.isoformat(),
            "extendedProps": {
                "student_id": student.id,
                "mini_task_id": mini_task_id,
                "mini_task_title": mini_task_title,
                "group": student.group.name if student.group else "N/A",
                "machine": slot.machine_name,
                "timeslot": f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}"
            }
        })

    inventory = Inventory.query.filter_by(site_id=site_id).all()
    return render_template("calender.html", schedule_events=events, machines=machines, groups=groups, inventory=inventory)

@app.route("/update_schedule/<int:schedule_id>", methods=["POST"])
def update_schedule(schedule_id):
    try:
        sched = Schedule.query.get_or_404(schedule_id)
        sched.student_name = request.form.get("student_name", sched.student_name)
        sched.machine_name = request.form.get("machine_name", sched.machine_name)
        sched.start_time = datetime.strptime(request.form.get("start_time"), "%Y-%m-%dT%H:%M")
        sched.end_time = datetime.strptime(request.form.get("end_time"), "%Y-%m-%dT%H:%M")

        conflict = Schedule.query.filter(
            Schedule.id != schedule_id,
            Schedule.student_name == sched.student_name,
            Schedule.machine_name == sched.machine_name,
            Schedule.start_time < sched.end_time,
            Schedule.end_time > sched.start_time
        ).first()

        if conflict:
            return jsonify({"status": "error", "message": "Conflict with another slot."}), 409

        db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/assign_inventory_from_calendar", methods=["POST"])
def assign_inventory_from_calendar():
    student_name = request.form["student_name"]
    mini_task_id = request.form["mini_task_id"]
    inventory_id = request.form["inventory_id"]
    quantity = int(request.form["quantity"])

    student = Student.query.filter_by(student_name=student_name).first()
    item = Inventory.query.get(inventory_id)
    task = StudentMiniTaskProgress.query.filter_by(student_id=student.id, mini_task_id=mini_task_id).first()

    if not all([student, item, task]):
        return jsonify({"status": "error", "message": "Missing student/task/item"}), 400

    usage = InventoryUsage(
        consumable=item.item_name,
        student_name=student.student_name,
        quantity=quantity,
        unit_cost=item.cost_per_unit,
        student_task_id=task.id
    )
    item.quantity -= quantity
    db.session.add(usage)
    db.session.commit()

    return jsonify({"status": "success"})

##############################################
# DAY VIEW
##############################################
@app.route("/schedule/day/<date>")
@require_site_access
def schedule_day_view(date):
    """Display hourly slots for a specific day"""
    site_id = get_active_site_id()
    
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except:
        flash("Invalid date format", "danger")
        return redirect(url_for("schedule_calendar"))
    
    # Get all schedules for this day (site-specific)
    start_of_day = datetime.combine(date_obj, datetime.min.time())
    end_of_day = datetime.combine(date_obj, datetime.max.time())
    
    schedules = Schedule.query.filter(
        Schedule.site_id == site_id,
        Schedule.start_time >= start_of_day,
        Schedule.start_time <= end_of_day
    ).all()
    
    # Get all students and machines for dropdowns (site-specific)
    students = Student.query.filter_by(site_id=site_id).order_by(Student.student_name).all()
    machines = Machine.query.filter_by(site_id=site_id).order_by(Machine.machine_name).all()
    groups = Group.query.filter_by(site_id=site_id).order_by(Group.name).all()
    
    # Create hourly slots from 7 AM to 6 PM
    hours = list(range(7, 19))  # 7 AM to 6 PM
    
    # Map schedules to their time slots
    schedule_map = {}
    for sched in schedules:
        hour = sched.start_time.hour
        if hour not in schedule_map:
            schedule_map[hour] = []
        schedule_map[hour].append(sched)
    
    return render_template(
        "day_view.html",
        date=date,
        date_obj=date_obj,
        hours=hours,
        schedule_map=schedule_map,
        students=students,
        machines=machines,
        groups=groups,
        timedelta=timedelta
    )

@app.route("/schedule/slot/add", methods=["POST"])
def add_schedule_slot():
    """Add a new schedule slot"""
    try:
        student_name = request.form.get("student_name")
        machine_name = request.form.get("machine_name")
        start_time_str = request.form.get("start_time")
        end_time_str = request.form.get("end_time")
        
        start_time = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M")
        end_time = datetime.strptime(end_time_str, "%Y-%m-%dT%H:%M")
        
        # Get student's group
        student = Student.query.filter_by(student_name=student_name).first()
        group_name = student.group.name if student and student.group else ""
        
        # Check for conflicts
        conflict = Schedule.query.filter(
            Schedule.student_name == student_name,
            Schedule.machine_name == machine_name,
            Schedule.start_time < end_time,
            Schedule.end_time > start_time
        ).first()
        
        if conflict:
            return jsonify({"status": "error", "message": "Time slot conflict detected"}), 409
        
        new_slot = Schedule(
            student_name=student_name,
            group_name=group_name,
            machine_name=machine_name,
            start_time=start_time,
            end_time=end_time
        )
        
        db.session.add(new_slot)
        db.session.commit()
        
        return jsonify({"status": "success", "message": "Slot added successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/schedule/slot/edit/<int:slot_id>", methods=["GET", "POST"])
def edit_schedule_slot(slot_id):
    """Edit an existing schedule slot"""
    slot = Schedule.query.get_or_404(slot_id)
    
    if request.method == "POST":
        try:
            slot.student_name = request.form.get("student_name", slot.student_name)
            slot.machine_name = request.form.get("machine_name", slot.machine_name)
            
            start_time_str = request.form.get("start_time")
            end_time_str = request.form.get("end_time")
            
            if start_time_str:
                slot.start_time = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M")
            if end_time_str:
                slot.end_time = datetime.strptime(end_time_str, "%Y-%m-%dT%H:%M")
            
            # Update group name
            student = Student.query.filter_by(student_name=slot.student_name).first()
            if student and student.group:
                slot.group_name = student.group.name
            
            # Check for conflicts
            conflict = Schedule.query.filter(
                Schedule.id != slot_id,
                Schedule.student_name == slot.student_name,
                Schedule.machine_name == slot.machine_name,
                Schedule.start_time < slot.end_time,
                Schedule.end_time > slot.start_time
            ).first()
            
            if conflict:
                return jsonify({"status": "error", "message": "Time slot conflict detected"}), 409
            
            db.session.commit()
            return jsonify({"status": "success", "message": "Slot updated successfully"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"status": "error", "message": str(e)}), 500
    
    # GET request - return slot data as JSON
    return jsonify({
        "id": slot.id,
        "student_name": slot.student_name,
        "machine_name": slot.machine_name,
        "start_time": slot.start_time.strftime("%Y-%m-%dT%H:%M"),
        "end_time": slot.end_time.strftime("%Y-%m-%dT%H:%M"),
        "group_name": slot.group_name
    })

@app.route("/schedule/slot/delete/<int:slot_id>", methods=["POST"])
def delete_schedule_slot(slot_id):
    """Delete a schedule slot"""
    try:
        slot = Schedule.query.get_or_404(slot_id)
        db.session.delete(slot)
        db.session.commit()
        return jsonify({"status": "success", "message": "Slot deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


##############################################
# VERIFICATION PAGE
##############################################
@app.route("/verify_features")
@login_required
def verify_features():
    """Page to verify all new features are working"""
    return render_template("verify_features.html")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)


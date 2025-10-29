# models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# SITE/FACILITY - Multi-tenancy support
class Site(db.Model):
    __tablename__ = "sites"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    code = db.Column(db.String(50), unique=True)  # Short code like "JHB", "CPT"
    location = db.Column(db.String(255))
    address = db.Column(db.Text)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    groups = db.relationship("Group", backref="site", lazy=True, cascade="all, delete-orphan")
    students = db.relationship("Student", backref="site", lazy=True, cascade="all, delete-orphan")
    lecturers = db.relationship("Lecturer", backref="site", lazy=True, cascade="all, delete-orphan")
    machines = db.relationship("Machine", backref="site", lazy=True, cascade="all, delete-orphan")
    modules = db.relationship("Module", backref="site", lazy=True, cascade="all, delete-orphan")
    inventory = db.relationship("Inventory", backref="site", lazy=True, cascade="all, delete-orphan")
    schedules = db.relationship("Schedule", backref="site", lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Site {self.code} - {self.name}>"

# Student-Module Enrollment Association Table
student_module_enrollment = db.Table('student_module_enrollment',
    db.Column('student_id', db.Integer, db.ForeignKey('students.id'), primary_key=True),
    db.Column('module_id', db.Integer, db.ForeignKey('modules.id'), primary_key=True),
    db.Column('enrolled_date', db.DateTime, default=datetime.utcnow),
    db.Column('status', db.String(50), default='Active')  # Active, Completed, Dropped
)

# GROUPS
class Group(db.Model):
    __tablename__ = "groups"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'), nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    province = db.Column(db.String(100))

    # Relationship to Student
    students = db.relationship("Student", backref="group", lazy=True)

    def __repr__(self):
        return f"<Group {self.id} - {self.name}>"

# LECTURERS
class Lecturer(db.Model):
    __tablename__ = "lecturers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'), nullable=True)
    phone_number = db.Column(db.String(50))
    email = db.Column(db.String(255))
    notes = db.Column(db.Text)

    def __repr__(self):
        return f"<Lecturer {self.id} - {self.name}>"

# STUDENTS
class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(50))  # e.g., AGP24101
    student_name = db.Column(db.String(255), nullable=False)  # e.g., Xander
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'), nullable=True)

    # Relationship to Group
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"))

    # Relationship to StudentMiniTaskProgress
    progress = db.relationship("StudentMiniTaskProgress", backref="student", lazy=True)
    
    # Many-to-many relationship with modules
    enrolled_modules = db.relationship("Module", secondary=student_module_enrollment, backref="enrolled_students")

    def __repr__(self):
        return f"<Student {self.id} - {self.student_number} {self.student_name}>"

# MACHINES
class Machine(db.Model):
    __tablename__ = "machines"
    id = db.Column(db.Integer, primary_key=True)
    machine_name = db.Column(db.String(255), nullable=False)
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'), nullable=True)
    level = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<Machine {self.id} - {self.machine_name}>"

# MODULES
class Module(db.Model):
    __tablename__ = "modules"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'), nullable=True)
    code = db.Column(db.String(100))  # Module code (e.g., 652201-000-01-00-KM-01)
    category = db.Column(db.String(100))  # FUNDAMENTALS, TOOLING U, THEORY MODULES, PRACTICAL MODULES
    status_type = db.Column(db.String(20))  # P/NYP or C/NYC
    credits = db.Column(db.String(20))  # e.g., "75%", "60%"

    # Relationship to MiniTask with cascade delete
    mini_tasks = db.relationship("MiniTask", backref="module", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Module {self.id} - {self.name}>"

# MINITASK
class MiniTask(db.Model):
    __tablename__ = "mini_tasks"
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey("modules.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)

    # Relationship to StudentMiniTaskProgress
    progress_records = db.relationship("StudentMiniTaskProgress", backref="mini_task", lazy=True)

    def __repr__(self):
        return f"<MiniTask {self.id} - {self.title}>"

# STUDENT MINITASK PROGRESS
class StudentMiniTaskProgress(db.Model):
    """
    Here we store attempts, integrated work piece attempts, credential WP attempts,
    online exam attempts, plus a free-text notes field.
    """
    __tablename__ = "student_mini_task_progress"
    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    mini_task_id = db.Column(db.Integer, db.ForeignKey("mini_tasks.id"), nullable=False)

    # Up to 3 attempts
    attempt_1 = db.Column(db.String(255))
    attempt_2 = db.Column(db.String(255))
    attempt_3 = db.Column(db.String(255))

    # Integrated Work Piece (IWP) attempts
    iwp_1 = db.Column(db.String(255))
    iwp_2 = db.Column(db.String(255))
    iwp_3 = db.Column(db.String(255))

    # Credential Work Piece (CWP) attempts
    cwp_1 = db.Column(db.String(255))
    cwp_2 = db.Column(db.String(255))
    cwp_3 = db.Column(db.String(255))

    # Online exams attempts
    oe_1 = db.Column(db.String(255))
    oe_2 = db.Column(db.String(255))
    oe_3 = db.Column(db.String(255))

    notes = db.Column(db.Text)

    # Relationship to ErrorLog and new Attempts
    error_logs = db.relationship("ErrorLog", backref="student_minitask", lazy=True)
    attempts = db.relationship("Attempt", backref="progress", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<StudentMiniTaskProgress ID={self.id} Student={self.student_id} Task={self.mini_task_id}>"

# NEW: Unlimited attempts for each attempt type
class Attempt(db.Model):
    """Store unlimited attempts for different assessment types (editable)"""
    __tablename__ = "attempts"
    id = db.Column(db.Integer, primary_key=True)
    
    progress_id = db.Column(db.Integer, db.ForeignKey("student_mini_task_progress.id"), nullable=False)
    
    # Type: 'Online', 'MT', 'MT1', 'MT2', 'IWP', 'CWP', 'regular', 'iwp', 'cwp', 'oe'
    attempt_type = db.Column(db.String(50), nullable=False)
    
    # Result: 'Pass' or 'Fail' (or 'Not Yet Passed', 'Complete', 'Not Yet Complete')
    result = db.Column(db.String(50), nullable=False)
    
    # Date of attempt (editable - can be set to any date, not restricted to schedule)
    attempt_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Last updated timestamp
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Optional notes for this attempt
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f"<Attempt {self.id} - {self.attempt_type}: {self.result}>"

# NEW: Student module progress (for modules without mini-tasks)
class StudentModuleProgress(db.Model):
    """Track student progress at module level"""
    __tablename__ = "student_module_progress"
    id = db.Column(db.Integer, primary_key=True)
    
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey("modules.id"), nullable=False)
    
    # Result: Supports both P/NYP and C/NYC status types
    # P/NYP: 'Pass', 'Not Yet Passed', 'In Progress'
    # C/NYC: 'Complete', 'Not Yet Complete', 'In Progress'
    result = db.Column(db.String(50), default='In Progress')
    
    # Completion date (editable)
    completion_date = db.Column(db.DateTime)
    
    # Last updated date
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Notes
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f"<StudentModuleProgress Student={self.student_id} Module={self.module_id}: {self.result}>"

# ERROR LOG
class ErrorLog(db.Model):
    __tablename__ = "error_logs"
    id = db.Column(db.Integer, primary_key=True)
    student_minitask_id = db.Column(db.Integer, db.ForeignKey("student_mini_task_progress.id"), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    error = db.Column(db.String(255))
    cause = db.Column(db.String(255))
    remedial = db.Column(db.String(255))

    def __repr__(self):
        return f"<ErrorLog ID={self.id} Error={self.error}>"

# INVENTORY
class Inventory(db.Model):
    __tablename__ = "inventory"
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(255), nullable=False)
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    cost_per_unit = db.Column(db.Float, nullable=False)

# INVENTORY USAGE
class InventoryUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    consumable = db.Column(db.String(255))
    student_name = db.Column(db.String(255))
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'), nullable=True)
    quantity = db.Column(db.Integer)
    unit_cost = db.Column(db.Float, default=0.0)
    date_issued = db.Column(db.DateTime, default=datetime.utcnow)

    # Optional: Link to mini-task progress
    student_task_id = db.Column(db.Integer, db.ForeignKey('student_mini_task_progress.id'))
    task = db.relationship('StudentMiniTaskProgress', backref='inventory_usage')


# OVERHEAD COST
class OverheadCost(db.Model):
    __tablename__ = "overhead_cost"
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'), nullable=True)
    cost = db.Column(db.Float, nullable=False)
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow)

# MACHINE MAINTENANCE
class MachineMaintenance(db.Model):
    __tablename__ = "machine_maintenance"
    id = db.Column(db.Integer, primary_key=True)
    machine_name = db.Column(db.String(255), nullable=False)
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'), nullable=True)
    task = db.Column(db.String(255), nullable=False)
    date_performed = db.Column(db.DateTime, default=datetime.utcnow)
    performed_by = db.Column(db.String(255))
    notes = db.Column(db.Text)

# MACRO PLAN
class MacroPlan(db.Model):
    __tablename__ = "macroplan"
    id = db.Column(db.Integer, primary_key=True)
    machine_name = db.Column(db.String(255), nullable=False)
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'), nullable=True)
    date = db.Column(db.Date, nullable=False)
    planned_maintenance = db.Column(db.Float, default=0.0)
    breakdown = db.Column(db.Float, default=0.0)
    installed_capacity = db.Column(db.Float, default=0.0)
    usage = db.Column(db.Float, default=0.0)

# SCHEDULE
class Schedule(db.Model):
    __tablename__ = "schedule"
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(255), nullable=False)
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'), nullable=True)
    group_name = db.Column(db.String(255))
    machine_name = db.Column(db.String(255))
    module_name = db.Column(db.String(255))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    extra_time = db.Column(db.Integer, default=0)
    session_type = db.Column(db.String(50), default='practical')  # practical, practical_test, written_test
    capacity = db.Column(db.Integer, default=1)  # For tests with multiple students
    notes = db.Column(db.Text)



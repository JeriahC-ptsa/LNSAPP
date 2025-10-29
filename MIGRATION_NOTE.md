# Database Migration Required

## New Tables Added

### 1. `attempts` Table
Stores unlimited attempts for mini-tasks with Pass/Fail results.

```sql
CREATE TABLE attempts (
    id INTEGER PRIMARY KEY,
    progress_id INTEGER NOT NULL,
    attempt_type VARCHAR(50) NOT NULL,
    result VARCHAR(50) NOT NULL,
    attempt_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (progress_id) REFERENCES student_mini_task_progress(id)
);
```

### 2. `student_module_progress` Table
Tracks student progress at module level (for modules without mini-tasks).

```sql
CREATE TABLE student_module_progress (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL,
    module_id INTEGER NOT NULL,
    result VARCHAR(50) DEFAULT 'In Progress',
    completion_date DATETIME,
    notes TEXT,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (module_id) REFERENCES modules(id)
);
```

## To Apply Migration

Run the following in your Python console or create a migration script:

```python
from app import app, db
from models import Attempt, StudentModuleProgress

with app.app_context():
    db.create_all()
    print("Tables created successfully!")
```

Or use Flask-Migrate if you have it installed:

```bash
flask db migrate -m "Add attempts and student_module_progress tables"
flask db upgrade
```

## Changes Summary

1. **Mini-Task Attempts**: Now unlimited (not limited to 3)
2. **Result Format**: Pass/Fail dropdowns instead of text boxes
3. **Module-Level Progress**: Can record Pass/Fail for entire modules
4. **Attempt Types**: Regular, IWP, CWP, OE - all with unlimited attempts

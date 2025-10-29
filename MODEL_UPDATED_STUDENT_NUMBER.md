# ✅ Student Model Updated - Separate Student Number Field

## Summary

Successfully updated the Student model to have separate `student_number` and `student_name` fields instead of combining them in a single field. This provides better data structure and cleaner separation of concerns.

## Changes Made

### 1. Database Model

**File:** `models.py`

**Before:**
```python
class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(255), nullable=False)  # Combined: "AGP24101 Xander"
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"))
```

**After:**
```python
class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(50))  # e.g., AGP24101
    student_name = db.Column(db.String(255), nullable=False)  # e.g., Xander
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"))
```

**Key Changes:**
- ✅ Added `student_number` field (optional, String(50))
- ✅ `student_name` now contains only the name
- ✅ Updated `__repr__` to show both fields

### 2. Migration Script

**File:** `migrate_student_number.py` (NEW)

**Purpose:** Automatically migrates existing data by splitting combined names

**Features:**
- Adds `student_number` column to database
- Splits existing `student_name` data on first space
- First part → `student_number`
- Remaining part → `student_name`
- Handles cases with no space (name only)

**Usage:**
```bash
python migrate_student_number.py
```

**Example Migration:**
- Before: `student_name = "AGP24101 Xander"`
- After: `student_number = "AGP24101"`, `student_name = "Xander"`

### 3. Templates Updated

#### **students/list.html**
- Now uses `s.student_number` and `s.student_name` directly
- No more string splitting in template
- Cleaner, more efficient code

**Before:**
```jinja2
{% set parts = s.student_name.split(' ', 1) %}
<span class="badge bg-primary">{{ parts[0] }}</span>
<strong>{{ parts[1] if parts|length > 1 else s.student_name }}</strong>
```

**After:**
```jinja2
{% if s.student_number %}
  <span class="badge bg-primary">{{ s.student_number }}</span>
{% endif %}
<strong>{{ s.student_name }}</strong>
```

#### **students/add.html**
- Added separate input field for student number
- Student number is optional
- Name field is required

**Form Fields:**
```html
<input name="student_number" placeholder="e.g., AGP24101">
<input name="student_name" placeholder="e.g., Xander" required>
```

#### **students/edit.html**
- Added separate input field for student number
- Pre-fills existing values
- Can edit both fields independently

### 4. Backend Routes Updated

#### **students_add()**
```python
student_number = request.form.get("student_number", "").strip() or None
student_name = request.form["student_name"].strip()

new_student = Student(
    student_number=student_number,
    student_name=student_name,
    group_id=group_id if group_id else None
)
```

#### **students_edit()**
```python
student.student_number = request.form.get("student_number", "").strip() or None
student.student_name = request.form["student_name"].strip()
```

#### **upload_students_confirm()**
- Now handles "Student Number" column in Excel imports
- Supports both "Student Number" and "student_number" column names
- Creates students with separate fields

```python
student_number = row.get("Student Number") or row.get("student_number")
student_name = row.get("Student Name") or row.get("student_name")

new_student = Student(
    student_number=str(student_number) if student_number and not pd.isna(student_number) else None,
    student_name=str(student_name),
    group_id=grp.id
)
```

### 5. Excel Import Support

**Supported Column Names:**
- `Student Number` or `student_number` - Optional
- `Student Name` or `student_name` - Required
- `Group Name` or `group_name` - Optional

**Example Excel Format:**

| Student Number | Student Name | Group Name |
|----------------|--------------|------------|
| AGP24101 | Xander | Feb 24 Group 5A |
| AGP24102 | Ayambonga | Feb 24 Group 5A |
| AGP24103 | Hanhani Zwelibanzi | Feb 24 Group 5A |

## Benefits

### **Better Data Structure**
✅ Separate fields for separate data
✅ No string parsing needed
✅ Easier to query and filter
✅ More efficient database operations

### **Flexibility**
✅ Student number is optional
✅ Can have students without numbers
✅ Can search/sort by number or name independently

### **Cleaner Code**
✅ No template-level string splitting
✅ Direct field access
✅ More maintainable

### **Better UX**
✅ Clear separate input fields
✅ Visual distinction (badge for number)
✅ Easy to edit independently

## Migration Path

### For Existing Data:

1. **Run Migration Script:**
   ```bash
   python migrate_student_number.py
   ```

2. **Script Will:**
   - Add `student_number` column
   - Split existing combined names
   - Update all student records
   - Preserve data integrity

3. **Result:**
   - All students with format "NUMBER Name" will be split
   - Students with name only will have NULL student_number
   - No data loss

### For New Data:

1. **Manual Entry:**
   - Use Add/Edit forms with separate fields
   - Student number is optional
   - Name is required

2. **Excel Import:**
   - Use separate columns for number and name
   - Both old format (combined) and new format (separate) supported

## Files Modified

### Models
- `models.py` - Added student_number field

### Migration
- `migrate_student_number.py` - NEW migration script

### Templates
- `templates/students/list.html` - Uses separate fields
- `templates/students/add.html` - Separate input fields
- `templates/students/edit.html` - Separate input fields

### Backend
- `app.py` - Updated add, edit, and upload routes

## Database Schema

```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    student_number VARCHAR(50),      -- NEW: Optional student ID
    student_name VARCHAR(255) NOT NULL,  -- Now contains only name
    group_id INTEGER,
    FOREIGN KEY (group_id) REFERENCES groups(id)
);
```

## Example Data

| id | student_number | student_name | group_id |
|----|----------------|--------------|----------|
| 40 | AGP24101 | Xander | 5 |
| 41 | AGP24102 | Ayambonga | 5 |
| 42 | AGP24103 | Hanhani Zwelibanzi | 5 |
| 43 | NULL | John Doe | 6 |

---

**Date:** October 14, 2025
**Status:** ✅ Complete - Model Updated
**Migration:** Available via migrate_student_number.py
**Backward Compatible:** Yes (student_number is optional)

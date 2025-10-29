# ✅ Excel Upload with Intake Group Selection

## Summary

Successfully updated the Excel upload functionality to require selecting an intake group before uploading students. All students in the uploaded file will be assigned to the selected intake group.

## Changes Made

### 1. Upload Form (upload_students.html)

**Added Intake Group Selection:**
- Dropdown to select intake group (required)
- Shows all available groups
- Clear helper text explaining all students will be assigned to this group
- Info alert explaining that Excel "Group Name" column will be ignored

**Form Fields:**
```html
<select name="intake_group_id" required>
  <option value="">-- Select Intake Group --</option>
  {% for group in groups %}
    <option value="{{ group.id }}">{{ group.name }}</option>
  {% endfor %}
</select>
```

### 2. Backend Routes Updated

#### **students_upload_form()**
- Now fetches and passes all groups to the template
- Groups displayed in dropdown

#### **upload_students_preview()**
- Validates intake_group_id is provided
- Verifies group exists in database
- Passes intake_group_id and intake_group_name to next step

#### **upload_students_analyze()**
- Receives and validates intake_group_id
- Passes through to preview template
- Shows intake group name in file info

#### **upload_students_confirm()**
- Receives intake_group_id
- Validates group exists
- **Assigns ALL students to the selected intake group**
- Ignores any "Group Name" column in Excel file
- Success message includes intake group name

### 3. Templates Updated

#### **upload_students_select_header.html**
- Added hidden field for intake_group_id
- Shows intake group badge in file info

#### **upload_students_preview.html**
- Added hidden field for intake_group_id
- Shows intake group badge in file info

### 4. How It Works Now

**Step 1: Upload Form**
1. User selects Excel file
2. User selects intake group (required)
3. Clicks "Next"

**Step 2: Header Selection**
- Shows Excel preview
- User selects which row contains headers
- **Displays selected intake group**

**Step 3: Column Mapping**
- Shows detected columns
- User selects custom fields to create
- **Displays selected intake group**

**Step 4: Import**
- Creates students with selected intake group
- **Ignores any "Group Name" column in Excel**
- All students assigned to the same intake group
- Success message: "Successfully uploaded X students to 'Group Name' with Y custom fields!"

## Benefits

✅ **Consistent Group Assignment** - All students in one upload go to the same intake group
✅ **No Confusion** - Excel "Group Name" column is ignored
✅ **Clear Visibility** - Intake group shown throughout the upload process
✅ **Validation** - System validates group exists before allowing upload
✅ **Better Organization** - Easy to manage intake cohorts

## Example Usage

### Scenario: Uploading Feb 2024 Intake

1. **Prepare Excel file:**
   - Columns: Student Number, Student Name, Gender, Race, etc.
   - No need for "Group Name" column

2. **Upload:**
   - Select file
   - Select "Feb 24 Group 5A" from dropdown
   - Click Next

3. **Result:**
   - All students assigned to "Feb 24 Group 5A"
   - Custom fields (Gender, Race) created if needed
   - Success message confirms group assignment

## Excel File Format

**Required Columns:**
- `Student Number` or `student_number` (optional)
- `Student Name` or `student_name` (required)

**Optional Custom Columns:**
- Any other columns (Gender, Race, Phone, etc.)

**Note:** `Group Name` column will be **ignored** if present. All students will be assigned to the intake group selected in the upload form.

---

**Date:** October 14, 2025
**Status:** ✅ Complete and Working
**Feature:** Intake group selection required for Excel uploads

# Dynamic Fields Auto-Update & Reports Fix

## Summary
This update implements automatic form updates when tables are modified via custom fields or Excel uploads, and fixes all broken chart/graph functionality on the reports page.

## Changes Implemented

### 1. Student Forms Auto-Update with Dynamic Fields

#### Student Add Form (`templates/students/add.html`)
- **Added**: Dynamic fields section that automatically displays all custom fields added to the Student model
- **Features**:
  - Automatically renders custom fields based on `DynamicField` entries
  - Supports multiple field types: text, textarea, number, date
  - Shows required field indicators
  - Responsive layout with Bootstrap grid

#### Student Add Route (`app.py`)
- **Modified**: `students_add()` function
- **Changes**:
  - Added loading of dynamic fields on GET request
  - Added processing and saving of dynamic field values on POST request
  - Uses `db.session.flush()` to get student ID before saving related dynamic values

#### Student Edit Form (`templates/students/edit.html`)
- **Already had dynamic fields** - No changes needed
- Maintains existing functionality for editing dynamic field values

### 2. Machine Forms Auto-Update with Dynamic Fields

#### Machine Add Form (`templates/machines/add.html`)
- **Completely redesigned** with modern UI
- **Added**: Dynamic fields section
- **Features**:
  - Bootstrap card layout for better organization
  - Automatic rendering of custom machine fields
  - Supports all field types (text, textarea, number, date)
  - Required field validation

#### Machine Add Route (`app.py`)
- **Modified**: `machines_add()` function
- **Changes**:
  - Loads `DynamicField` entries for Machine model
  - Processes and saves dynamic field values
  - Passes dynamic fields to template

#### Machine Edit Form (`templates/machines/edit.html`)
- **Completely redesigned** with modern UI
- **Added**: Dynamic fields section
- **Features**:
  - Pre-populates existing dynamic field values
  - Allows updating custom field data
  - Matches the styling of student edit form

#### Machine Edit Route (`app.py`)
- **Modified**: `machines_edit()` function
- **Changes**:
  - Loads dynamic fields on GET request
  - Retrieves existing dynamic field values
  - Updates or creates dynamic field values on POST request
  - Deletes empty dynamic field values

### 3. Reports Page Fixes

#### Dynamic Fields in Reports (`reports.py`)
- **Modified**: `reports_page()` function
- **Added**:
  - Loading of student dynamic fields
  - Loading of machine dynamic fields
  - Passing both field types to template

#### Fixed Report Functions

##### 1. Group Comparison Report
- **Issue**: Referenced non-existent fields (`completed`, `online_exam_mark`, `integrated_wp_mark`)
- **Fix**: 
  - Now uses actual `StudentMiniTaskProgress` fields (`attempt_1`, `attempt_2`, `attempt_3`)
  - Calculates completion rates instead of marks
  - Added site filtering
  - Updated chart labels to "Completion %" instead of "Marks"

##### 2. Inventory Usage Report
- **Issue**: Referenced non-existent relationships (`usage.inventory`, `usage.student`)
- **Fix**:
  - Now uses actual `InventoryUsage` fields: `consumable`, `student_name`, `quantity`, `date_issued`
  - Added site filtering
  - Removed broken relationship references

##### 3. Lecturer Workload Report
- **Issue**: Referenced non-existent `lecturer_id` in Module model and non-existent `students` relationship
- **Fix**:
  - Simplified to show lecturer contact information
  - Removed module assignment counting (not supported by current schema)
  - Added site filtering
  - Created simple overview chart

##### 4. Demographic Analysis Report
- **Improvements**:
  - Added site filtering
  - Added support for multiple group filtering
  - Dynamic chart titles based on field being analyzed
  - Better field name formatting
  - Added field name to stats

##### 5. Completion Rates Report
- **Added**: Site filtering to ensure multi-site compatibility

##### 6. Contingency Table Report
- **Added**: Site filtering for students, groups, and modules

##### 7. Cross Tabulation Report
- **Added**: Site filtering for accurate data scoping

### 4. How It Works

#### Dynamic Fields Flow
1. **Adding Custom Fields** (via Excel upload or manual):
   - When new columns are detected in Excel, they're automatically added to `DynamicField` table
   - Field type is auto-detected or can be specified

2. **Form Rendering**:
   - Forms query `DynamicField` table for the relevant model (Student or Machine)
   - Template loops through fields and renders appropriate input controls
   - Required fields are marked with asterisks

3. **Data Saving**:
   - Form submission includes dynamic field values with prefix `dynamic_`
   - Backend extracts these values and saves to `DynamicFieldValue` table
   - Links to the parent record via `record_id`

4. **Data Loading**:
   - Edit forms query `DynamicFieldValue` for existing data
   - Values are pre-populated in the form fields

#### Reports Auto-Update
1. **Filter Options**:
   - Reports page loads all available dynamic fields
   - These can be used for filtering and analysis

2. **Dynamic Field Analysis**:
   - Demographic reports automatically include all custom fields
   - Custom field analysis report shows distribution of any custom field
   - Reports adapt to show whatever fields exist in the database

## Files Modified

### Templates
- `templates/students/add.html` - Added dynamic fields section
- `templates/machines/add.html` - Complete redesign with dynamic fields
- `templates/machines/edit.html` - Complete redesign with dynamic fields

### Python Files
- `app.py` - Updated student and machine routes to handle dynamic fields
- `reports.py` - Fixed all broken chart functions and added dynamic field support

## Files Created
- `DYNAMIC_FIELDS_AUTO_UPDATE.md` - This documentation file

## Benefits

### 1. Automatic Form Updates
- **No manual coding needed** when adding new fields
- Excel uploads automatically extend forms
- Custom fields appear immediately in UI

### 2. Data Consistency
- All custom data is properly stored and linked
- Easy to query and report on
- Maintains referential integrity

### 3. Flexibility
- Supports multiple field types
- Works for both Students and Machines
- Can be extended to other models

### 4. Multi-Site Support
- All reports properly filter by site
- No data leakage between sites
- Accurate cross-site reporting

### 5. Fixed Visualizations
- All charts now work correctly
- No more errors from missing fields
- Proper data representation

## Usage Guide

### Adding Custom Fields via Excel

1. **Upload Excel file** with new columns
2. **Select columns** to import as custom fields
3. **Fields are automatically created** in DynamicField table
4. **Forms immediately show** the new fields

### Adding/Editing Records with Custom Fields

1. **Navigate to Add/Edit form**
2. **Fill in standard fields** (name, group, etc.)
3. **Scroll to "Additional Information" section**
4. **Fill in custom fields** as needed
5. **Save** - all data is stored correctly

### Using Custom Fields in Reports

1. **Go to Reports page**
2. **Select report type** (e.g., "Custom Fields Analysis" or "Student Demographics")
3. **Choose filters** if needed
4. **Generate report** - custom fields appear automatically
5. **View charts and tables** with your custom data

## Technical Notes

### Database Schema
- `DynamicField`: Stores field definitions (name, type, model, required, etc.)
- `DynamicFieldValue`: Stores actual values (field_id, record_id, value)

### Field Types Supported
- **text**: Single-line text input
- **textarea**: Multi-line text area
- **number**: Numeric input
- **date**: Date picker

### Naming Convention
- Form fields: `dynamic_{field_name}`
- Example: `dynamic_gender`, `dynamic_population_group`

## Testing Recommendations

1. **Test student creation** with custom fields
2. **Test machine creation** with custom fields
3. **Edit existing records** and verify custom field updates
4. **Upload Excel** with new columns
5. **Generate each report type** and verify charts display
6. **Test multi-site filtering** in reports
7. **Try different chart types** (bar, pie, line) for each report

## Future Enhancements

Potential additions:
- Support for select/dropdown field types
- Conditional field visibility
- Field validation rules
- Bulk edit custom fields
- Import/export custom field definitions
- Custom field templates for common scenarios

## Troubleshooting

### Forms not showing custom fields
- Verify `DynamicField` entries exist in database
- Check `model_name` matches exactly ('Student' or 'Machine')
- Ensure dynamic fields are passed to template

### Custom field values not saving
- Check form field names have `dynamic_` prefix
- Verify `db.session.flush()` is called before saving values
- Check for database permission issues

### Reports showing errors
- Verify site_id is being passed in filters
- Check that referenced fields exist in models
- Review query filters for correct syntax

### Charts not displaying
- Check that data is not empty
- Verify column names match between data and chart code
- Check browser console for JavaScript errors

## Support

For issues or questions:
1. Check this documentation
2. Review the code comments
3. Test with sample data
4. Check database for field definitions

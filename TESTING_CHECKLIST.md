# Testing Checklist - Dynamic Fields & Reports Fix

## Pre-Testing Setup

### Database Check
- [ ] Verify `dynamic_fields` table exists
- [ ] Verify `dynamic_field_values` table exists
- [ ] Check for existing dynamic fields: `SELECT * FROM dynamic_fields;`

### Server Check
- [ ] Start the Flask application
- [ ] Check no startup errors in console
- [ ] Verify all routes load without errors

---

## 1️⃣ Student Forms Testing

### Student Add Form
- [ ] Navigate to `/students/add`
- [ ] Verify form loads without errors
- [ ] Check "Additional Information" section appears if custom fields exist
- [ ] Fill in:
  - [ ] Student Number: `TEST001`
  - [ ] Student Name: `Test Student`
  - [ ] Group: Select any
  - [ ] Any custom fields shown
- [ ] Click "Save Student"
- [ ] Verify success message appears
- [ ] Verify student appears in students list
- [ ] Check database: `SELECT * FROM dynamic_field_values WHERE record_id = (SELECT id FROM students WHERE student_number = 'TEST001');`

### Student Edit Form
- [ ] Navigate to edit form for a student
- [ ] Verify "Additional Information" section appears
- [ ] Verify existing custom field values are pre-populated
- [ ] Change a custom field value
- [ ] Click "Update Student"
- [ ] Verify success message
- [ ] Re-open edit form
- [ ] Verify updated value is shown

---

## 2️⃣ Machine Forms Testing

### Machine Add Form
- [ ] Navigate to `/machines/add`
- [ ] Verify new modern UI with card layout
- [ ] Check "Additional Information" section appears if custom fields exist
- [ ] Fill in:
  - [ ] Machine Name: `Test CNC Machine`
  - [ ] Level: `Advanced`
  - [ ] Any custom fields shown
- [ ] Click "Add Machine"
- [ ] Verify success message appears
- [ ] Verify machine appears in machines list
- [ ] Check database: `SELECT * FROM dynamic_field_values WHERE record_id = (SELECT id FROM machines WHERE machine_name = 'Test CNC Machine');`

### Machine Edit Form
- [ ] Navigate to edit form for a machine
- [ ] Verify new modern UI with card layout
- [ ] Verify "Additional Information" section appears
- [ ] Verify existing custom field values are pre-populated
- [ ] Change a custom field value
- [ ] Click "Update Machine"
- [ ] Verify success message
- [ ] Re-open edit form
- [ ] Verify updated value is shown

---

## 3️⃣ Excel Upload Testing

### Student Excel Upload
- [ ] Create test Excel file with columns:
  - `Student Number`, `Student Name`, `Group`, `Department` (new custom field)
- [ ] Navigate to student upload page
- [ ] Upload the file
- [ ] Select header row
- [ ] Map columns including new `Department` column
- [ ] Select `Department` as a custom field
- [ ] Complete upload
- [ ] Check database: `SELECT * FROM dynamic_fields WHERE model_name = 'Student' AND field_name = 'Department';`
- [ ] Navigate to `/students/add`
- [ ] Verify "Department" field now appears in form

### Machine Excel Upload
- [ ] Create test Excel file with columns:
  - `Machine Name`, `Level`, `Manufacturer` (new custom field)
- [ ] Navigate to machine upload page
- [ ] Upload the file
- [ ] Select header row
- [ ] Map columns including new `Manufacturer` column
- [ ] Select `Manufacturer` as a custom field
- [ ] Complete upload
- [ ] Check database: `SELECT * FROM dynamic_fields WHERE model_name = 'Machine' AND field_name = 'Manufacturer';`
- [ ] Navigate to `/machines/add`
- [ ] Verify "Manufacturer" field now appears in form

---

## 4️⃣ Reports Testing

### Report Page Load
- [ ] Navigate to `/reports`
- [ ] Verify page loads without errors
- [ ] Check all report type cards are visible
- [ ] Verify filter options populate correctly

### Student Performance Report
- [ ] Select "Student Performance Analysis"
- [ ] Choose a group from filters
- [ ] Select chart type: **Bar**
- [ ] Click "Generate Report"
- [ ] Verify:
  - [ ] No errors in browser console
  - [ ] Chart displays correctly
  - [ ] Table shows student data
  - [ ] Statistics show correct count
- [ ] Try chart type: **Pie**
- [ ] Verify pie chart displays

### Group Comparison Report (FIXED)
- [ ] Select "Group Comparison & Analytics"
- [ ] Select chart type: **Bar**
- [ ] Click "Generate Report"
- [ ] Verify:
  - [ ] No errors
  - [ ] Chart shows "Average %" and "Highest %"
  - [ ] Y-axis labeled "Completion Rate (%)"
  - [ ] Table shows group statistics
  - [ ] No references to "Marks" or non-existent fields

### Inventory Usage Report (FIXED)
- [ ] Select "Inventory Usage Statistics"
- [ ] Select chart type: **Bar**
- [ ] Click "Generate Report"
- [ ] Verify:
  - [ ] No errors
  - [ ] Chart displays usage by item
  - [ ] Table shows: Item, Student, Quantity Used, Date
  - [ ] No "Unknown" values if data exists

### Machine Utilization Report
- [ ] Select "Machine Utilization Report"
- [ ] Select chart type: **Bar**
- [ ] Click "Generate Report"
- [ ] Verify:
  - [ ] Chart shows total hours by machine
  - [ ] Table shows booking details
  - [ ] Statistics show total bookings

### Schedule Analysis Report
- [ ] Select "Schedule & Attendance Analysis"
- [ ] Select chart type: **Bar**
- [ ] Click "Generate Report"
- [ ] Verify:
  - [ ] Chart shows schedules by day of week
  - [ ] Table shows schedule details
  - [ ] Busiest day is identified in stats

### Student Progress Report
- [ ] Select "Student Progress Tracking"
- [ ] Select chart type: **Bar**
- [ ] Click "Generate Report"
- [ ] Verify:
  - [ ] Chart shows completion rates per student
  - [ ] Table includes: Student, Group, Tasks, Completion Rate
  - [ ] Average completion rate calculated

### Demographic Analysis Report (FIXED)
- [ ] Select "Student Demographics"
- [ ] Select chart type: **Pie**
- [ ] Click "Generate Report"
- [ ] Verify:
  - [ ] Chart shows distribution of first custom field
  - [ ] Title reflects field name (not generic "Demographic")
  - [ ] Table shows categories and percentages
  - [ ] Stats show field being analyzed
- [ ] Try chart type: **Bar**
- [ ] Verify bar chart displays correctly

### Completion Rates Report (FIXED)
- [ ] Select "Module Completion Rates"
- [ ] Select chart type: **Bar**
- [ ] Click "Generate Report"
- [ ] Verify:
  - [ ] Chart shows average completion by module
  - [ ] Table shows task-level details
  - [ ] No site data leakage (only current site data)

### Attempt Analysis Report
- [ ] Select "Assessment Attempts Analysis"
- [ ] Select chart type: **Pie**
- [ ] Click "Generate Report"
- [ ] Verify:
  - [ ] Pie chart shows pass attempts distribution
  - [ ] Categories: Pass - 1st/2nd/3rd Attempt, Not Passed
  - [ ] Table shows student attempt details

### Inventory Stock Report
- [ ] Select "Inventory Stock Levels"
- [ ] Select chart type: **Bar**
- [ ] Click "Generate Report"
- [ ] Verify:
  - [ ] Chart shows initial vs current stock
  - [ ] Table shows stock status
  - [ ] Stats show low stock items

### Lecturer Workload Report (FIXED)
- [ ] Select "Lecturer Workload Analysis"
- [ ] Select chart type: **Bar**
- [ ] Click "Generate Report"
- [ ] Verify:
  - [ ] No errors (even without module assignments)
  - [ ] Chart displays (simple overview)
  - [ ] Table shows: Lecturer, Phone, Email, Notes
  - [ ] No references to non-existent fields

### Custom Field Analysis Report
- [ ] Select "Custom Fields Analysis"
- [ ] Select chart type: **Pie**
- [ ] Click "Generate Report"
- [ ] Verify:
  - [ ] Chart shows distribution of first custom field
  - [ ] Title includes field name
  - [ ] Table shows values and percentages

### Contingency Table Report (FIXED)
- [ ] Select "Contingency Table Analysis"
- [ ] Select chart type: **Bar** (shows heatmap)
- [ ] Click "Generate Report"
- [ ] Verify:
  - [ ] Heatmap displays correctly
  - [ ] Shows Groups vs Modules
  - [ ] Table includes totals
  - [ ] Only shows current site data

### Cross Tabulation Report (FIXED)
- [ ] Select "Cross-Tabulation Report"
- [ ] Select chart type: **Bar**
- [ ] Click "Generate Report"
- [ ] Verify:
  - [ ] Stacked bar chart displays
  - [ ] Shows module status by group
  - [ ] Table is a proper crosstab
  - [ ] Only shows current site data

---

## 5️⃣ Multi-Site Testing

### Site Switching
- [ ] Switch to Site A
- [ ] Add a student with custom field value "Site A Data"
- [ ] Generate a report
- [ ] Verify only Site A data appears
- [ ] Switch to Site B
- [ ] Generate same report
- [ ] Verify "Site A Data" student does NOT appear
- [ ] Verify only Site B data appears

### Custom Fields Per Site
- [ ] Custom fields are global (shared across sites)
- [ ] Custom field VALUES are site-specific (linked to records)
- [ ] Verify a custom field added in Site A appears in Site B forms
- [ ] Verify values entered in Site A don't show for Site B records

---

## 6️⃣ Edge Cases Testing

### Empty Data
- [ ] Try generating a report with no data
- [ ] Verify graceful message: "No data available"
- [ ] Verify no errors in console
- [ ] Verify page doesn't crash

### No Custom Fields
- [ ] Remove all custom fields: `DELETE FROM dynamic_fields WHERE model_name = 'Student';`
- [ ] Navigate to `/students/add`
- [ ] Verify form still works without "Additional Information" section
- [ ] Add a student successfully
- [ ] Restore custom fields for further testing

### Required Custom Fields
- [ ] Create a required custom field: `UPDATE dynamic_fields SET required = 1 WHERE field_name = 'Department';`
- [ ] Navigate to `/students/add`
- [ ] Try submitting without filling required custom field
- [ ] Verify HTML5 validation prevents submission
- [ ] Fill required field and submit
- [ ] Verify success

### Special Characters in Field Names
- [ ] Add field with underscores: `test_field_name`
- [ ] Verify it displays as "Test Field Name" in forms
- [ ] Enter data and save
- [ ] Verify data saves correctly

---

## 7️⃣ Performance Testing

### Large Dataset
- [ ] Upload Excel with 100+ students
- [ ] Verify upload completes successfully
- [ ] Navigate to student list
- [ ] Verify page loads in reasonable time
- [ ] Generate a report with all students
- [ ] Verify report generates in reasonable time (<10 seconds)

### Multiple Custom Fields
- [ ] Add 10+ custom fields via Excel
- [ ] Navigate to add form
- [ ] Verify all fields display
- [ ] Verify form is still usable (not too cluttered)
- [ ] Fill form and save
- [ ] Verify all values save correctly

---

## 8️⃣ Browser Compatibility

### Test in Different Browsers
- [ ] Chrome
  - [ ] Forms work
  - [ ] Charts display
  - [ ] No console errors
- [ ] Firefox
  - [ ] Forms work
  - [ ] Charts display
  - [ ] No console errors
- [ ] Edge
  - [ ] Forms work
  - [ ] Charts display
  - [ ] No console errors

### Mobile Responsive
- [ ] Test forms on mobile view (Chrome DevTools)
- [ ] Verify forms are responsive
- [ ] Verify custom fields section is readable
- [ ] Test reports on mobile
- [ ] Verify charts are responsive

---

## 9️⃣ Security Testing

### SQL Injection
- [ ] Try entering SQL in custom field: `'; DROP TABLE students; --`
- [ ] Verify data is escaped/sanitized
- [ ] Verify no SQL execution
- [ ] Verify data saves as plain text

### XSS Testing
- [ ] Enter HTML/JavaScript in custom field: `<script>alert('XSS')</script>`
- [ ] Save and view in edit form
- [ ] Verify script doesn't execute
- [ ] Verify HTML is escaped

### Access Control
- [ ] Test with different user roles
- [ ] Verify non-admin can't access certain routes
- [ ] Verify site filtering prevents cross-site access

---

## 🔟 Database Integrity

### Foreign Key Constraints
- [ ] Try deleting a student with custom field values
- [ ] Verify CASCADE deletes related `dynamic_field_values`
- [ ] Or verify deletion is prevented if not CASCADE

### Data Consistency
- [ ] Check no orphaned dynamic_field_values: 
  ```sql
  SELECT * FROM dynamic_field_values dfv
  LEFT JOIN dynamic_fields df ON df.id = dfv.field_id
  WHERE df.id IS NULL;
  ```
- [ ] Should return 0 rows

### Indexes (Optional)
- [ ] Check if indexes exist on foreign keys
- [ ] Monitor query performance
- [ ] Add indexes if needed

---

## ✅ Final Validation

### Code Review
- [ ] Review all modified files
- [ ] Check for any debug print statements
- [ ] Verify no hardcoded values
- [ ] Check error handling is in place

### Documentation Review
- [ ] Read `DYNAMIC_FIELDS_AUTO_UPDATE.md`
- [ ] Read `IMPLEMENTATION_SUMMARY_DYNAMIC_FIELDS.md`
- [ ] Read `QUICK_REFERENCE_DYNAMIC_FIELDS.md`
- [ ] Verify documentation matches implementation

### Deployment Readiness
- [ ] No errors in any forms
- [ ] All reports generate successfully
- [ ] No console errors
- [ ] Database is clean
- [ ] Documentation is complete

---

## 📊 Test Results Summary

| Category | Total Tests | Passed | Failed | Notes |
|----------|-------------|--------|--------|-------|
| Student Forms | | | | |
| Machine Forms | | | | |
| Excel Upload | | | | |
| Reports | | | | |
| Multi-Site | | | | |
| Edge Cases | | | | |
| Performance | | | | |
| Browser Compat | | | | |
| Security | | | | |
| Database | | | | |

---

## 🐛 Issues Found

| Issue # | Description | Severity | Status | Fix |
|---------|-------------|----------|--------|-----|
| 1 | | | | |
| 2 | | | | |

---

## 📝 Notes

_Add any additional observations, recommendations, or issues here_

---

**Testing Date**: _______________  
**Tested By**: _______________  
**Environment**: _______________  
**Result**: ☐ Pass ☐ Fail ☐ Pass with Issues

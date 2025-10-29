# ✅ Excel Upload - NaN Value Handling

## Summary

Updated the Excel upload functionality to properly handle and disregard "nan" values and other invalid/unreadable data during import and preview.

## Problem

When uploading Excel files with empty cells or invalid data, the system was importing literal "nan" strings and displaying them in previews, causing:
- Invalid data in the database
- Confusing preview displays
- Poor data quality

## Solution

Created a `clean_value()` helper function that:
1. Detects pandas NaN values
2. Identifies common invalid string values
3. Returns `None` for invalid data
4. Preserves valid data

## Invalid Values Detected

The system now automatically disregards:
- `nan` (pandas NaN values)
- `"nan"` (string literal)
- `"none"`
- `"null"`
- `""` (empty strings)
- `"-"` (dash placeholders)
- `"n/a"` or `"na"`
- Whitespace-only values

## Changes Made

### 1. Upload Confirmation Route (`upload_students_confirm`)

**Added `clean_value()` function:**
```python
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
```

**Updated student import logic:**
```python
# Clean values before processing
student_number = clean_value(row.get("Student Number")) or clean_value(row.get("student_number"))
student_name = clean_value(row.get("Student Name")) or clean_value(row.get("student_name"))

# Skip rows without valid student name
if not student_name:
    continue

# Only add dynamic field values if they're valid
for field_name in selected_fields:
    cleaned_value = clean_value(row.get(field_name))
    if cleaned_value is not None:
        # Add to database
```

### 2. Preview Route (`upload_students_analyze`)

**Added `clean_preview_value()` function:**
```python
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
```

**Updated preview generation:**
```python
# Clean all preview values before display
preview_data = []
for _, row in df.head(5).iterrows():
    cleaned_row = {col: clean_preview_value(row[col]) for col in columns}
    preview_data.append(cleaned_row)
```

## How It Works

### During Preview:
1. Excel file is read
2. Each cell value is cleaned
3. Invalid values shown as **empty cells** in preview
4. User sees clean, accurate preview

### During Import:
1. Each row is processed
2. Values are cleaned before validation
3. **Rows with no valid student name are skipped**
4. Only valid field values are saved to database
5. Invalid values are **not imported**

## Example Behavior

### Excel File:
```
| Student Number | Student Name | Gender | Phone    |
|----------------|--------------|--------|----------|
| ADKNU18002     | Andile       | F      | 0723360786 |
| nan            | Duma         | nan    | nan      |
| ADKNU18003     | nan          | M      | -        |
```

### Preview Display:
```
| Student Number | Student Name | Gender | Phone      |
|----------------|--------------|--------|------------|
| ADKNU18002     | Andile       | F      | 0723360786 |
|                | Duma         |        |            |
| ADKNU18003     |              | M      |            |
```

### Import Result:
- ✅ **Row 1:** Imported with all fields
- ✅ **Row 2:** Imported (Duma) with no student number, no gender, no phone
- ❌ **Row 3:** **SKIPPED** - No valid student name

## Benefits

✅ **Clean Data** - No "nan" strings in database  
✅ **Better Validation** - Rows without names are skipped  
✅ **Clear Previews** - Empty cells shown as empty, not "nan"  
✅ **Flexible** - Handles multiple invalid value formats  
✅ **Case Insensitive** - Catches "NaN", "nan", "NAN", etc.  
✅ **Whitespace Handling** - Trims and validates properly  

## Testing Recommendations

Test with Excel files containing:
- Empty cells
- "nan" text values
- "N/A" or "n/a" values
- Dash placeholders ("-")
- Whitespace-only cells
- Mixed valid and invalid data

All should be handled gracefully! ✅

---

**Date:** October 14, 2025  
**Status:** ✅ Complete  
**Feature:** Smart NaN and invalid value detection during Excel import

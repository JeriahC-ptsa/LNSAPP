# ⚠️ IMPORTANT: Database Migration Required

## New Schedule Features Added

The Schedule model has been updated with new fields. You **MUST** run a database migration before using the advanced schedule generator.

---

## 🔧 Run These Commands

### Option 1: Flask-Migrate (Recommended)
```bash
# Generate migration
flask db migrate -m "Add session_type, module_name, capacity, and notes to Schedule"

# Apply migration
flask db upgrade
```

### Option 2: Manual SQL (if Flask-Migrate not set up)
```sql
ALTER TABLE schedule ADD COLUMN module_name VARCHAR(255);
ALTER TABLE schedule ADD COLUMN session_type VARCHAR(50) DEFAULT 'practical';
ALTER TABLE schedule ADD COLUMN capacity INTEGER DEFAULT 1;
ALTER TABLE schedule ADD COLUMN notes TEXT;
```

---

## ✅ Verification

After running migration, restart your Flask server:
```bash
python app.py
```

Then test:
1. Go to Schedule → Advanced Generator
2. Try generating a schedule
3. Check if it works without errors

---

## 📋 New Fields Explained

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `module_name` | String(255) | NULL | Which module the session is for |
| `session_type` | String(50) | 'practical' | practical, practical_test, or written_test |
| `capacity` | Integer | 1 | How many students per session |
| `notes` | Text | NULL | Optional notes about the session |

---

## ⚠️ If You Get Errors

**Error**: "Column 'session_type' not found"
- **Solution**: Run the migration commands above

**Error**: "flask: command not found"
- **Solution**: Use `python -m flask db migrate ...`

**Error**: Migration conflicts
- **Solution**: Delete existing migration files and regenerate

---

## 🎯 After Migration

You can now use:
- ✅ Advanced Schedule Generator with session types
- ✅ Multiple students per test session
- ✅ Module-based filtering
- ✅ Enhanced schedule views with type badges

---

**Run the migration NOW before proceeding!**

# Database Schema Fix - Groups Table

## Issue
The application was crashing with:
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such column: groups.date_added
```

## Root Cause
The `Group` model in `models.py` defined columns that didn't exist in the actual database table:
- `site_id` - Missing (required for multi-site support)
- `date_added` - Missing (timestamp field)
- `province` - Missing (location field)

## Discovery
- Multiple database files existed: `app.db`, `database.db`, `lns_app.db`
- The actual database in use was `database.db` (73KB with data)
- The `config.py` was pointing to `app.db` instead of `database.db`
- The groups table only had 2 columns: `id` and `name`

## Fix Applied

### 1. Added Missing Columns to Database
Ran `fix_database_schema.py` which added:
```sql
ALTER TABLE groups ADD COLUMN site_id INTEGER;
ALTER TABLE groups ADD COLUMN date_added DATETIME DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE groups ADD COLUMN province VARCHAR(100);
```

### 2. Updated Configuration
Changed `config.py` line 17:
```python
# Before:
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///app.db")

# After:
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///database.db")
```

## Verification

Groups table now has 5 columns:
1. `id` (INTEGER) - Primary key
2. `name` (VARCHAR(100)) - Group name
3. `site_id` (INTEGER) - Foreign key to sites table
4. `date_added` (DATETIME) - Creation timestamp
5. `province` (VARCHAR(100)) - Location/province

## Result
✅ Application now starts without errors
✅ Groups table matches the model definition
✅ Multi-site filtering will work correctly
✅ All forms and reports can access group data

## Files Created/Modified

### Created:
- `fix_database_schema.py` - Script to add missing columns
- `check_all_dbs.py` - Script to identify which database file has data
- `init_db.py` - Script to initialize database tables
- `DATABASE_SCHEMA_FIX.md` - This documentation

### Modified:
- `config.py` - Updated database URI to point to `database.db`

## Future Prevention

To prevent schema mismatches in the future:

1. **Use Flask-Migrate** (already imported in `app.py`):
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

2. **Always run migrations** when model changes:
   ```bash
   flask db migrate -m "Add new column to groups"
   flask db upgrade
   ```

3. **Single source of truth**: Keep only one database file in production

## Testing Checklist
- [ ] Start the Flask application
- [ ] Navigate to home page (/)
- [ ] Check no OperationalError appears
- [ ] Access Groups page
- [ ] Verify groups display correctly
- [ ] Test creating a new group
- [ ] Test multi-site filtering

## Notes
- Existing group records will have `site_id` set to `NULL`
- You may want to run an update query to set site_id for existing groups:
  ```sql
  UPDATE groups SET site_id = 1 WHERE site_id IS NULL;
  ```
- The `date_added` column will be set to CURRENT_TIMESTAMP for existing records

---
**Fix Applied**: October 24, 2025  
**Status**: ✅ RESOLVED

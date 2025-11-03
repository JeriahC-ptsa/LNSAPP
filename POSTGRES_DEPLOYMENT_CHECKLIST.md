# PostgreSQL Deployment Checklist

## ✅ Pre-Deployment Verification

Your application is **READY** for PostgreSQL deployment!

### Files Present:
- [x] `config.py` - PostgreSQL configuration with auto-detection
- [x] `requirements.txt` - Includes psycopg2-binary==2.9.9 and gunicorn==21.2.0
- [x] `Procfile` - Web server command: `web: gunicorn run:app`
- [x] `runtime.txt` - Python version: python-3.11.0
- [x] `.env.example` - Environment variables template
- [x] `.gitignore` - Protects sensitive files
- [x] `init_database.py` - Database initialization script
- [x] `setup_auth_original_db.py` - Admin user creation script

### Configuration Status:
- [x] Automatic PostgreSQL URL conversion (postgres:// → postgresql://)
- [x] Connection pooling enabled
- [x] SQLite fallback for local development
- [x] Production-ready engine options

## 🚀 Deployment Steps

### Step 1: Choose Your Platform

**Recommended: Render.com (Free tier available)**
- ✅ Free PostgreSQL for 90 days
- ✅ Easy GitHub integration
- ✅ Automatic deployments
- ✅ Free SSL certificates

**Alternatives:**
- Heroku (PostgreSQL $5/month)
- Railway.app ($5/month credit)
- DigitalOcean ($5/month minimum)

### Step 2: Create PostgreSQL Database

#### On Render:
1. Go to https://dashboard.render.com
2. Click "New +" → "PostgreSQL"
3. Settings:
   - Name: `lnsapp-db`
   - Database: `lnsapp`
   - Region: Choose closest
   - Plan: Free
4. Click "Create Database"
5. **Copy the Internal Database URL**

#### On Heroku:
```bash
heroku addons:create heroku-postgresql:mini
```

#### On Railway:
1. Click "New" → "Database" → "PostgreSQL"
2. Database auto-provisions

### Step 3: Deploy Application

#### On Render:
1. Click "New +" → "Web Service"
2. Connect GitHub: `JeriahC-ptsa/LNSAPP`
3. Settings:
   - Name: `lnsapp`
   - Branch: `main`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn run:app`
4. Environment Variables:
   ```
   DATABASE_URL = <paste Internal Database URL>
   SECRET_KEY = <generate random key>
   FLASK_ENV = production
   ```
5. Click "Create Web Service"

#### Generate SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 4: Initialize Database

After deployment completes, open Render Shell and run:

```bash
# Create all tables
python init_database.py

# Create admin user and permissions
python setup_auth_original_db.py

# Sync all permissions to all roles
python sync_all_permissions.py
```

### Step 5: Verify Deployment

Visit your app URL (e.g., `https://lnsapp.onrender.com`)

Test:
- [ ] Login page loads
- [ ] Can login with `admin` / `admin123`
- [ ] Dashboard displays
- [ ] All menu items visible (Machines, Students, etc.)
- [ ] Can create a test student
- [ ] Can view reports
- [ ] Admin panel accessible

### Step 6: Post-Deployment Security

1. **Change admin password immediately**
   - Login as admin
   - Go to user settings
   - Change password from `admin123`

2. **Update SECRET_KEY**
   - Generate new key: `python -c "import secrets; print(secrets.token_hex(32))"`
   - Update in Render environment variables
   - Restart service

3. **Create additional users**
   - Admin → Manage Users
   - Create site-specific users
   - Assign appropriate roles

## 📋 Environment Variables

### Required:

| Variable | Value | Example |
|----------|-------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | Random 64-character hex string | `a1b2c3d4...` |
| `FLASK_ENV` | `production` | `production` |

### Optional:

| Variable | Value | Purpose |
|----------|-------|---------|
| `FLASK_DEBUG` | `0` | Disable debug mode |
| `MAX_CONTENT_LENGTH` | `16777216` | Max upload size (16MB) |

## 🔧 Configuration Details

### How PostgreSQL Detection Works:

```python
# config.py
database_url = os.environ.get("DATABASE_URL", 
                              'sqlite:///' + os.path.join(basedir, 'instance', 'app.db'))

# Fix Render's postgres:// to postgresql://
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

SQLALCHEMY_DATABASE_URI = database_url
```

**Result:**
- ✅ Local development: Uses SQLite (`instance/app.db`)
- ✅ Production: Uses PostgreSQL (from `DATABASE_URL`)
- ✅ Automatic URL format correction

### Connection Pool Settings:

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,      # Verify connection before use
    "pool_recycle": 300,         # Recycle after 5 minutes
}
```

**Benefits:**
- Prevents "connection already closed" errors
- Better performance under load
- Handles network issues gracefully

## 🗄️ Database Schema

### Tables Created:
1. `users` - User accounts
2. `roles` - User roles (Admin, Manager, etc.)
3. `permissions` - Granular permissions (43 total)
4. `user_roles` - Many-to-many relationship
5. `role_permissions` - Many-to-many relationship
6. `user_sites` - User site access
7. `sites` - Campus/location data
8. `students` - Student records
9. `groups` - Student groups
10. `machines` - Machine inventory
11. `modules` - Course modules
12. `lecturers` - Lecturer data
13. `schedule` - Scheduling data
14. `dynamic_fields` - Custom fields
15. `inventory` - Inventory items
16. And more...

### Initial Data:
- **1 Super Admin user**: admin/admin123
- **5 Roles**: Super Admin, Admin, Manager, Viewer, Lecturer
- **43 Permissions**: All assigned to all roles

## 🔍 Troubleshooting

### Issue: "relation does not exist"
**Cause**: Tables not created  
**Solution**: Run `python init_database.py`

### Issue: "could not connect to server"
**Cause**: Wrong DATABASE_URL  
**Solution**: Verify DATABASE_URL in environment variables

### Issue: "password authentication failed"
**Cause**: Incorrect database credentials  
**Solution**: Check DATABASE_URL format and credentials

### Issue: "SSL connection required"
**Cause**: Database requires SSL  
**Solution**: Add `?sslmode=require` to DATABASE_URL

### Issue: Build fails with "No module named 'psycopg2'"
**Cause**: Missing dependency  
**Solution**: Verify `psycopg2-binary==2.9.9` in requirements.txt

### Issue: "Application Error" after deployment
**Cause**: Check logs  
**Solution**: View logs in Render dashboard → Logs tab

## 📊 Monitoring

### Check Application Health:
```bash
curl https://your-app.onrender.com/
```

### View Logs:
- **Render**: Dashboard → Logs tab
- **Heroku**: `heroku logs --tail`
- **Railway**: Dashboard → Deployments → Logs

### Database Metrics:
```sql
-- Connection count
SELECT count(*) FROM pg_stat_activity;

-- Database size
SELECT pg_size_pretty(pg_database_size('lnsapp'));

-- Table sizes
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 💾 Backup & Recovery

### Automatic Backups:
- **Render**: Daily backups on paid plans
- **Heroku**: `heroku pg:backups:schedule --at '02:00 UTC'`
- **Railway**: Automatic backups included

### Manual Backup:
```bash
# Export database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore database
psql $DATABASE_URL < backup_20251103.sql
```

### Backup Your Data Before Migration:
```bash
# From SQLite
python export_sqlite_data.py

# Import to PostgreSQL
python import_to_postgres.py
```

## 🎯 Performance Tips

### For Production:

1. **Enable Query Caching** (if using Redis)
2. **Use CDN for Static Files**
3. **Enable Gzip Compression**
4. **Monitor Slow Queries**
5. **Set up Database Indexes** (already configured)

### Recommended Indexes:
```sql
CREATE INDEX IF NOT EXISTS idx_students_site ON students(site_id);
CREATE INDEX IF NOT EXISTS idx_groups_site ON groups(site_id);
CREATE INDEX IF NOT EXISTS idx_schedule_date ON schedule(date);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
```

## 💰 Cost Estimates

### Free Tier:
- **Render**: Free for 90 days, then $7/month for PostgreSQL
- **Railway**: $5/month credit (pay for usage)
- **Heroku**: No free tier (Mini $5/month)

### Recommended Production:
- **Render**: Standard ~$20/month (DB + Web)
- **Railway**: ~$10-15/month based on usage
- **Heroku**: Basic ~$12/month

## ✅ Final Checklist

Before going live:

- [ ] PostgreSQL database created
- [ ] Application deployed
- [ ] Environment variables set (DATABASE_URL, SECRET_KEY, FLASK_ENV)
- [ ] Database initialized (`python init_database.py`)
- [ ] Admin user created (`python setup_auth_original_db.py`)
- [ ] Permissions synced (`python sync_all_permissions.py`)
- [ ] Login tested (admin/admin123)
- [ ] Admin password changed
- [ ] Additional users created
- [ ] Test data added
- [ ] All features tested
- [ ] Backup strategy in place
- [ ] Monitoring set up

## 📚 Additional Resources

- **Render Docs**: https://render.com/docs/databases
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **Flask-SQLAlchemy**: https://flask-sqlalchemy.palletsprojects.com/
- **Deployment Guide**: See `DEPLOYMENT_GUIDE.md`

---

## 🎉 You're Ready to Deploy!

Your application is **100% configured** for PostgreSQL deployment.

**Next Steps:**
1. Choose your platform (Render recommended)
2. Create PostgreSQL database
3. Deploy application
4. Initialize database
5. Start using your app!

**Need help?** Check `DEPLOYMENT_GUIDE.md` for detailed platform-specific instructions.

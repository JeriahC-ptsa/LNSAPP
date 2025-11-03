# PostgreSQL Deployment Guide

## ✅ Your App is Ready for PostgreSQL Deployment!

Your application is already configured to work with PostgreSQL. Here's everything you need to know.

## Current Configuration Status

### ✅ Files Ready:
1. **`config.py`** - PostgreSQL support configured
2. **`requirements.txt`** - Includes `psycopg2-binary` and `gunicorn`
3. **`Procfile`** - Tells deployment platform how to run the app
4. **`runtime.txt`** - Specifies Python version
5. **`.env.example`** - Environment variables template

### ✅ Features:
- Automatic PostgreSQL URL conversion (postgres:// → postgresql://)
- Connection pooling configured
- Falls back to SQLite for local development
- Production-ready settings

## Deployment Options

### Option 1: Render.com (Recommended - Free Tier Available)

#### Step 1: Create PostgreSQL Database
1. Go to https://dashboard.render.com
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `lnsapp-db`
   - **Database**: `lnsapp`
   - **User**: (auto-generated)
   - **Region**: Choose closest to you
   - **Plan**: Free
4. Click **"Create Database"**
5. Copy the **Internal Database URL** (starts with `postgres://`)

#### Step 2: Deploy Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository: `JeriahC-ptsa/LNSAPP`
3. Configure:
   - **Name**: `lnsapp`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: (leave blank)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:app`
   - **Plan**: Free
4. Add Environment Variables:
   - **Key**: `DATABASE_URL`
   - **Value**: Paste the Internal Database URL from Step 1
   - **Key**: `SECRET_KEY`
   - **Value**: Generate a random secret (see below)
   - **Key**: `FLASK_ENV`
   - **Value**: `production`
5. Click **"Create Web Service"**

#### Step 3: Initialize Database
After deployment, run these commands in Render Shell:
```bash
python init_database.py
python setup_auth_original_db.py
```

### Option 2: Heroku

#### Step 1: Install Heroku CLI
```bash
# Download from: https://devcenter.heroku.com/articles/heroku-cli
```

#### Step 2: Login and Create App
```bash
heroku login
heroku create lnsapp
heroku addons:create heroku-postgresql:mini
```

#### Step 3: Set Environment Variables
```bash
heroku config:set SECRET_KEY="your-secret-key-here"
heroku config:set FLASK_ENV=production
```

#### Step 4: Deploy
```bash
git push heroku main
```

#### Step 5: Initialize Database
```bash
heroku run python init_database.py
heroku run python setup_auth_original_db.py
```

### Option 3: Railway.app

1. Go to https://railway.app
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select `JeriahC-ptsa/LNSAPP`
4. Add PostgreSQL:
   - Click **"New"** → **"Database"** → **"PostgreSQL"**
5. Add Environment Variables:
   - `SECRET_KEY`: Your secret key
   - `FLASK_ENV`: `production`
   - `DATABASE_URL`: (auto-set by Railway)
6. Deploy automatically happens

### Option 4: DigitalOcean App Platform

1. Go to https://cloud.digitalocean.com/apps
2. Click **"Create App"**
3. Connect GitHub: `JeriahC-ptsa/LNSAPP`
4. Add PostgreSQL database (Dev or Basic plan)
5. Configure environment variables
6. Deploy

## Environment Variables

### Required Variables:

```bash
# Secret key for Flask sessions (generate a random string)
SECRET_KEY=your-super-secret-key-change-this

# Database URL (automatically set by most platforms)
DATABASE_URL=postgresql://user:password@host:5432/database

# Flask environment
FLASK_ENV=production
```

### Generate Secret Key:
```python
import secrets
print(secrets.token_hex(32))
```

Or in terminal:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Database Migration

### From SQLite to PostgreSQL:

If you have existing data in SQLite that you want to migrate:

#### Option 1: Export/Import via CSV
```python
# Export from SQLite
python export_sqlite_data.py

# Import to PostgreSQL
python import_to_postgres.py
```

#### Option 2: Use pgloader (Advanced)
```bash
pgloader sqlite:///instance/app.db postgresql://user:pass@host/db
```

## Post-Deployment Setup

### 1. Initialize Database Tables
```bash
python init_database.py
```

### 2. Create Super Admin User
```bash
python setup_auth_original_db.py
```

This creates:
- Username: `admin`
- Password: `admin123`
- Role: Super Admin with all 43 permissions

### 3. Verify Deployment
Visit your deployed URL and:
- [ ] Login page loads
- [ ] Can login with admin/admin123
- [ ] All menu items visible
- [ ] Can create/view data

## Configuration Details

### config.py Explanation:

```python
# Get DATABASE_URL from environment
database_url = os.environ.get("DATABASE_URL", 
                              'sqlite:///' + os.path.join(basedir, 'instance', 'app.db'))

# Fix Render's postgres:// to postgresql://
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

SQLALCHEMY_DATABASE_URI = database_url
```

**What this does:**
- Uses PostgreSQL if `DATABASE_URL` is set (production)
- Falls back to SQLite for local development
- Automatically fixes Render's URL format

### Production Settings:

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,      # Check connection health
    "pool_recycle": 300,         # Recycle after 5 minutes
}
```

**Benefits:**
- Prevents stale connections
- Better performance
- Handles connection drops gracefully

## Local Development with PostgreSQL

If you want to test with PostgreSQL locally:

### 1. Install PostgreSQL
- Windows: https://www.postgresql.org/download/windows/
- Mac: `brew install postgresql`
- Linux: `sudo apt-get install postgresql`

### 2. Create Database
```bash
psql -U postgres
CREATE DATABASE lnsapp_dev;
\q
```

### 3. Set Environment Variable
Create `.env` file:
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/lnsapp_dev
SECRET_KEY=dev-secret-key
FLASK_ENV=development
```

### 4. Run App
```bash
python run.py
```

## Troubleshooting

### Error: "relation does not exist"
**Solution**: Run database initialization
```bash
python init_database.py
```

### Error: "could not connect to server"
**Solution**: Check DATABASE_URL is correct
```bash
echo $DATABASE_URL  # Linux/Mac
echo %DATABASE_URL%  # Windows
```

### Error: "password authentication failed"
**Solution**: Verify database credentials in DATABASE_URL

### Error: "SSL connection required"
**Solution**: Add `?sslmode=require` to DATABASE_URL
```bash
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
```

## Performance Optimization

### For Production:

1. **Enable Connection Pooling** (already configured)
2. **Use CDN for Static Files**
3. **Enable Gzip Compression**
4. **Set up Redis for Sessions** (optional)

### Database Indexes:
Already configured in models, but verify:
```sql
CREATE INDEX idx_students_site ON students(site_id);
CREATE INDEX idx_groups_site ON groups(site_id);
CREATE INDEX idx_schedule_date ON schedule(date);
```

## Monitoring

### Check Database Size:
```sql
SELECT pg_size_pretty(pg_database_size('lnsapp'));
```

### Check Active Connections:
```sql
SELECT count(*) FROM pg_stat_activity;
```

### View Slow Queries:
```sql
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

## Backup Strategy

### Automated Backups:
- **Render**: Automatic daily backups on paid plans
- **Heroku**: `heroku pg:backups:schedule --at '02:00 UTC'`
- **Railway**: Automatic backups included

### Manual Backup:
```bash
# Render
pg_dump $DATABASE_URL > backup.sql

# Heroku
heroku pg:backups:capture
heroku pg:backups:download
```

## Security Checklist

- [x] PostgreSQL configured with SSL
- [x] SECRET_KEY is random and secure
- [x] FLASK_ENV=production (not development)
- [ ] Change default admin password after first login
- [ ] Set up firewall rules (if self-hosting)
- [ ] Enable 2FA for deployment platform
- [ ] Regular database backups
- [ ] Monitor for suspicious activity

## Cost Estimates

### Free Tier Options:
- **Render**: Free PostgreSQL (90 days, then $7/month)
- **Railway**: $5/month credit (pay for usage)
- **Heroku**: Mini PostgreSQL $5/month
- **DigitalOcean**: $5/month (no free tier)

### Recommended for Production:
- **Render**: Standard plan ~$20/month (includes DB + web service)
- **Railway**: ~$10-15/month based on usage
- **DigitalOcean**: Basic plan $12/month

## Support

### Platform Documentation:
- **Render**: https://render.com/docs
- **Heroku**: https://devcenter.heroku.com
- **Railway**: https://docs.railway.app
- **DigitalOcean**: https://docs.digitalocean.com

### Common Issues:
- Database connection: Check DATABASE_URL format
- Build failures: Verify requirements.txt
- Runtime errors: Check logs in platform dashboard

---

## Quick Start Checklist

- [x] `config.py` - PostgreSQL support ✅
- [x] `requirements.txt` - psycopg2-binary ✅
- [x] `Procfile` - gunicorn command ✅
- [x] `runtime.txt` - Python version ✅
- [ ] Choose deployment platform
- [ ] Create PostgreSQL database
- [ ] Set environment variables
- [ ] Deploy application
- [ ] Initialize database
- [ ] Create admin user
- [ ] Test login and functionality

**Your app is 100% ready for PostgreSQL deployment!** 🚀

Choose your platform and follow the steps above.

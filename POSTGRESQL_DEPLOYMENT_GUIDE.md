# PostgreSQL Deployment Guide for LnSapp

## ✅ Changes Made

Your application has been updated to support PostgreSQL for production deployment:

1. ✅ **Added PostgreSQL support** - `psycopg2-binary` in requirements.txt
2. ✅ **Added production server** - `gunicorn` for WSGI serving
3. ✅ **Updated configuration** - Automatic PostgreSQL URL handling
4. ✅ **Added connection pooling** - Production-ready database settings
5. ✅ **Created deployment files** - `.env.example` and `render.yaml`

---

## 🔄 How It Works

Your app now automatically detects which database to use:

- **Local Development**: Uses SQLite (`instance/app.db`) - No setup needed
- **Production (Render)**: Uses PostgreSQL when `DATABASE_URL` is set

The config automatically handles the database URL format conversion that Render requires.

---

## 🚀 Deployment to Render

### Option 1: Using Render Dashboard (Recommended)

#### Step 1: Create PostgreSQL Database

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `lnsapp-postgres`
   - **Database**: `lnsapp`
   - **User**: `lnsapp_user`
   - **Region**: Choose closest to your users
   - **Instance Type**: 
     - **Free** (for testing only, expires in 30 days)
     - **Starter** ($7/month - Basic-256MB) - Recommended for launch
     - **Standard** ($25/month - Basic-1GB) - Recommended for production
4. Click **"Create Database"**
5. **Copy the Internal Database URL** (starts with `postgres://`)

#### Step 2: Create Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your Git repository (GitHub/GitLab/Bitbucket)
3. Configure:
   - **Name**: `lnsapp-web`
   - **Region**: Same as database
   - **Branch**: `main` (or your deployment branch)
   - **Root Directory**: Leave blank
   - **Runtime**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt && flask db upgrade
     ```
   - **Start Command**:
     ```bash
     gunicorn app:app
     ```
   - **Instance Type**:
     - **Starter** ($7/month) - Recommended for launch
     - **Standard** ($25/month) - Recommended for production

4. **Add Environment Variables**:
   - Click "Advanced" → "Add Environment Variable"
   
   | Key | Value |
   |-----|-------|
   | `SECRET_KEY` | Generate secure key: Use [random.org](https://www.random.org/strings/) or run `python -c "import secrets; print(secrets.token_hex(32))"` |
   | `DATABASE_URL` | Paste the Internal Database URL from Step 1 |
   | `FLASK_ENV` | `production` |

5. Click **"Create Web Service"**

#### Step 3: Initial Setup

After deployment completes:

1. Click on your service → **"Shell"**
2. Run initial setup commands:
   ```bash
   flask db upgrade
   python
   ```
   
3. In Python shell, create admin user:
   ```python
   from app import app, db
   from auth_models import User, Role
   from models import Site
   
   with app.app_context():
       # Create a site
       site = Site(name="Main Campus", code="MAIN", location="Primary Location")
       db.session.add(site)
       db.session.commit()
       
       # Create admin user
       admin = User(username="admin", email="admin@example.com")
       admin.set_password("ChangeThisPassword123!")
       db.session.add(admin)
       db.session.commit()
       
       print(f"Admin user created! ID: {admin.id}")
       print(f"Site created! ID: {site.id}")
   ```

4. Exit shell and visit your app URL

---

### Option 2: Using render.yaml (Infrastructure as Code)

1. Push your code with the `render.yaml` file to your repository
2. In Render Dashboard, click **"New +"** → **"Blueprint"**
3. Select your repository
4. Render will automatically create both database and web service
5. Follow Step 3 above for initial setup

---

## 🧪 Local Testing with PostgreSQL (Optional)

If you want to test PostgreSQL locally before deploying:

### Windows Setup

1. **Install PostgreSQL**:
   - Download from [postgresql.org](https://www.postgresql.org/download/windows/)
   - Install with default settings
   - Remember your password!

2. **Create Database**:
   ```powershell
   # Open PowerShell as Administrator
   psql -U postgres
   
   # In psql:
   CREATE DATABASE lnsapp;
   CREATE USER lnsapp_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE lnsapp TO lnsapp_user;
   \q
   ```

3. **Set Environment Variable**:
   ```powershell
   # Create .env file in project root
   echo "DATABASE_URL=postgresql://lnsapp_user:your_password@localhost:5432/lnsapp" > .env
   echo "SECRET_KEY=your-dev-secret-key" >> .env
   ```

4. **Run Migrations**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   flask db upgrade
   python app.py
   ```

---

## 🔍 Verify PostgreSQL Connection

To verify your app is using PostgreSQL:

```python
# Run in Flask shell or add to a route temporarily
from models import db
print(db.engine.url)
# Should show: postgresql://... (not sqlite:///)
```

---

## 📊 Database Migrations

When you make model changes:

```bash
# Local development
flask db migrate -m "Description of changes"
flask db upgrade

# Production (Render)
# Migrations run automatically on deploy via build command
# Or run manually in Render Shell:
flask db upgrade
```

---

## 💰 Recommended Configuration

### For Initial Launch (1 site, <50 students)
- **Workspace**: Individual (Free)
- **Web Service**: Starter ($7/month)
- **Database**: Basic-256MB + 5GB storage (~$8.50/month)
- **Total**: ~$15.50/month

### For Production (2-3 sites, 100-300 students)
- **Workspace**: Individual (Free)
- **Web Service**: Standard ($25/month)
- **Database**: Basic-1GB + 10GB storage (~$28/month)
- **Total**: ~$53/month

---

## 🔒 Security Checklist

- [ ] Change default `SECRET_KEY` to a secure random value
- [ ] Use strong database password (Render generates this automatically)
- [ ] Set `FLASK_ENV=production` in production
- [ ] Never commit `.env` file (it's in `.gitignore`)
- [ ] Use HTTPS (Render provides this automatically)
- [ ] Regularly backup your database (Render provides automatic backups on paid plans)

---

## 🐛 Troubleshooting

### Database Connection Errors

**Error**: `could not connect to server: Connection refused`
- **Solution**: Check DATABASE_URL is correctly set in environment variables
- **Solution**: Ensure database and web service are in the same region

**Error**: `password authentication failed`
- **Solution**: Verify DATABASE_URL includes correct password
- **Solution**: Copy fresh Internal Database URL from Render dashboard

### Migration Errors

**Error**: `Target database is not up to date`
- **Solution**: Run `flask db upgrade` in Render Shell
- **Solution**: Check build logs for migration errors

**Error**: `Can't locate revision identified by 'xxxxx'`
- **Solution**: Your migrations folder might not be in Git. Add it:
  ```bash
  git add migrations/
  git commit -m "Add migrations"
  git push
  ```

### Performance Issues

**Slow queries**: Upgrade database instance
**Out of memory**: Upgrade web service instance
**Connection timeouts**: Check `SQLALCHEMY_ENGINE_OPTIONS` in config.py

---

## 📈 Monitoring

1. **Render Dashboard**: View logs, metrics, deployment history
2. **Database Metrics**: Monitor connection count, query performance
3. **Set up Alerts**: Configure email alerts for errors/downtime

---

## 🔄 Rollback

If deployment fails:

1. Go to Render Dashboard → Your Service
2. Click **"Deploys"** tab
3. Find previous successful deploy
4. Click **"Rollback to this deploy"**

---

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [Flask-SQLAlchemy Docs](https://flask-sqlalchemy.palletsprojects.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Flask-Migrate Docs](https://flask-migrate.readthedocs.io/)

---

## ✅ Next Steps

1. **Test Locally**: Ensure app runs without errors
2. **Commit Changes**: 
   ```bash
   git add .
   git commit -m "Add PostgreSQL support for deployment"
   git push
   ```
3. **Deploy to Render**: Follow deployment steps above
4. **Create Initial Data**: Run setup commands to create admin user
5. **Test Production**: Verify all features work correctly
6. **Monitor**: Watch logs and metrics for first few days

---

**Your app is now ready for production deployment with PostgreSQL!** 🎉

For questions or issues, refer to:
- This guide
- `RENDER_DEPLOYMENT_REPORT.md` for pricing details
- Render community forum

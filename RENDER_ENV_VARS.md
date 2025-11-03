# Render Environment Variables

## Add these to your Render Web Service

Go to your Web Service → Environment → Add Environment Variable

### 1. DATABASE_URL
```
postgresql://lnsapp_user:xtOZmNow4nehkMEP6DKtHpSjUiXOIQza@dpg-d445idje5dus73aka2eg-a:5432/lnsapp
```

### 2. SECRET_KEY
```
b3149fac6ed16bdbf81d3943282ab3d5a3d39afccb7950ce04a882de2fe53a44
```

### 3. FLASK_ENV
```
production
```

### 4. FLASK_DEBUG
```
0
```

---

## After Adding Environment Variables

1. **Save** the environment variables
2. **Deploy** (or Render will auto-deploy)
3. Wait for deployment to complete
4. Open **Shell** in your Web Service
5. Run these commands:

```bash
# Initialize database tables
python init_database.py

# Create admin user and permissions
python setup_auth_original_db.py

# Sync all permissions to all roles
python sync_all_permissions.py
```

6. Visit your app URL
7. Login with:
   - Username: `admin`
   - Password: `admin123`

---

## Important Notes

⚠️ **DO NOT commit `.env.production` to Git!**
- It's already in `.gitignore`
- Contains sensitive credentials

✅ **These values are already configured in `.env.production`**
- Use that file as reference
- Copy values to Render dashboard

🔒 **Security**
- Change admin password after first login
- Keep SECRET_KEY secret
- Never share database credentials

---

## Troubleshooting

### If deployment fails:
1. Check logs in Render dashboard
2. Verify all 4 environment variables are set
3. Ensure DATABASE_URL is the Internal URL (not External)

### If database connection fails:
1. Verify DATABASE_URL is correct
2. Check that Web Service and Database are in same region
3. Our config automatically handles postgres:// vs postgresql://

### If tables don't exist:
1. Run `python init_database.py` in Render Shell
2. Check logs for any errors

---

## Quick Copy-Paste for Render

**Key**: `DATABASE_URL`  
**Value**: `postgresql://lnsapp_user:xtOZmNow4nehkMEP6DKtHpSjUiXOIQza@dpg-d445idje5dus73aka2eg-a:5432/lnsapp`

**Key**: `SECRET_KEY`  
**Value**: `b3149fac6ed16bdbf81d3943282ab3d5a3d39afccb7950ce04a882de2fe53a44`

**Key**: `FLASK_ENV`  
**Value**: `production`

**Key**: `FLASK_DEBUG`  
**Value**: `0`

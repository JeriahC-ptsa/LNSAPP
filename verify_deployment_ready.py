"""
Verify that the application is ready for PostgreSQL deployment
"""
import os
import sys

def check_file_exists(filepath, description):
    """Check if a file exists"""
    exists = os.path.exists(filepath)
    status = "OK" if exists else "MISSING"
    print(f"  [{status}] {description}: {filepath}")
    return exists

def check_file_content(filepath, search_text, description):
    """Check if file contains specific text"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            found = search_text in content
            status = "OK" if found else "MISSING"
            print(f"  [{status}] {description}")
            return found
    except:
        print(f"  [ERROR] Could not read {filepath}")
        return False

print("="*70)
print("PostgreSQL Deployment Readiness Check")
print("="*70)

all_checks = []

print("\n1. Required Files:")
all_checks.append(check_file_exists("config.py", "Configuration file"))
all_checks.append(check_file_exists("requirements.txt", "Dependencies file"))
all_checks.append(check_file_exists("Procfile", "Deployment command file"))
all_checks.append(check_file_exists("runtime.txt", "Python version file"))
all_checks.append(check_file_exists(".gitignore", "Git ignore file"))
all_checks.append(check_file_exists("run.py", "Application entry point"))

print("\n2. Database Configuration:")
all_checks.append(check_file_content("config.py", "DATABASE_URL", "DATABASE_URL environment variable"))
all_checks.append(check_file_content("config.py", "postgresql://", "PostgreSQL URL conversion"))
all_checks.append(check_file_content("config.py", "pool_pre_ping", "Connection pooling"))

print("\n3. Dependencies:")
all_checks.append(check_file_content("requirements.txt", "psycopg2-binary", "PostgreSQL adapter"))
all_checks.append(check_file_content("requirements.txt", "gunicorn", "Production server"))
all_checks.append(check_file_content("requirements.txt", "Flask-SQLAlchemy", "SQLAlchemy ORM"))

print("\n4. Deployment Files:")
all_checks.append(check_file_content("Procfile", "gunicorn", "Gunicorn command"))
all_checks.append(check_file_content("runtime.txt", "python-3", "Python version specified"))

print("\n5. Security:")
all_checks.append(check_file_content(".gitignore", ".env", ".env file ignored"))
all_checks.append(check_file_content(".gitignore", "*.db", "Database files ignored"))
all_checks.append(check_file_content("config.py", "SECRET_KEY", "Secret key configuration"))

print("\n6. Initialization Scripts:")
all_checks.append(check_file_exists("init_database.py", "Database initialization"))
all_checks.append(check_file_exists("setup_auth_original_db.py", "Admin user creation"))

print("\n7. Documentation:")
all_checks.append(check_file_exists("DEPLOYMENT_GUIDE.md", "Deployment guide"))
all_checks.append(check_file_exists("POSTGRES_DEPLOYMENT_CHECKLIST.md", "Deployment checklist"))

print("\n" + "="*70)
print("Summary:")
print("="*70)

passed = sum(all_checks)
total = len(all_checks)
percentage = (passed / total) * 100

print(f"Checks Passed: {passed}/{total} ({percentage:.1f}%)")

if passed == total:
    print("\nOK Your application is 100% ready for PostgreSQL deployment!")
    print("\nNext steps:")
    print("1. Read DEPLOYMENT_GUIDE.md for platform-specific instructions")
    print("2. Choose your deployment platform (Render, Heroku, Railway)")
    print("3. Create PostgreSQL database")
    print("4. Deploy your application")
    print("5. Run: python init_database.py")
    print("6. Run: python setup_auth_original_db.py")
    print("7. Login with admin/admin123")
    sys.exit(0)
else:
    print("\nWARNING: Some checks failed. Review the items marked [MISSING] above.")
    print("Your application may not deploy correctly until these are fixed.")
    sys.exit(1)

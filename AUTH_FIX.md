# Authentication Fix - AnonymousUserMixin Error

## Issue
After fixing the database schema, a new error appeared:
```
AttributeError: 'AnonymousUserMixin' object has no attribute 'is_super_admin'
```

## Root Cause
The `require_site_access` decorator was checking `current_user.is_super_admin()` without first verifying if the user was authenticated. When an unauthenticated user tried to access the home page, Flask-Login provided an `AnonymousUserMixin` object which doesn't have custom methods like `is_super_admin()`.

## Fix Applied

### Modified `app.py` line 89-117
Added `@login_required` decorator to `require_site_access`:

```python
def require_site_access(f):
    """Decorator to ensure user has access to active site"""
    @wraps(f)
    @login_required  # ← Added this line
    def decorated_function(*args, **kwargs):
        # Now current_user is guaranteed to be authenticated
        # Safe to call is_super_admin() and has_site_access()
        ...
```

## Behavior After Fix

### Before:
- Unauthenticated user visits `/` → **500 Error** (AttributeError)

### After:
- Unauthenticated user visits `/` → **Redirected to login page** ✅
- After login → Home page loads normally ✅

## Impact

All routes decorated with `@require_site_access` now:
1. Require authentication (redirect to login if not logged in)
2. Require site access (verify user has permission for the active site)
3. No longer crash when accessed by anonymous users

## Routes Affected

Any route with `@require_site_access` decorator:
- `/` (index/home page)
- `/students/*`
- `/machines/*`
- `/groups/*`
- `/modules/*`
- `/inventory/*`
- `/schedules/*`
- `/reports/*`
- And many more...

## Testing

1. ✅ Access home page without logging in → Redirects to `/auth/login`
2. ✅ Login with valid credentials → Can access home page
3. ✅ Navigate to any protected route → Works correctly
4. ✅ No more AttributeError crashes

---
**Fix Applied**: October 24, 2025  
**Status**: ✅ RESOLVED

# Profile Picture Not Persisting After Refresh - Troubleshooting

## The Problem
Profile picture uploads successfully but disappears after page refresh on deployed site.

## Most Likely Causes

### 1. Database Migrations Not Run on Production
**Check if migrations are applied:**
```bash
# SSH into your deployment or run via deployment console
python manage.py showmigrations users

# If not all applied, run:
python manage.py migrate
```

### 2. Using Wrong Database in Production
Check your production `settings.py` or environment variables:
```python
# Should be using Supabase PostgreSQL, not SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': '...',
        'HOST': 'db.gxwvncpgdkmcvmangljn.supabase.co',
        'PORT': '5432',
    }
}
```

### 3. Session/Cache Issue
The user object might be cached. Try:
```python
# In views.py, after saving
from django.contrib.auth import update_session_auth_hash
request.user.refresh_from_db()
```

### 4. Field Length Issue
If the Supabase URL is very long, check if the URLField can store it:
```python
# In models.py - should be at least 500 characters
profile_picture = models.URLField(max_length=500, blank=True, null=True)
```

## Quick Fixes to Try

### Fix 1: Force Database Refresh
Add this to your view after saving:
```python
# After request.user.save()
request.user.refresh_from_db()
print(f"Saved profile picture: {request.user.profile_picture}")
```

### Fix 2: Check Production Logs
Look for these debug messages after upload:
- `✅ Supabase URL: ...`
- `🔍 Verified saved URL: ...`

If you don't see these, the save isn't working.

### Fix 3: Verify Database Directly
Connect to your production database and check:
```sql
SELECT id, username, profile_picture FROM users_customuser WHERE id = YOUR_USER_ID;
```

### Fix 4: Clear Browser Cache
Sometimes it's just browser caching:
- Hard refresh: `Ctrl + Shift + R` (Windows/Linux) or `Cmd + Shift + R` (Mac)
- Clear site data in DevTools

## Run Migrations on Production

**If using Render/Railway/Heroku:**
```bash
# Add to your build command or run manually
python manage.py migrate
```

**If using Vercel/similar:**
Make sure your deployment runs migrations automatically or add a post-deploy script.

## Verify the Fix

1. Upload a profile picture
2. Check browser console for logs
3. Check server logs for the verified URL message
4. Refresh the page
5. If it's gone, check the database directly to see if it's actually saved

## Most Common Solution

Run this on your production server:
```bash
python manage.py migrate users
python manage.py migrate
```

Then try uploading again!

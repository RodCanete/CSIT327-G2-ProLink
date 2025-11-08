# Profile Picture Upload - Troubleshooting Plan

## Problem
Profile picture uploads successfully but disappears on refresh. Image is being saved locally instead of to Supabase cloud storage.

## Root Cause Analysis

### Confirmed Issues:
1. ✅ **Multiple conflicting profile_picture fields:**
   - `CustomUser.profile_picture` (URLField) - What we want to use
   - `Profile.profile_picture` (ImageField) - Old model interfering
   
2. ✅ **Context processor using old Profile model:**
   - File: `users/context_processors.py`
   - Using `Profile.objects.get()` instead of `user.profile_picture`

3. ✅ **Django caching old code:**
   - Server not reloading new view code
   - Bytecode cache not clearing

## Step-by-Step Fix Plan

### Step 1: Verify Which View is Running
```powershell
cd prolink
python manage.py shell
```

Then run:
```python
from users.views import edit_profile_picture
import inspect
print("=" * 60)
print("CHECKING WHICH VIEW DJANGO IS USING")
print("=" * 60)
print(f"\nFile: {inspect.getsourcefile(edit_profile_picture)}")
print(f"\nFirst 300 chars of code:")
print(inspect.getsource(edit_profile_picture)[:300])
print("\n" + "=" * 60)
# Look for: "NEW SUPABASE VERSION" or "supabase.storage"
```

**Expected Output:** Should show Supabase upload code
**If Not:** Old code is cached or wrong file

---

### Step 2: Delete Old Profile Model (Nuclear Option)
The `Profile` model is causing conflicts. Let's remove it:

**A. Comment out Profile model in models.py:**
```python
# COMMENT OUT OR DELETE THIS:
# class Profile(models.Model):
#     user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
#     profile_picture = models.ImageField(upload_to='profile_pictures/', default='profile_pictures/default_profile.png')
#
#     def __str__(self):
#         return self.user.username
```

**B. Update context_processors.py:**
```python
# Change FROM:
def profile_picture(request):
    if request.user.is_authenticated:
        try:
            profile = Profile.objects.get(user=request.user)
            return {'profile_picture_url': profile.profile_picture.url}
        except Profile.DoesNotExist:
            return {'profile_picture_url': None}
    return {'profile_picture_url': None}

# Change TO:
def profile_picture(request):
    if request.user.is_authenticated:
        return {'profile_picture_url': request.user.profile_picture}
    return {'profile_picture_url': None}
```

**C. Create migration:**
```powershell
python manage.py makemigrations
python manage.py migrate
```

---

### Step 3: Clear ALL Caches
```powershell
# Stop server first (Ctrl+C)

# Delete all __pycache__ folders
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# Delete .pyc files
Get-ChildItem -Path . -Recurse -Filter "*.pyc" | Remove-Item -Force

# Restart server
python manage.py runserver
```

---

### Step 4: Create Supabase Storage Bucket

**Manual Method (Recommended):**
1. Go to https://supabase.com/dashboard
2. Select your project: `gxwvncpgdkmcvmangljn`
3. Click **Storage** in sidebar
4. Click **New bucket**
5. Name: `avatars`
6. ✅ Check **"Public bucket"**
7. Click **Create bucket**

**OR use SQL in Supabase SQL Editor:**
```sql
-- Create public bucket
INSERT INTO storage.buckets (id, name, public)
VALUES ('avatars', 'avatars', true)
ON CONFLICT (id) DO NOTHING;

-- Allow authenticated uploads
CREATE POLICY IF NOT EXISTS "Allow authenticated uploads"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'avatars');

-- Allow public reads
CREATE POLICY IF NOT EXISTS "Allow public reads"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'avatars');
```

---

### Step 5: Test Supabase Connection
```powershell
python test_supabase_connection.py
```

**Expected Output:**
```
✓ Connected to Supabase
✓ Found X bucket(s):
   - avatars (PUBLIC ✓)
✅ SUCCESS! 'avatars' bucket exists!
```

---

### Step 6: Test Upload with Debug Output
```powershell
# Start server
python manage.py runserver

# Watch console output
# When you upload, you should see:
# 🔵 NEW SUPABASE VERSION RUNNING!
# 📁 File received: filename.png
# ☁️ Attempting Supabase upload...
# 📤 Uploading to Supabase: profile_pictures/xxx.png
# ✅ Supabase URL: https://...supabase.co/...
```

---

### Step 7: Check Database After Upload
```powershell
python manage.py shell
```

```python
from users.models import CustomUser
user = CustomUser.objects.get(email='your_email@example.com')
print(f"Profile picture URL: {user.profile_picture}")
# Should show Supabase URL like:
# https://gxwvncpgdkmcvmangljn.supabase.co/storage/v1/object/public/avatars/profile_pictures/xxx.png
```

---

## Quick Diagnostic Commands

### Check if view has Supabase code:
```powershell
Select-String -Path "prolink\users\views.py" -Pattern "supabase.storage" -Context 2,2
```

### Check for old Profile imports:
```powershell
Select-String -Path "prolink\users\*.py" -Pattern "from.*Profile|import.*Profile" | Where-Object { $_ -notmatch "Professional" }
```

### Find all profile_picture references:
```powershell
Select-String -Path "prolink\users\*.py" -Pattern "profile_picture" -CaseSensitive
```

---

## Alternative: Use FormData Debugging

Add this to the JavaScript in `client_profile.html`:

```javascript
profilePictureInput.addEventListener('change', function() {
    if (!this.files || !this.files[0]) return;
    
    const formData = new FormData(profilePictureForm);
    
    // DEBUG: Log what we're sending
    console.log('=== UPLOAD DEBUG ===');
    console.log('URL:', profilePictureForm.action);
    console.log('Method:', profilePictureForm.method);
    for (let pair of formData.entries()) {
        console.log(pair[0] + ':', pair[1]);
    }
    console.log('===================');
    
    fetch(profilePictureForm.action, {
        // ... rest of code
    })
    .then(response => {
        console.log('Response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        // Check if data.image_url contains 'supabase'
        if (data.image_url && data.image_url.includes('supabase')) {
            console.log('✅ Supabase URL received!');
        } else {
            console.log('❌ Not a Supabase URL:', data.image_url);
        }
        // ... rest of code
    });
});
```

---

## Expected vs Actual

### ❌ Current (Local Storage):
```
Upload → Saved to: /media/profile_pictures/pic.png (local disk)
Database stores: /media/profile_pictures/pic.png
Refresh → ❌ File not found on server
```

### ✅ Goal (Supabase Storage):
```
Upload → Saved to: https://supabase.co/storage/.../pic.png (cloud)
Database stores: https://supabase.co/storage/.../pic.png
Refresh → ✅ Works everywhere!
```

---

## If Still Not Working

Run this comprehensive check:
```powershell
cd prolink
python -c "
import sys
sys.path.insert(0, 'prolink')
import django
django.setup()

print('=== COMPREHENSIVE CHECK ===')

# Check 1: Which view is loaded?
from users import views
import inspect
print(f'\n1. View file: {inspect.getfile(views.edit_profile_picture)}')
print(f'   Has supabase import: {\"supabase\" in inspect.getsource(views.edit_profile_picture)}')

# Check 2: Check models
from users.models import CustomUser
print(f'\n2. CustomUser has profile_picture: {hasattr(CustomUser, \"profile_picture\")}')
field = CustomUser._meta.get_field('profile_picture')
print(f'   Field type: {type(field).__name__}')

# Check 3: Check settings
from django.conf import settings
print(f'\n3. SUPABASE_URL: {settings.SUPABASE_URL[:30]}...')
print(f'   MEDIA_URL: {settings.MEDIA_URL}')

print('\n' + '='*40)
"
```

---

## Next Steps

1. **Start with Step 1** - Find out which view Django is actually using
2. **Then Step 2** - Remove conflicting Profile model
3. **Then Steps 3-6** - Clean, setup, test

Let me know which step fails and I'll provide specific fixes!

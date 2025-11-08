# Profile Picture Issue - Local vs Remote

## Problem
Profile pictures upload locally but don't appear on remote because:
1. **Media files are stored on local filesystem** (not in database)
2. **Git doesn't push media files** (they're in .gitignore)
3. **You have 3 conflicting profile_picture fields** in your models

## Current Setup

### Three Profile Picture Fields:
```python
# 1. CustomUser model (line 21)
profile_picture = models.URLField()  # Stores URL string

# 2. Profile model (line 151)  
profile_picture = models.ImageField(upload_to='profile_pictures/')  # Stores file

# 3. ProfessionalProfile might have one too
```

## Quick Fix Solutions

### Option A: Use Cloud Storage (Recommended)
Upload images to cloud service like:
- Cloudinary (Free tier: 25GB)
- AWS S3
- Azure Blob Storage
- Supabase Storage (you're already using Supabase!)

**Benefits:**
- ✅ Works on both local and remote
- ✅ Images persist across deployments
- ✅ Fast CDN delivery
- ✅ No Git storage bloat

### Option B: Use Supabase Storage (Since you already have it!)

1. **Install Supabase Storage Python SDK:**
```powershell
pip install supabase-storage-py
```

2. **Update your view to upload to Supabase:**
```python
# In users/views.py
from supabase import create_client
from django.conf import settings

def edit_profile_picture(request):
    if request.method == 'POST' and request.FILES.get('profile_picture'):
        file = request.FILES['profile_picture']
        
        # Upload to Supabase Storage
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        
        file_path = f"profile_pictures/{request.user.id}/{file.name}"
        supabase.storage.from_('avatars').upload(file_path, file.read())
        
        # Get public URL
        public_url = supabase.storage.from_('avatars').get_public_url(file_path)
        
        # Save URL to user model (using URLField)
        request.user.profile_picture = public_url
        request.user.save()
        
        return JsonResponse({'success': True, 'image_url': public_url})
```

### Option C: Clean Up Your Models First

**Remove duplicate fields:**

```python
# users/models.py

class CustomUser(AbstractUser):
    # Keep ONLY the URLField (works for both local files and cloud URLs)
    profile_picture = models.URLField(max_length=500, blank=True, null=True)
    # ... rest of fields

# REMOVE the separate Profile model (it's redundant)
# Delete this entire class:
class Profile(models.Model):  # <-- DELETE THIS
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    profile_picture = models.ImageField(...)  # <-- DELETE THIS
```

Then update your template:
```django
<!-- Change from: -->
{% if user.profile.profile_picture %}
    <img src="{{ user.profile.profile_picture.url }}">
{% endif %}

<!-- To: -->
{% if user.profile_picture %}
    <img src="{{ user.profile_picture }}">
{% endif %}
```

## Step-by-Step: Quick Supabase Fix

### 1. Create a Supabase Storage Bucket
```sql
-- In Supabase Dashboard > Storage
CREATE BUCKET avatars PUBLIC;
```

### 2. Update Your View
See Option B above for the code.

### 3. Update Template
```django
{% if user.profile_picture %}
    <img src="{{ user.profile_picture }}" alt="Profile">
{% else %}
    <img src="{% static 'images/default_profile.png' %}" alt="Profile">
{% endif %}
```

### 4. Test
- Upload on local → saved to Supabase
- Deploy to remote → same Supabase URL works!

## Why This Happens

**Local (Your PC):**
```
Upload → Saved to: C:\Users\Rod\prolink\media\profile_pictures\pic.jpg
Database stores: "profile_pictures/pic.jpg"
```

**Remote (Deployed):**
```
Database has: "profile_pictures/pic.jpg"
But file doesn't exist on remote server!
Result: Broken image ❌
```

**With Cloud Storage:**
```
Upload → Saved to: https://supabase.co/storage/avatars/pic.jpg
Database stores: "https://supabase.co/storage/avatars/pic.jpg"
Works everywhere! ✅
```

## Recommended Action

1. **Use Supabase Storage** (you're already using Supabase for auth)
2. **Clean up duplicate profile_picture fields**
3. **Keep only CustomUser.profile_picture as URLField**

Want me to implement this for you? Let me know!

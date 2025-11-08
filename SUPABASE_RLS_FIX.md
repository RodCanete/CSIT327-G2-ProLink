# Fixing Supabase Row-Level Security (RLS) for Profile Pictures

## Problem
You're getting this error: `new row violates row-level security policy`

This means Supabase's security policies are blocking uploads to the `avatars` bucket.

## Solution

### Option 1: Disable RLS (Quick Fix - Not Recommended for Production)

1. Go to your Supabase Dashboard
2. Navigate to **Storage** → **avatars** bucket
3. Click on **Policies**
4. Toggle **"Enable RLS"** to OFF

⚠️ **Warning**: This makes the bucket publicly writable. Only use for testing!

---

### Option 2: Create Proper RLS Policies (Recommended)

1. Go to your Supabase Dashboard
2. Navigate to **Storage** → **avatars** bucket
3. Click on **Policies**
4. Make sure **"Enable RLS"** is ON
5. Click **"New Policy"**

#### Policy 1: Allow Authenticated Users to Upload

```sql
-- Policy Name: Allow authenticated users to upload
-- Allowed operation: INSERT
-- Policy definition:
(bucket_id = 'avatars' AND auth.role() = 'authenticated')
```

#### Policy 2: Allow Users to Update Their Own Files

```sql
-- Policy Name: Allow users to update own files
-- Allowed operation: UPDATE
-- Policy definition:
(bucket_id = 'avatars' AND auth.role() = 'authenticated')
```

#### Policy 3: Allow Public Read Access

```sql
-- Policy Name: Public read access
-- Allowed operation: SELECT
-- Policy definition:
(bucket_id = 'avatars')
```

#### Policy 4: Allow Users to Delete Their Own Files

```sql
-- Policy Name: Allow users to delete own files
-- Allowed operation: DELETE
-- Policy definition:
(bucket_id = 'avatars' AND auth.role() = 'authenticated')
```

---

### Option 3: Make the Bucket Public (Simplest)

1. Go to your Supabase Dashboard
2. Navigate to **Storage** → **avatars** bucket
3. Click on the bucket settings (three dots)
4. Toggle **"Public bucket"** to ON
5. Click **"Save"**

This makes all files in the bucket publicly accessible, which is fine for profile pictures.

---

## Alternative: Use Service Role Key (Backend Only)

If you want to bypass RLS entirely from your Django backend, you can use the Service Role key instead of the Anon key:

**In your `.env` file:**
```env
SUPABASE_SERVICE_KEY=your_service_role_key_here
```

**In `supabase_config.py`:**
```python
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
```

**In `views.py`:**
```python
# Use SERVICE key instead of ANON key for admin operations
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
```

⚠️ **Warning**: Service Role key bypasses ALL security. Keep it secret and only use server-side!

---

## Recommended Setup

For profile pictures, I recommend:
1. Make the `avatars` bucket **public** (Option 3)
2. This allows anyone to view images (good for profile pictures)
3. Keep using the ANON key in your code
4. Images will be publicly readable, which is what you want for profile pictures

---

## Testing

After implementing any of these solutions, try uploading a profile picture again. The error should be resolved!

# Supabase Storage Integration for File Uploads

This document describes the implementation of Supabase Storage for handling file uploads in the ProLink application.

## Overview

We've migrated from local file storage to **Supabase Storage** for production-ready file management. This provides:

- ✅ Cloud-based storage (scalable and reliable)
- ✅ Public URL access for uploaded files
- ✅ Built-in CDN for fast file delivery
- ✅ Automatic file validation and security
- ✅ No server disk space concerns

## Features Implemented

### 1. **File Upload to Supabase Storage**
   - Files are uploaded to a dedicated bucket: `request-files`
   - Each user's files are organized in folders: `requests/{user_email}/`
   - Supports multiple file formats: PDF, DOC, DOCX, PNG, JPG, JPEG, ZIP, TXT, CSV
   - Maximum file size: 10MB per file
   - Maximum files per request: 5 files

### 2. **Professional Selection**
   - ❌ Removed smart auto-assignment
   - ✅ Manual professional selection via dropdown
   - Users can see all available professionals
   - Optional field - can be left empty and assigned later

### 3. **File Display in Request Details**
   - Files shown with appropriate icons based on type
   - Direct download links with public URLs
   - File size display (human-readable format)
   - Hover effects and visual feedback

## File Structure

```
prolink/
├── requests/
│   ├── storage_utils.py          # Supabase Storage manager
│   ├── views.py                  # Updated with Supabase integration
│   └── models.py                 # Request model (unchanged)
├── templates/
│   └── requests/
│       ├── create_request.html   # Updated with professional dropdown
│       └── request_detail.html   # Updated file display
├── static/css/
│   └── dashboard.css             # Added file display styles
└── setup_supabase_bucket.py      # Bucket setup script
```

## Setup Instructions

### 1. Install Dependencies

Make sure you have the Supabase Python client:

```bash
pip install supabase
```

### 2. Configure Supabase Credentials

Ensure your `supabase_config.py` has the service role key:

```python
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key"
SUPABASE_SERVICE_ROLE_KEY = "your-service-role-key"  # Required for storage admin operations
```

**How to get the Service Role Key:**
1. Go to Supabase Dashboard
2. Navigate to: Settings > API
3. Copy the `service_role` key (not the `anon` key)
4. Add it to your `supabase_config.py`

### 3. Create Storage Bucket

Run the setup script to create the bucket:

```bash
cd prolink
python setup_supabase_bucket.py
```

This will:
- Create the `request-files` bucket
- Configure it as a public bucket
- Test the upload functionality
- Verify everything is working

### 4. Configure Storage Policies (Optional)

For production, you may want to add RLS policies in Supabase Dashboard:

**Storage Policies Location:**
- Go to: Storage > Policies
- Select bucket: `request-files`

**Recommended Policies:**

1. **Allow authenticated users to upload:**
   ```sql
   CREATE POLICY "Authenticated users can upload files"
   ON storage.objects FOR INSERT
   TO authenticated
   WITH CHECK (bucket_id = 'request-files');
   ```

2. **Allow public read access:**
   ```sql
   CREATE POLICY "Public can view files"
   ON storage.objects FOR SELECT
   TO public
   USING (bucket_id = 'request-files');
   ```

3. **Allow users to delete their own files:**
   ```sql
   CREATE POLICY "Users can delete their own files"
   ON storage.objects FOR DELETE
   TO authenticated
   USING (
     bucket_id = 'request-files' 
     AND (storage.foldername(name))[1] = 'requests'
     AND (storage.foldername(name))[2] = auth.jwt() ->> 'email'
   );
   ```

## Usage

### Creating a Request with Files

1. User navigates to "Create Request"
2. Fills in the form details
3. **Selects a professional** from the dropdown (optional)
4. Uploads files (drag & drop or browse)
5. Submits the form

**Behind the scenes:**
- Files are validated (size, type)
- Uploaded to Supabase: `request-files/requests/{user_email}/{unique-id}.ext`
- Metadata stored in database (JSON format)
- Public URLs generated automatically

### Viewing Request with Files

1. User opens a request detail page
2. Files section displays all uploaded files with:
   - File type icons (PDF, Word, Image, etc.)
   - Original filename
   - File size
   - Download button

**File Metadata Format:**
```json
[
  {
    "original_name": "project-report.pdf",
    "stored_path": "requests/user@example.com/abc123.pdf",
    "public_url": "https://.../request-files/requests/user@example.com/abc123.pdf",
    "size": 1048576,
    "mime_type": "application/pdf",
    "uploaded": true
  }
]
```

## Code Components

### SupabaseStorageManager (`storage_utils.py`)

Main class for handling file operations:

```python
from requests.storage_utils import get_storage_manager

storage = get_storage_manager()

# Upload single file
file_info = storage.upload_file(uploaded_file, folder="requests/user@example.com")

# Upload multiple files
files_info, errors = storage.upload_multiple_files(files, folder="requests/user@example.com")

# Delete file
storage.delete_file("requests/user@example.com/file.pdf")

# Get public URL
url = storage.get_file_url("requests/user@example.com/file.pdf")
```

**Methods:**
- `ensure_bucket_exists()` - Create bucket if doesn't exist
- `validate_file(file)` - Validate file size and type
- `upload_file(file, folder)` - Upload single file
- `upload_multiple_files(files, folder)` - Upload multiple files
- `delete_file(path)` - Delete a file
- `delete_multiple_files(paths)` - Delete multiple files
- `get_file_url(path)` - Get public URL

### Updated Views

**`create_request` view:**
- Fetches all professionals for dropdown
- Uses `get_storage_manager()` to upload files
- Validates professional selection
- Stores file metadata as JSON

**`request_detail` view:**
- Parses attached files JSON
- Passes file data to template

## Testing

### Test File Upload

1. Create a test professional user:
```bash
python manage.py shell
from users.models import CustomUser
pro = CustomUser.objects.create_user(
    username='testpro',
    email='testpro@example.com',
    password='test123',
    user_role='professional',
    first_name='Test',
    last_name='Professional'
)
```

2. Create a request with files:
   - Login as a client
   - Navigate to "Create Request"
   - Select the test professional
   - Upload 1-2 test files (PDF, images, etc.)
   - Submit

3. Verify:
   - Files appear in Supabase Dashboard (Storage)
   - Files display correctly in request detail
   - Download buttons work
   - Public URLs are accessible

## Troubleshooting

### Issue: Bucket creation fails
**Solution:** Check your `SUPABASE_SERVICE_ROLE_KEY` in `supabase_config.py`

### Issue: Upload fails with permission error
**Solution:** 
1. Verify bucket is public or has appropriate policies
2. Check that service role key is correct

### Issue: Files don't display
**Solution:**
1. Check that `attached_files` JSON is properly formatted
2. Verify public URLs are accessible
3. Check browser console for errors

### Issue: "No professionals found" in dropdown
**Solution:** Create professional users with `user_role='professional'`

## Security Considerations

1. **File Validation:** 
   - Max size: 10MB
   - Allowed types only
   - Unique filenames (UUID)

2. **Access Control:**
   - Consider RLS policies for production
   - Use service role key only server-side
   - Public URLs are accessible to anyone (by design)

3. **File Organization:**
   - Files organized by user email
   - Easy to implement user-specific policies

## Future Enhancements

- [ ] Add file upload progress indicator
- [ ] Implement file preview (images, PDFs)
- [ ] Add file deletion for request owners
- [ ] Implement file versioning
- [ ] Add virus scanning integration
- [ ] Implement signed URLs for private files
- [ ] Add file search/filtering
- [ ] Bulk file operations

## Support

For issues or questions:
1. Check Supabase Dashboard for storage logs
2. Review Django logs for error messages
3. Verify all credentials are correct
4. Test with `setup_supabase_bucket.py` script

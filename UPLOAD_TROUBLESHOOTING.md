# File Upload Troubleshooting Guide

## 🐛 Issue: Files not uploading or not showing in create_request.html

### ✅ Testing Steps:

#### 1. **Test the Upload System**
Visit: http://127.0.0.1:8000/requests/test-upload/

This diagnostic page will:
- Show if files are being received by Django
- Display any upload errors
- Show successfully uploaded files with URLs
- Help identify where the problem is

#### 2. **Check Server Console**
The server now prints debug information when uploading:
```
📁 Uploading 2 files for user@example.com
✅ Uploaded 2 files
❌ Errors: 0
  - document.pdf: https://...
  - image.png: https://...
```

Watch the terminal where `python manage.py runserver` is running.

---

## 🔍 Common Issues & Solutions:

### Issue 1: "Bucket not found"
**Solution:**
1. Go to Supabase Dashboard → Storage
2. Verify `request-files` bucket exists
3. If not, create it manually (Public bucket)

### Issue 2: "Permission denied" or "RLS policy"
**Solution:**
1. Go to Storage → request-files → Policies
2. Add this policy:
   - Name: "Allow authenticated uploads"
   - Operation: INSERT
   - Target: authenticated
   - USING: `bucket_id = 'request-files'`

### Issue 3: Files upload but don't show in form
**Check:**
1. Look at server console for upload confirmations
2. Visit `/requests/test-upload/` to see if files appear there
3. Check browser console (F12) for JavaScript errors
4. Verify the success message appears after form submission

### Issue 4: Form submits but no success message
**Solution:**
The form might be redirecting too fast. Look for:
- Success message on the requests list page
- Check if request was created in database
- Look at server console for upload logs

---

## 📊 Diagnostic Checklist:

Run through these in order:

- [ ] **Bucket exists in Supabase**
  - Dashboard → Storage → see `request-files`

- [ ] **Test upload works**
  - Visit `/requests/test-upload/`
  - Upload a file
  - See success message with URL

- [ ] **Server logs show uploads**
  - Watch terminal during form submission
  - Look for "📁 Uploading X files..."
  - Look for "✅ Uploaded X files"

- [ ] **Form has correct enctype**
  - Already set: `enctype="multipart/form-data"` ✅

- [ ] **Input name matches backend**
  - Frontend: `name="attached_files"` ✅
  - Backend: `request.FILES.getlist('attached_files')` ✅

- [ ] **File validation passes**
  - Max 5 files
  - Max 10MB each
  - Allowed types: PDF, DOC, DOCX, PNG, JPG, ZIP

---

## 🧪 Quick Test Commands:

### Test 1: Check if bucket is accessible
```bash
cd prolink
.\env\Scripts\Activate.ps1
python test_upload.py
```
Should show: ✅ All tests passed!

### Test 2: Try diagnostic page
1. Start server: `python manage.py runserver`
2. Visit: http://127.0.0.1:8000/requests/test-upload/
3. Upload a file
4. Check results

### Test 3: Create actual request
1. Visit: http://127.0.0.1:8000/requests/create/
2. Fill form with valid data
3. Select files
4. Watch terminal for debug logs
5. Submit
6. Check success message

---

## 🎯 Expected Behavior:

### When uploading files:
1. User selects files → File list appears below upload area ✅
2. User clicks "Submit Request" → Form submits ✅
3. Server receives files → Console logs "📁 Uploading..." ✅
4. Files upload to Supabase → Console logs "✅ Uploaded..." ✅
5. Request created → Database entry made ✅
6. Redirect → User sees success message ✅
7. View request → Files appear in detail page ✅

### Server Console Output (Expected):
```
📁 Uploading 2 files for student@example.com
✅ Uploaded 2 files
❌ Errors: 0
  - project-report.pdf: https://gxwvncpgdkmcvmangljn.supabase.co/storage/v1/object/public/request-files/requests/student@example.com/abc123.pdf
  - screenshot.png: https://gxwvncpgdkmcvmangljn.supabase.co/storage/v1/object/public/request-files/requests/student@example.com/def456.png
[08/Nov/2025 10:30:15] "POST /requests/create/ HTTP/1.1" 302 0
```

---

## 🚨 If Still Not Working:

1. **Stop the server** (Ctrl+C)
2. **Restart the server:**
   ```bash
   cd prolink
   .\env\Scripts\Activate.ps1
   python manage.py runserver
   ```
3. **Clear browser cache** (Ctrl+Shift+Delete)
4. **Try in incognito/private window**
5. **Check browser console** (F12 → Console tab)

---

## 📝 What to Check in Browser (F12):

### Console Tab:
- Look for JavaScript errors
- Should see file list update when selecting files

### Network Tab:
1. Submit form
2. Look for POST to `/requests/create/`
3. Check if files are in the request payload
4. Status should be 302 (redirect) on success

---

## ✅ Success Indicators:

You'll know it's working when you see:
1. ✅ Files appear in list after selection
2. ✅ Console logs show "📁 Uploading..."
3. ✅ Console logs show "✅ Uploaded X files"
4. ✅ Success message appears: "Request 'Title' created successfully! (2 file(s) uploaded)"
5. ✅ Files appear in request detail page
6. ✅ Download buttons work

---

## 🆘 Need More Help?

Share this information:
1. What you see in browser (screenshots)
2. Server console output (copy/paste)
3. Browser console errors (F12)
4. Result from `/requests/test-upload/` page

This will help pinpoint exactly where the issue is!

"""
Quick test script to check file upload functionality
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'prolink'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prolink.settings')
django.setup()

from requests.storage_utils import get_storage_manager
from django.core.files.uploadedfile import SimpleUploadedFile

print("=" * 60)
print("🧪 Testing File Upload to Supabase")
print("=" * 60)

# Test 1: Check if storage manager can be initialized
print("\n1. Initializing storage manager...")
try:
    storage = get_storage_manager()
    print("   ✅ Storage manager initialized")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 2: Check if bucket exists
print("\n2. Checking bucket...")
try:
    bucket_ok = storage.ensure_bucket_exists()
    if bucket_ok:
        print("   ✅ Bucket 'request-files' is accessible")
    else:
        print("   ❌ Bucket check failed")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 3: Try uploading a test file
print("\n3. Testing file upload...")
try:
    # Create a test file
    test_content = b"This is a test file for ProLink upload system"
    test_file = SimpleUploadedFile(
        "test-upload.txt",
        test_content,
        content_type="text/plain"
    )
    
    # Upload it
    file_info = storage.upload_file(test_file, folder="test-uploads")
    
    print("   ✅ File uploaded successfully!")
    print(f"   📁 Original name: {file_info['original_name']}")
    print(f"   📍 Stored path: {file_info['stored_path']}")
    print(f"   🔗 Public URL: {file_info['public_url']}")
    print(f"   📦 Size: {file_info['size']} bytes")
    
    # Clean up test file
    print("\n4. Cleaning up test file...")
    storage.delete_file(file_info['stored_path'])
    print("   ✅ Test file deleted")
    
except Exception as e:
    print(f"   ❌ Upload failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ All tests passed! File upload is working correctly.")
print("=" * 60)

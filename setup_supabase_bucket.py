"""
Setup script for Supabase Storage bucket
Run this once to create the bucket for file uploads

Usage:
    cd prolink  (the inner prolink directory with manage.py)
    python ../setup_supabase_bucket.py
"""
import os
import sys
import django

# Setup Django environment
# Add the prolink directory (where manage.py is) to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
prolink_dir = os.path.join(current_dir, 'prolink')
sys.path.insert(0, prolink_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prolink.settings')
django.setup()

from django.conf import settings
from supabase import create_client


def setup_storage_bucket():
    """
    Create and configure the Supabase storage bucket
    """
    print("🚀 Setting up Supabase Storage...")
    
    try:
        # Create Supabase client with service role key for admin operations
        client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
        
        bucket_name = "request-files"
        
        # Check if bucket exists by trying to list files
        print(f"📦 Checking if bucket '{bucket_name}' exists...")
        bucket_exists = False
        try:
            client.storage.from_(bucket_name).list()
            bucket_exists = True
        except Exception:
            bucket_exists = False
        
        if bucket_exists:
            print(f"✅ Bucket '{bucket_name}' already exists!")
        else:
            # Create the bucket
            print(f"📦 Creating bucket '{bucket_name}'...")
            client.storage.create_bucket(
                bucket_name,
                options={"public": True}  # Make it public for easy access
            )
            print(f"✅ Bucket '{bucket_name}' created successfully!")
        
        # Test upload
        print("\n🧪 Testing file upload...")
        test_content = b"This is a test file for Supabase Storage"
        test_path = "test/test-file.txt"
        
        try:
            client.storage.from_(bucket_name).upload(
                test_path,
                test_content,
                file_options={
                    "content-type": "text/plain",
                    "upsert": "true"
                }
            )
            print("✅ Test upload successful!")
            
            # Get public URL
            public_url = client.storage.from_(bucket_name).get_public_url(test_path)
            print(f"📎 Test file URL: {public_url}")
            
            # Clean up test file
            client.storage.from_(bucket_name).remove([test_path])
            print("🧹 Test file cleaned up!")
            
        except Exception as e:
            print(f"⚠️  Test upload failed: {str(e)}")
            print("Bucket was created but test upload failed. You may need to check permissions.")
        
        print("\n✅ Setup complete!")
        print("\n📝 Next steps:")
        print("1. Make sure SUPABASE_SERVICE_ROLE_KEY is set in your supabase_config.py")
        print("2. Verify bucket policies in Supabase dashboard if needed")
        print("3. Try creating a request with file attachments")
        
    except Exception as e:
        print(f"\n❌ Error setting up storage: {str(e)}")
        print("\n💡 Troubleshooting:")
        print("1. Check that SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are correct in supabase_config.py")
        print("2. Make sure you have the supabase-py package installed: pip install supabase")
        print("3. Verify your Supabase project is active")
        return False
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("🌟 ProLink - Supabase Storage Setup")
    print("=" * 60)
    print()
    
    setup_storage_bucket()
    
    print()
    print("=" * 60)

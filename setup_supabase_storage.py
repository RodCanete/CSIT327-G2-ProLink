"""
Script to create the 'avatars' storage bucket in Supabase
Run this once from the outer prolink directory: python setup_supabase_storage.py
"""
import os
import sys

# Add the inner prolink directory to path
current_dir = os.path.dirname(os.path.abspath(__filey__))
prolink_dir = os.path.join(current_dir, 'prolink')
sys.path.insert(0, prolink_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prolink.settings')

import django
django.setup()

from django.conf import settings
from supabase import create_client

def setup_storage():
    print("="*60)
    print("Setting up Supabase Storage for Profile Pictures")
    print("="*60)
    
    try:
        # Initialize Supabase client
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        
        # Check if 'avatars' bucket exists
        buckets = supabase.storage.list_buckets()
        
        avatar_bucket_exists = any(bucket['name'] == 'avatars' for bucket in buckets)
        
        if avatar_bucket_exists:
            print("✓ 'avatars' bucket already exists!")
        else:
            print("Creating 'avatars' bucket...")
            
            # Create public bucket for avatars
            supabase.storage.create_bucket(
                'avatars',
                options={'public': True}
            )
            
            print("✓ 'avatars' bucket created successfully!")
        
        print("\n" + "="*60)
        print("Setup Complete!")
        print("="*60)
        print("\nYou can now upload profile pictures:")
        print("1. Go to your profile page")
        print("2. Click 'Edit Profile Picture'")
        print("3. Select an image")
        print("4. It will be uploaded to Supabase Storage")
        print("\n✓ Profile pictures will work on both local and remote!")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("\nTo create the bucket manually:")
        print("1. Go to https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Go to Storage in the sidebar")
        print("4. Click 'New bucket'")
        print("5. Name it 'avatars'")
        print("6. Make it PUBLIC")
        print("7. Click Create")

if __name__ == "__main__":
    setup_storage()

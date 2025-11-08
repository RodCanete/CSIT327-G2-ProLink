"""
Supabase Storage utilities for file uploads
"""
import os
import uuid
import mimetypes
from django.conf import settings
from supabase import create_client, Client
from typing import List, Dict, Optional


class SupabaseStorageManager:
    """
    Manager class for handling file uploads to Supabase Storage
    """
    
    BUCKET_NAME = "request-files"
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {
        '.pdf', '.doc', '.docx', 
        '.png', '.jpg', '.jpeg', 
        '.zip', '.txt', '.csv'
    }
    
    def __init__(self):
        self.client: Client = create_client(
            settings.SUPABASE_URL, 
            settings.SUPABASE_SERVICE_ROLE_KEY  # Use service role for admin operations
        )
        self.storage = self.client.storage
    
    def ensure_bucket_exists(self) -> bool:
        """
        Ensure the bucket exists, create if it doesn't
        """
        try:
            # Try to get bucket - list_buckets returns a list directly in newer versions
            try:
                buckets_response = self.storage.list_buckets()
                # Handle different response types
                if hasattr(buckets_response, 'data'):
                    buckets = buckets_response.data if buckets_response.data else []
                elif isinstance(buckets_response, list):
                    buckets = buckets_response
                else:
                    buckets = []
                
                bucket_exists = any(
                    (bucket.get('name') if isinstance(bucket, dict) else getattr(bucket, 'name', None)) == self.BUCKET_NAME 
                    for bucket in buckets
                )
            except Exception:
                # If list fails, assume bucket doesn't exist
                bucket_exists = False
            
            if not bucket_exists:
                # Create public bucket
                self.storage.create_bucket(
                    self.BUCKET_NAME,
                    options={"public": True}
                )
                print(f"Created bucket: {self.BUCKET_NAME}")
            return True
        except Exception as e:
            print(f"Error ensuring bucket exists: {str(e)}")
            return False
    
    def validate_file(self, file) -> tuple[bool, Optional[str]]:
        """
        Validate file size and type
        Returns: (is_valid, error_message)
        """
        # Check file size
        if file.size > self.MAX_FILE_SIZE:
            return False, f"File {file.name} is too large. Maximum size is 10MB."
        
        # Check file extension
        file_ext = os.path.splitext(file.name)[1].lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            allowed = ', '.join(self.ALLOWED_EXTENSIONS)
            return False, f"File {file.name} has unsupported format. Allowed: {allowed}"
        
        return True, None
    
    def upload_file(self, file, folder: str = "uploads") -> Dict:
        """
        Upload a single file to Supabase Storage
        
        Args:
            file: Django uploaded file object
            folder: Folder path within the bucket
            
        Returns:
            Dictionary with file information
        """
        # Ensure bucket exists
        self.ensure_bucket_exists()
        
        # Validate file
        is_valid, error = self.validate_file(file)
        if not is_valid:
            raise ValueError(error)
        
        # Generate unique filename
        file_extension = os.path.splitext(file.name)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = f"{folder}/{unique_filename}"
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(file.name)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        # Read file content
        file_content = file.read()
        
        # Upload to Supabase
        try:
            response = self.storage.from_(self.BUCKET_NAME).upload(
                file_path,
                file_content,
                file_options={
                    "content-type": mime_type,
                    "cache-control": "3600",
                    "upsert": "false"
                }
            )
            
            # Get public URL
            public_url = self.storage.from_(self.BUCKET_NAME).get_public_url(file_path)
            
            return {
                'original_name': file.name,
                'stored_path': file_path,
                'public_url': public_url,
                'size': file.size,
                'mime_type': mime_type,
                'uploaded': True
            }
            
        except Exception as e:
            raise Exception(f"Error uploading file {file.name}: {str(e)}")
    
    def upload_multiple_files(self, files, folder: str = "uploads") -> tuple[List[Dict], List[str]]:
        """
        Upload multiple files to Supabase Storage
        
        Args:
            files: List of Django uploaded file objects
            folder: Folder path within the bucket
            
        Returns:
            Tuple of (uploaded_files_list, errors_list)
        """
        uploaded_files = []
        errors = []
        
        # Validate file count
        if len(files) > 5:
            errors.append("Maximum 5 files allowed.")
            return uploaded_files, errors
        
        # Upload each file
        for file in files:
            try:
                file_info = self.upload_file(file, folder)
                uploaded_files.append(file_info)
            except Exception as e:
                errors.append(str(e))
        
        return uploaded_files, errors
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from Supabase Storage
        
        Args:
            file_path: Path to the file in the bucket
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.storage.from_(self.BUCKET_NAME).remove([file_path])
            return True
        except Exception as e:
            print(f"Error deleting file {file_path}: {str(e)}")
            return False
    
    def delete_multiple_files(self, file_paths: List[str]) -> int:
        """
        Delete multiple files from Supabase Storage
        
        Args:
            file_paths: List of file paths in the bucket
            
        Returns:
            Number of successfully deleted files
        """
        try:
            self.storage.from_(self.BUCKET_NAME).remove(file_paths)
            return len(file_paths)
        except Exception as e:
            print(f"Error deleting files: {str(e)}")
            return 0
    
    def get_file_url(self, file_path: str) -> Optional[str]:
        """
        Get public URL for a file
        
        Args:
            file_path: Path to the file in the bucket
            
        Returns:
            Public URL or None if error
        """
        try:
            return self.storage.from_(self.BUCKET_NAME).get_public_url(file_path)
        except Exception as e:
            print(f"Error getting file URL: {str(e)}")
            return None


# Singleton instance
_storage_manager = None

def get_storage_manager() -> SupabaseStorageManager:
    """
    Get singleton instance of SupabaseStorageManager
    """
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = SupabaseStorageManager()
    return _storage_manager

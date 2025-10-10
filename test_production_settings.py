#!/usr/bin/env python
"""
Test script to verify production settings work correctly
Run this with: python test_production_settings.py
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir / 'prolink'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prolink.settings')
os.environ.setdefault('DEBUG', 'False')  # Test production mode
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-production-testing')

django.setup()

from django.conf import settings
from django.core.management import execute_from_command_line

def test_production_settings():
    print("Testing production settings...")
    
    # Test basic settings
    assert not settings.DEBUG, "DEBUG should be False in production"
    assert settings.SECRET_KEY != 'django-insecure-@k!$%3pzfv5kyj(#gbqct1f+^%a$m7@4!+6$mvq%ja3cqp-0%r', "Should use environment SECRET_KEY"
    assert 'whitenoise.middleware.WhiteNoiseMiddleware' in settings.MIDDLEWARE, "WhiteNoise should be in middleware"
    assert settings.STATIC_ROOT, "STATIC_ROOT should be configured"
    
    print("✓ All production settings tests passed!")
    
    # Test collectstatic command
    print("Testing collectstatic...")
    try:
        execute_from_command_line(['manage.py', 'collectstatic', '--no-input', '--dry-run'])
        print("✓ collectstatic command works")
    except Exception as e:
        print(f"✗ collectstatic failed: {e}")
    
    print("Production settings test completed successfully!")

if __name__ == '__main__':
    test_production_settings()


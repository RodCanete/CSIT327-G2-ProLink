import sys
import os

# Add the inner prolink directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
prolink_dir = os.path.join(current_dir, 'prolink')
sys.path.insert(0, prolink_dir)

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prolink.settings')

import django
django.setup()

from users.views import edit_profile_picture
import inspect

print('='*60)
print('CHECKING WHICH VIEW DJANGO IS USING')
print('='*60)

file_path = inspect.getsourcefile(edit_profile_picture)
print(f'\n📁 File: {file_path}')

code = inspect.getsource(edit_profile_picture)

print(f'\n✓ Has SUPABASE code: {"supabase" in code}')
print(f'✓ Has NEW VERSION marker: {"NEW SUPABASE VERSION" in code}')
print(f'✓ Has debug prints: {"🔵" in code or "Debug line" in code}')

print(f'\n📝 First 500 characters of function:')
print('-'*60)
print(code[:500])
print('-'*60)

if "supabase" in code:
    print('\n✅ Supabase view is loaded!')
else:
    print('\n❌ OLD view is still being used!')
    print('   Solutions:')
    print('   1. Restart Django server')
    print('   2. Delete __pycache__ folders')
    print('   3. Check for multiple views.py files')

print('='*60)

from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Check if a user exists and show their details'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address to check')

    def handle(self, *args, **options):
        email = options['email']
        
        # Use raw SQL to avoid ORM model field issues
        with connection.cursor() as cursor:
            # Check if user exists
            cursor.execute("""
                SELECT id, username, email, user_role, is_active, is_staff, created_at
                FROM users_customuser
                WHERE email = %s
            """, [email])
            
            user = cursor.fetchone()
            
            if user:
                user_id, username, user_email, user_role, is_active, is_staff, created_at = user
                self.stdout.write(self.style.SUCCESS(f'✓ User found: {user_email}'))
                self.stdout.write(f'  - ID: {user_id}')
                self.stdout.write(f'  - Username: {username}')
                self.stdout.write(f'  - Role: {user_role}')
                self.stdout.write(f'  - Active: {is_active}')
                self.stdout.write(f'  - Staff: {is_staff}')
                self.stdout.write(f'  - Created: {created_at}')
            else:
                self.stdout.write(self.style.ERROR(f'❌ No user found with email: {email}'))
                self.stdout.write('\nTrying to find similar emails...')
                
                cursor.execute("""
                    SELECT email FROM users_customuser
                    WHERE email ILIKE %s
                    LIMIT 5
                """, [f'%{email.split("@")[0]}%'])
                
                similar = cursor.fetchall()
                if similar:
                    for (similar_email,) in similar:
                        self.stdout.write(f'  - {similar_email}')
                else:
                    self.stdout.write('  No similar emails found')
                    
                # Show total user count
                cursor.execute("SELECT COUNT(*) FROM users_customuser")
                total = cursor.fetchone()[0]
                self.stdout.write(f'\nTotal users in database: {total}')

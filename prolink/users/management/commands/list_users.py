from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'List all users in the database with their details'

    def handle(self, *args, **kwargs):
        self.stdout.write('=== All Users in Database ===\n')
        
        with connection.cursor() as cursor:
            # Get all users with their details
            cursor.execute("""
                SELECT 
                    id, 
                    username, 
                    email, 
                    first_name, 
                    last_name, 
                    user_role,
                    school_name,
                    major,
                    year_level,
                    graduation_year,
                    company_name,
                    job_title,
                    bio,
                    created_at
                FROM users_customuser
                ORDER BY created_at DESC
            """)
            
            users = cursor.fetchall()
            
            if not users:
                self.stdout.write(self.style.WARNING('No users found in database.'))
                return
            
            self.stdout.write(f'Found {len(users)} user(s):\n')
            
            for user in users:
                (user_id, username, email, first_name, last_name, user_role, 
                 school_name, major, year_level, graduation_year, 
                 company_name, job_title, bio, created_at) = user
                
                self.stdout.write(self.style.SUCCESS(f'\n━━━ User #{user_id} ━━━'))
                self.stdout.write(f'Name: {first_name} {last_name}')
                self.stdout.write(f'Email: {email}')
                self.stdout.write(f'Username: {username}')
                self.stdout.write(f'Role: {user_role}')
                
                if user_role == 'student':
                    self.stdout.write(self.style.WARNING('\n📚 Student Info:'))
                    if school_name:
                        self.stdout.write(f'  School: {school_name}')
                    if major:
                        self.stdout.write(f'  Major: {major}')
                    if year_level:
                        self.stdout.write(f'  Year Level: {year_level}')
                    if graduation_year:
                        self.stdout.write(f'  Graduation Year: {graduation_year}')
                
                elif user_role == 'worker':
                    self.stdout.write(self.style.WARNING('\n💼 Worker Info:'))
                    if company_name:
                        self.stdout.write(f'  Company: {company_name}')
                    if job_title:
                        self.stdout.write(f'  Job Title: {job_title}')
                
                elif user_role == 'professional':
                    self.stdout.write(self.style.WARNING('\n👔 Professional Info:'))
                    # Check if they have a professional profile
                    cursor.execute("""
                        SELECT experience_level, hourly_rate, is_available
                        FROM users_professionalprofile
                        WHERE user_id = %s
                    """, [user_id])
                    prof_profile = cursor.fetchone()
                    if prof_profile:
                        exp_level, hourly_rate, is_available = prof_profile
                        self.stdout.write(f'  Experience: {exp_level}')
                        self.stdout.write(f'  Hourly Rate: ${hourly_rate}')
                        self.stdout.write(f'  Available: {"Yes" if is_available else "No"}')
                
                if bio:
                    self.stdout.write(f'\nBio: {bio}')
                
                self.stdout.write(f'Created: {created_at}')
            
            self.stdout.write(self.style.SUCCESS(f'\n\n✓ Total users: {len(users)}'))

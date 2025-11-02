from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Verify and fix database table structure'

    def handle(self, *args, **kwargs):
        self.stdout.write('=== Checking database structure ===')
        
        with connection.cursor() as cursor:
            # Check if all required tables exist
            required_tables = [
                'users_customuser',
                'users_specialization',
                'users_professionalprofile',
                'users_professionalprofile_specializations',
                'users_savedprofessional'
            ]
            
            missing_tables = []
            for table_name in required_tables:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s
                    );
                """, [table_name])
                
                exists = cursor.fetchone()[0]
                if not exists:
                    missing_tables.append(table_name)
                else:
                    self.stdout.write(self.style.SUCCESS(f'✓ Table {table_name} exists'))
            
            if missing_tables:
                self.stdout.write(self.style.ERROR(f'\n❌ Missing tables: {", ".join(missing_tables)}'))
                self.stdout.write(self.style.WARNING('\nThese tables should be created by migrations.'))
                self.stdout.write(self.style.WARNING('Run: python manage.py migrate --run-syncdb'))
                return
            
            # Check if users_customuser table exists
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users_customuser'
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            
            if not columns:
                self.stdout.write(self.style.ERROR('❌ Table users_customuser does not exist!'))
                return
            
            self.stdout.write(self.style.SUCCESS('✓ Table users_customuser exists'))
            self.stdout.write('\nCurrent columns:')
            
            column_names = []
            for col_name, col_type in columns:
                self.stdout.write(f'  - {col_name} ({col_type})')
                column_names.append(col_name)
            
            # Check for required columns
            required_columns = [
                'id', 'password', 'last_login', 'is_superuser', 'username',
                'first_name', 'last_name', 'email', 'is_staff', 'is_active',
                'date_joined', 'user_role', 'phone_number', 'profile_picture',
                'bio', 'date_of_birth', 'school_name', 'major', 'year_level',
                'graduation_year', 'company_name', 'job_title', 'created_at',
                'updated_at'
            ]
            
            missing_columns = [col for col in required_columns if col not in column_names]
            
            if missing_columns:
                self.stdout.write(self.style.ERROR(f'\n❌ Missing columns: {", ".join(missing_columns)}'))
                self.stdout.write(self.style.WARNING('\nAttempting to add missing columns...'))
                
                # Add missing columns with proper data types
                column_definitions = {
                    'date_of_birth': 'DATE NULL',
                    'school_name': 'VARCHAR(255) NULL',
                    'major': 'VARCHAR(255) NULL',
                    'year_level': 'VARCHAR(50) NULL',
                    'graduation_year': 'INTEGER NULL',
                    'company_name': 'VARCHAR(255) NULL',
                    'job_title': 'VARCHAR(255) NULL',
                }
                
                for col in missing_columns:
                    if col in column_definitions:
                        cursor.execute(f'ALTER TABLE users_customuser ADD COLUMN {col} {column_definitions[col]};')
                        self.stdout.write(self.style.SUCCESS(f'✓ Added {col} column'))
                
                # Fix profile_picture if needed
                if 'profile_picture' in column_names:
                    cursor.execute("""
                        SELECT data_type, character_maximum_length
                        FROM information_schema.columns 
                        WHERE table_name = 'users_customuser' AND column_name = 'profile_picture';
                    """)
                    result = cursor.fetchone()
                    if result and result[0] == 'character varying' and (result[1] or 0) < 500:
                        cursor.execute('ALTER TABLE users_customuser ALTER COLUMN profile_picture TYPE VARCHAR(500);')
                        self.stdout.write(self.style.SUCCESS('✓ Updated profile_picture column to VARCHAR(500)'))
                
                # IMPORTANT: Close and reopen connection to clear Django's cached table structure
                connection.close()
                
                self.stdout.write(self.style.SUCCESS('\n✓ Database structure fixed!'))
            else:
                self.stdout.write(self.style.SUCCESS('\n✓ All required columns exist!'))

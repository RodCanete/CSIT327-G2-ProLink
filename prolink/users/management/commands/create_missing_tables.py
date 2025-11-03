from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps

class Command(BaseCommand):
    help = 'Automatically detect and create any missing database tables from Django models'

    def handle(self, *args, **kwargs):
        self.stdout.write('=== Checking for missing tables ===')
        
        with connection.cursor() as cursor:
            # Get all existing tables in the database (works for both SQLite and PostgreSQL)
            if connection.vendor == 'postgresql':
                cursor.execute("""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                """)
                existing_tables = {row[0] for row in cursor.fetchall()}
            else:
                # SQLite
                cursor.execute("""
                    SELECT name 
                    FROM sqlite_master 
                    WHERE type='table'
                """)
                existing_tables = {row[0] for row in cursor.fetchall()}
            
            self.stdout.write(f'Found {len(existing_tables)} existing tables in database ({connection.vendor})')
            
            # Get all models and their expected table names
            required_tables = {}
            for model in apps.get_models():
                table_name = model._meta.db_table
                required_tables[table_name] = model
            
            self.stdout.write(f'Found {len(required_tables)} models in Django')
            
            # Find missing tables
            missing_tables = [
                table for table in required_tables.keys() 
                if table not in existing_tables
            ]
            
            if not missing_tables:
                self.stdout.write(self.style.SUCCESS('✓ All tables exist! No action needed.'))
                return
            
            self.stdout.write(self.style.WARNING(f'\n❌ Missing {len(missing_tables)} table(s):'))
            for table in missing_tables:
                self.stdout.write(f'   - {table}')
            
            # Create missing tables using Django's schema editor
            self.stdout.write(self.style.WARNING('\n🔧 Creating missing tables...'))
            
            from django.db import connection as db_connection
            from django.db.backends.base.schema import BaseDatabaseSchemaEditor
            
            with db_connection.schema_editor() as schema_editor:
                for table_name in missing_tables:
                    model = required_tables[table_name]
                    try:
                        self.stdout.write(f'Creating table: {table_name}')
                        schema_editor.create_model(model)
                        self.stdout.write(self.style.SUCCESS(f'✓ Created {table_name}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'✗ Failed to create {table_name}: {str(e)}'))
            
            # Verify tables were created
            if connection.vendor == 'postgresql':
                cursor.execute("""
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                """)
                new_existing_tables = {row[0] for row in cursor.fetchall()}
            else:
                # SQLite
                cursor.execute("""
                    SELECT name 
                    FROM sqlite_master 
                    WHERE type='table'
                """)
                new_existing_tables = {row[0] for row in cursor.fetchall()}
            
            still_missing = [
                table for table in missing_tables 
                if table not in new_existing_tables
            ]
            
            if still_missing:
                self.stdout.write(self.style.ERROR(f'\n⚠️  Still missing {len(still_missing)} table(s):'))
                for table in still_missing:
                    self.stdout.write(f'   - {table}')
            else:
                self.stdout.write(self.style.SUCCESS('\n✅ All missing tables created successfully!'))
                self.stdout.write(f'Total tables in database: {len(new_existing_tables)}')
